"""Integrity tests for source metadata and catalog configuration."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from pydantic import ValidationError

from indy_accessibility_data.catalog import (
    CatalogError,
    DataCatalog,
    Dataset,
    LicenseMetadata,
    ValidationRules,
    load_catalog,
)

EXPECTED_DATASETS = {
    "acs_2024_block_group_demographics",
    "census_block_groups_2024",
    "hospital_locations_2023",
    "ifd_fire_stations",
    "indiana_library_locations_2025",
    "indiana_school_directory_2025_2026",
    "indygo_gtfs",
    "marion_county_boundary",
    "snap_grocery_retailers_2005_2025",
}


def test_catalog_covers_every_planned_core_dataset() -> None:
    catalog = load_catalog()

    assert {dataset.id for dataset in catalog.datasets} == EXPECTED_DATASETS
    assert catalog.project_geography.state_fips == "18"
    assert catalog.project_geography.county_fips == "097"


def test_catalog_records_complete_source_and_risk_metadata() -> None:
    for dataset in load_catalog().datasets:
        assert urlsplit(dataset.source_page_url).scheme == "https"
        assert urlsplit(dataset.source_url).scheme == "https"
        assert dataset.important_fields
        assert dataset.known_limitations
        assert dataset.manual_fallback
        assert dataset.license.name
        assert dataset.license.notes
        assert "api key" not in dataset.source_url.casefold()


def test_catalog_marks_grocery_fallback_and_credential_requirement() -> None:
    catalog = load_catalog()

    grocery = catalog.dataset("snap_grocery_retailers_2005_2025")
    demographics = catalog.dataset("acs_2024_block_group_demographics")

    assert grocery.authoritative_status == "authoritative_fallback"
    assert demographics.requires_environment == ["CENSUS_API_KEY"]
    assert "{CENSUS_API_KEY}" in demographics.source_url


def test_catalog_rejects_unknown_dataset_with_valid_choices() -> None:
    with pytest.raises(CatalogError, match="available datasets"):
        load_catalog().dataset("not_a_dataset")


def test_catalog_reports_missing_and_invalid_json(tmp_path: Path) -> None:
    with pytest.raises(CatalogError, match="not found"):
        load_catalog(tmp_path / "missing.json")

    invalid = tmp_path / "invalid.json"
    invalid.write_text("{", encoding="utf-8")
    with pytest.raises(CatalogError, match="not valid JSON"):
        load_catalog(invalid)


def test_catalog_reports_structural_validation_error(tmp_path: Path) -> None:
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps({"catalog_version": "1"}), encoding="utf-8")

    with pytest.raises(CatalogError, match="validation failed"):
        load_catalog(path)


def test_url_models_reject_credentials_and_non_http_urls() -> None:
    with pytest.raises(ValidationError, match="credentials"):
        LicenseMetadata(name="unsafe", url="https://user:pass@example.com", notes="x")
    with pytest.raises(ValidationError, match="HTTP"):
        LicenseMetadata(name="unsafe", url="file:///tmp/data", notes="x")


def test_validation_rules_require_format_configuration() -> None:
    with pytest.raises(ValidationError, match="lacks its required configuration"):
        ValidationRules(kind="geojson")


def test_dataset_rejects_undeclared_or_missing_url_placeholders() -> None:
    raw = load_catalog().dataset("marion_county_boundary").model_dump()
    raw["source_url"] = "https://example.com/{TOKEN}"
    with pytest.raises(ValidationError, match="undeclared"):
        Dataset.model_validate(raw)

    raw["requires_environment"] = ["TOKEN"]
    raw["source_url"] = "https://example.com/no-template"
    with pytest.raises(ValidationError, match="missing"):
        Dataset.model_validate(raw)


def test_catalog_rejects_duplicate_ids_and_cache_filenames() -> None:
    raw = load_catalog().model_dump()
    raw["datasets"].append(dict(raw["datasets"][0]))

    with pytest.raises(ValidationError, match="dataset ids must be unique"):
        DataCatalog.model_validate(raw)

    raw["datasets"][-1]["id"] = "different_id"
    with pytest.raises(ValidationError, match="cache filenames must be unique"):
        DataCatalog.model_validate(raw)
