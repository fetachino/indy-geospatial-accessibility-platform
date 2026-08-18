from pathlib import Path

from indy_accessibility_etl import ANALYSIS_EPSG
from indy_accessibility_etl.fixture import load_fixture
from indy_accessibility_etl.geometry import project_geometry, validate_geometry

ROOT = Path(__file__).resolve().parents[2]


def test_fixture_etl_loads_only_unique_in_county_features() -> None:
    result = load_fixture()
    assert len(result.loaded) == 1
    assert {entry["action"] for entry in result.audit} == {
        "loaded",
        "duplicate",
        "quarantined",
    }


def test_geometry_projection_and_repair() -> None:
    from shapely.geometry import Point, Polygon

    projected = project_geometry(Point(-86.16, 39.77), 4326)
    assert projected.x != -86.16
    assert (
        validate_geometry(
            Polygon([(0, 0), (10, 10), (0, 10), (10, 0), (0, 0)]),
            source_epsg=ANALYSIS_EPSG,
            expected_type="MultiPolygon",
        ).action
        == "repaired"
    )


def test_migration_defines_required_objects() -> None:
    sql = (ROOT / "database" / "migrations" / "001_initial.sql").read_text(
        encoding="utf-8"
    )
    for expected in (
        "boundaries.marion_county",
        "demographics.census_block_groups",
        "transit.stops",
        "transit.routes",
        "services.hospitals",
        "services.grocery_stores",
        "services.schools",
        "services.libraries",
        "services.fire_stations",
        "etl.load_runs",
    ):
        assert expected in sql
    assert "26916" in sql
