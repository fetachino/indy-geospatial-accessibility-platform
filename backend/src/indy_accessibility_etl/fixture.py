"""Small legal fixture ETL used when production data or Docker is unavailable."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from shapely.geometry import Point, Polygon
from shapely.geometry.base import BaseGeometry

from . import ANALYSIS_EPSG
from .geometry import GeometryDecision, validate_geometry


@dataclass(frozen=True)
class FixtureResult:
    loaded: tuple[dict[str, Any], ...]
    audit: tuple[dict[str, Any], ...]


def load_fixture() -> FixtureResult:
    """Normalize representative point records and exercise every quality rule."""
    county = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000)])
    records = (
        {"source_id": "stop-1", "name": "Fixture Stop", "geometry": Point(500, 500)},
        {"source_id": "stop-1", "name": "Duplicate Stop", "geometry": Point(500, 500)},
        {"source_id": "outside", "name": "Outside", "geometry": Point(1200, 500)},
    )
    loaded: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        source_id = str(record["source_id"])
        if source_id in seen:
            audit.append(
                {
                    "source_id": source_id,
                    "action": "duplicate",
                    "reason": "duplicate source identifier",
                }
            )
            continue
        seen.add(source_id)
        decision: GeometryDecision = validate_geometry(
            record["geometry"]
            if isinstance(record["geometry"], BaseGeometry)
            else Point(),
            source_epsg=ANALYSIS_EPSG,
            expected_type="Point",
            county_geometry=county,
        )
        audit.append(
            {
                "source_id": source_id,
                "action": decision.action,
                "reason": decision.reason,
            }
        )
        if decision.geometry is not None:
            loaded.append(
                {
                    "source_id": source_id,
                    "name": record["name"],
                    "geometry": decision.geometry,
                }
            )
    return FixtureResult(tuple(loaded), tuple(audit))


def load_fixture_to_database(url: str) -> dict[str, int | str]:
    """Load the fixture in one transaction, replacing only its stable IDs."""
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install psycopg to load the fixture into PostGIS") from exc
    result = load_fixture()
    run_id = str(uuid.uuid4())
    with psycopg.connect(url) as connection, connection.transaction():
        connection.execute(
            "INSERT INTO etl.load_runs(load_run_id, source_dataset_id, "
            "retrieved_at, status, "
            "transformation_version) VALUES (%s, %s, %s, 'running', %s)",
            (
                run_id,
                "fixture_transit",
                datetime.now(UTC),
                "milestone-2-v1",
            ),
        )
        for record in result.loaded:
            geometry = record["geometry"]
            connection.execute(
                "INSERT INTO transit.stops(source_id, name, source_crs, "
                "load_run_id, geometry) "
                "VALUES (%s, %s, %s, %s, ST_SetSRID(ST_GeomFromText(%s), 26916)) "
                "ON CONFLICT (source_id) DO UPDATE SET name = EXCLUDED.name, "
                "load_run_id = EXCLUDED.load_run_id, geometry = EXCLUDED.geometry",
                (
                    record["source_id"],
                    record["name"],
                    "EPSG:26916",
                    run_id,
                    geometry.wkt,
                ),
            )
        connection.execute(
            "UPDATE etl.load_runs SET completed_at = %s, status = 'succeeded', "
            "row_count = %s, "
            "rejected_count = %s WHERE load_run_id = %s",
            (
                datetime.now(UTC),
                len(result.loaded),
                len(result.audit) - len(result.loaded),
                run_id,
            ),
        )
    return {
        "load_run_id": run_id,
        "loaded": len(result.loaded),
        "rejected": len(result.audit) - len(result.loaded),
    }
