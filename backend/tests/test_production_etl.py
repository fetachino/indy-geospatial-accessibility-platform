import json
import zipfile
from pathlib import Path

import pytest

from indy_accessibility_etl import production


def test_cached_source_discovery_and_geojson_routing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        production,
        "DATASET_FILES",
        {
            "marion_county_boundary": ("boundary", "boundary.geojson"),
            "hospital_locations_2023": ("hospitals", "hospitals.geojson"),
        },
    )
    boundary = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"OBJECTID": 1},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-86.3, 39.7],
                            [-86.0, 39.7],
                            [-86.0, 39.9],
                            [-86.3, 39.9],
                            [-86.3, 39.7],
                        ]
                    ],
                },
            }
        ],
    }
    hospital = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "id": "h-1",
                    "name": "Fixture Hospital",
                    "county": "MARION",
                },
                "geometry": {"type": "Point", "coordinates": [-86.15, 39.78]},
            }
        ],
    }
    for directory, name, payload in (
        ("boundary", "boundary.geojson", boundary),
        ("hospitals", "hospitals.geojson", hospital),
    ):
        target = tmp_path / directory
        target.mkdir()
        (target / name).write_text(json.dumps(payload), encoding="utf-8")
    result = production.run_production_etl(tmp_path)
    assert {record.dataset_id for record in result.records} == {
        "marion_county_boundary",
        "hospital_locations_2023",
    }
    assert len(result.audit) == 2


def test_gtfs_loader_reads_stops_from_cached_zip(tmp_path: Path) -> None:
    archive_path = tmp_path / "feed.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(
            "stops.txt",
            "stop_id,stop_name,stop_lat,stop_lon\ns-1,Fixture Stop,39.78,-86.15\n",
        )
    records = production._gtfs_records(archive_path)
    assert records[0].source_id == "s-1"
    assert records[0].geometry.geom_type == "Point"
