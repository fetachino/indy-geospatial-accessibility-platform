"""Deterministic tests for download caching and source-schema validation."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request

import pytest
from openpyxl import Workbook

from indy_accessibility_data.acquisition import (
    AcquisitionError,
    SourceValidationError,
    acquire_dataset,
    validate_source,
)
from indy_accessibility_data.catalog import Dataset, load_catalog

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse(io.BytesIO):
    """Minimal context-managed HTTP response used without a network."""

    def __init__(
        self,
        content: bytes,
        *,
        content_type: str = "application/json",
        status: int = 200,
    ) -> None:
        super().__init__(content)
        self.status = status
        self.headers = {
            "Content-Type": content_type,
            "ETag": '"synthetic"',
            "Last-Modified": "Tue, 18 Aug 2026 12:00:00 GMT",
        }

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def dataset(dataset_id: str) -> Dataset:
    """Return one validated production rule set for a synthetic fixture."""
    return load_catalog().dataset(dataset_id)


@pytest.mark.parametrize(
    ("dataset_id", "fixture_name"),
    [
        ("marion_county_boundary", "marion_county_boundary.geojson"),
        ("hospital_locations_2023", "hospital_locations.geojson"),
        ("ifd_fire_stations", "fire_stations.geojson"),
        ("indiana_library_locations_2025", "library_locations.geojson"),
    ],
)
def test_geojson_fixtures_pass_source_specific_quality_rules(
    dataset_id: str, fixture_name: str
) -> None:
    validate_source(FIXTURES / fixture_name, dataset(dataset_id))


def test_census_fixture_validates_required_geography_and_fields() -> None:
    validate_source(
        FIXTURES / "acs_block_groups.json",
        dataset("acs_2024_block_group_demographics"),
    )


def test_gtfs_fixture_validates_files_fields_and_stop_coordinates(
    tmp_path: Path,
) -> None:
    archive = tmp_path / "gtfs.zip"
    with zipfile.ZipFile(archive, "w") as output:
        for source in (FIXTURES / "gtfs").iterdir():
            output.write(source, source.name)

    validate_source(archive, dataset("indygo_gtfs"))


def test_snap_csv_fixture_validates_inside_zip(tmp_path: Path) -> None:
    archive = tmp_path / "snap.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.write(FIXTURES / "snap_retailers.csv", "retailers.csv")

    rules = dataset("snap_grocery_retailers_2005_2025")
    rules = rules.model_copy(
        update={
            "validation": rules.validation.model_copy(
                update={"minimum_bytes": archive.stat().st_size}
            )
        }
    )
    validate_source(archive, rules)


def test_tiger_fixture_validates_required_shapefile_members(tmp_path: Path) -> None:
    archive = tmp_path / "tiger.zip"
    with zipfile.ZipFile(archive, "w") as output:
        for suffix in ("shp", "shx", "dbf", "prj"):
            output.writestr(f"tl_2024_18_bg.{suffix}", "synthetic")

    rules = dataset("census_block_groups_2024")
    rules = rules.model_copy(
        update={
            "validation": rules.validation.model_copy(
                update={"minimum_bytes": archive.stat().st_size}
            )
        }
    )
    validate_source(archive, rules)


def test_school_fixture_validates_required_workbook_sheets(tmp_path: Path) -> None:
    path = tmp_path / "schools.xlsx"
    workbook = Workbook()
    active = workbook.active
    assert active is not None
    workbook.remove(active)
    fields = dataset("indiana_school_directory_2025_2026").important_fields
    for sheet_name in ("SCHL", "NPSCHL"):
        sheet = workbook.create_sheet(sheet_name)
        sheet.append(fields)
        sheet.append(
            [
                "0001",
                "Synthetic School",
                "1 Test St",
                "Indianapolis",
                "IN",
                "46204",
                "Marion",
                "KG",
                "12",
            ]
        )
    workbook.save(path)

    validate_source(path, dataset("indiana_school_directory_2025_2026"))


def test_acquire_downloads_atomically_writes_manifest_and_reuses_cache(
    tmp_path: Path,
) -> None:
    source = (FIXTURES / "marion_county_boundary.geojson").read_bytes()
    calls: list[Request] = []

    def opener(request: Request, timeout: float) -> FakeResponse:
        calls.append(request)
        assert timeout == 12
        return FakeResponse(source, content_type="application/geo+json")

    first = acquire_dataset(
        dataset("marion_county_boundary"),
        cache_dir=tmp_path,
        timeout=12,
        opener=opener,
    )
    second = acquire_dataset(
        dataset("marion_county_boundary"),
        cache_dir=tmp_path,
        opener=opener,
    )
    metadata = json.loads(first.manifest_path.read_text(encoding="utf-8"))

    assert first.downloaded is True
    assert second.downloaded is False
    assert len(calls) == 1
    assert metadata["dataset_id"] == "marion_county_boundary"
    assert metadata["sha256"] == first.sha256
    assert metadata["etag"] == '"synthetic"'
    assert "User-agent" in dict(calls[0].header_items())


def test_force_redownloads_and_validate_existing_uses_local_file(
    tmp_path: Path,
) -> None:
    source = (FIXTURES / "marion_county_boundary.geojson").read_bytes()
    calls = 0

    def opener(request: Request, timeout: float) -> FakeResponse:
        nonlocal calls
        calls += 1
        return FakeResponse(source)

    rules = dataset("marion_county_boundary")
    acquire_dataset(rules, cache_dir=tmp_path, opener=opener)
    forced = acquire_dataset(rules, cache_dir=tmp_path, opener=opener, force=True)
    existing = acquire_dataset(
        rules, cache_dir=tmp_path, opener=opener, validate_existing=True
    )

    assert calls == 2
    assert forced.downloaded is True
    assert existing.downloaded is False


def test_missing_environment_fails_without_exposing_a_secret(tmp_path: Path) -> None:
    with pytest.raises(AcquisitionError, match="CENSUS_API_KEY") as error:
        acquire_dataset(
            dataset("acs_2024_block_group_demographics"),
            cache_dir=tmp_path,
            environment={},
        )

    assert "secret-value" not in str(error.value)


def test_environment_template_is_rendered_only_for_request(tmp_path: Path) -> None:
    content = (FIXTURES / "acs_block_groups.json").read_bytes()
    observed_url = ""

    def opener(request: Request, timeout: float) -> FakeResponse:
        nonlocal observed_url
        observed_url = request.full_url
        return FakeResponse(content)

    result = acquire_dataset(
        dataset("acs_2024_block_group_demographics"),
        cache_dir=tmp_path,
        environment={"CENSUS_API_KEY": "secret-value"},
        opener=opener,
    )
    manifest = result.manifest_path.read_text(encoding="utf-8")

    assert "secret-value" in observed_url
    assert "secret-value" not in manifest
    assert "{CENSUS_API_KEY}" in manifest


@pytest.mark.parametrize(
    ("response", "message"),
    [
        (FakeResponse(b"{}", content_type="text/html"), "Content-Type"),
        (FakeResponse(b"{}", status=503), "HTTP status 503"),
    ],
)
def test_bad_http_response_is_rejected_and_partial_file_removed(
    tmp_path: Path, response: FakeResponse, message: str
) -> None:
    def opener(request: Request, timeout: float) -> FakeResponse:
        return response

    with pytest.raises(AcquisitionError, match=message):
        acquire_dataset(
            dataset("marion_county_boundary"), cache_dir=tmp_path, opener=opener
        )

    assert not list(tmp_path.rglob(".*"))


def test_network_error_includes_manual_fallback(tmp_path: Path) -> None:
    def opener(request: Request, timeout: float) -> Any:
        raise URLError("synthetic outage")

    with pytest.raises(AcquisitionError, match="manual fallback"):
        acquire_dataset(
            dataset("marion_county_boundary"), cache_dir=tmp_path, opener=opener
        )


def test_validate_existing_reports_missing_cache(tmp_path: Path) -> None:
    with pytest.raises(AcquisitionError, match="no cached file exists"):
        acquire_dataset(
            dataset("marion_county_boundary"),
            cache_dir=tmp_path,
            validate_existing=True,
        )


@pytest.mark.parametrize(
    "document",
    [
        {"type": "FeatureCollection", "features": []},
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "properties": {"OBJECTID": 1},
                    "geometry": {"type": "Point", "coordinates": [500, 500]},
                }
            ],
        },
    ],
)
def test_invalid_geojson_quality_is_rejected(
    tmp_path: Path, document: dict[str, Any]
) -> None:
    path = tmp_path / "invalid.geojson"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(SourceValidationError):
        validate_source(path, dataset("marion_county_boundary"))


def test_invalid_archive_and_missing_source_are_rejected(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.zip"
    invalid.write_text("not a zip", encoding="utf-8")

    with pytest.raises(SourceValidationError, match="expected at least"):
        validate_source(invalid, dataset("census_block_groups_2024"))
    with pytest.raises(SourceValidationError, match="does not exist"):
        validate_source(tmp_path / "missing", dataset("marion_county_boundary"))


def test_malformed_json_is_wrapped_as_a_source_validation_error(
    tmp_path: Path,
) -> None:
    path = tmp_path / "malformed.geojson"
    path.write_text("{", encoding="utf-8")

    with pytest.raises(SourceValidationError, match="geojson validation failed"):
        validate_source(path, dataset("marion_county_boundary"))


@pytest.mark.parametrize(
    "document",
    [
        {"type": "Feature", "features": []},
        {"type": "FeatureCollection", "features": "not-a-list"},
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "properties": {
                        "OBJECTID": 1,
                        "SUM_ACRES": 1,
                        "DISPLAY": "Synthetic",
                    },
                    "geometry": {"type": "Point", "coordinates": [-86.1, 39.7]},
                }
            ],
        },
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "properties": {
                        "OBJECTID": 1,
                        "SUM_ACRES": 1,
                        "DISPLAY": "Synthetic",
                    },
                    "geometry": {"type": "Polygon", "coordinates": []},
                }
            ],
        },
    ],
)
def test_geojson_structure_errors_are_clear(
    tmp_path: Path, document: dict[str, Any]
) -> None:
    path = tmp_path / "invalid.geojson"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(SourceValidationError):
        validate_source(path, dataset("marion_county_boundary"))


def test_archive_missing_required_member_is_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "gtfs.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("agency.txt", "agency_name,agency_url,agency_timezone\n")

    with pytest.raises(SourceValidationError, match="missing required files"):
        validate_source(archive, dataset("indygo_gtfs"))


@pytest.mark.parametrize(
    "document",
    [
        {},
        [],
        [["NAME"], ["too", "wide"]],
        [
            [
                "NAME",
                "B01003_001E",
                "B01003_001M",
                "B08201_001E",
                "B08201_002E",
                "state",
                "county",
                "tract",
                "block group",
            ],
            ["Synthetic", "1", "1", "1", "1", "18", "001", "1", "1"],
        ],
    ],
)
def test_census_structure_and_geography_errors_are_rejected(
    tmp_path: Path, document: Any
) -> None:
    path = tmp_path / "census.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(SourceValidationError):
        validate_source(path, dataset("acs_2024_block_group_demographics"))
