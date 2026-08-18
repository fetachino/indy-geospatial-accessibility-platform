"""PostGIS runner and exports for the proximity baseline."""

from __future__ import annotations

import csv
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shapely import wkb
from shapely.strtree import STRtree

from indy_accessibility_etl.migrations import apply_migrations

from . import ANALYSIS_VERSION
from .core import load_config, result_status, score_components

SERVICE_TYPES = ("hospital", "grocery_store", "library", "fire_station", "school")


def run_analysis(
    url: str, output_root: Path = Path("data/processed")
) -> dict[str, object]:
    try:
        import psycopg
        from psycopg.types.json import Jsonb
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install psycopg to run the accessibility analysis") from exc
    config = load_config()
    apply_migrations(url)
    run_id = str(uuid.uuid4())
    with psycopg.connect(url) as connection, connection.transaction():
        connection.execute(
            "INSERT INTO analysis.runs(run_id, calculation_version, "
            "configuration_version, configuration_hash, status, source_lineage) "
            "VALUES (%s,%s,%s,%s,'running',%s)",
            (
                run_id,
                ANALYSIS_VERSION,
                config.configuration_version,
                config.hash,
                Jsonb(
                    {
                        "boundary": "boundaries.marion_county",
                        "block_groups": "demographics.census_block_groups",
                        "transit": "transit.stops",
                        "services": "services.service_locations",
                    }
                ),
            ),
        )
        block_groups = connection.execute(
            "SELECT geoid, ST_AsBinary(geometry), population "
            "FROM demographics.census_block_groups"
        ).fetchall()
        stops = [
            wkb.loads(row[0])
            for row in connection.execute(
                "SELECT ST_AsBinary(geometry) FROM transit.stops"
            ).fetchall()
        ]
        stop_tree = STRtree(stops) if stops else None
        services: dict[str, list[Any]] = {kind: [] for kind in SERVICE_TYPES}
        for kind, blob in connection.execute(
            "SELECT service_type, ST_AsBinary(geometry) FROM services.service_locations"
        ).fetchall():
            if kind in services:
                services[kind].append(wkb.loads(blob))
        service_trees = {
            kind: STRtree(items) if items else None for kind, items in services.items()
        }
        school_available = bool(services["school"])
        rows: list[tuple[Any, ...]] = []
        for geoid, blob, population in block_groups:
            geometry = wkb.loads(blob)
            origin = geometry.centroid
            nearby_stops: Any = (
                stop_tree.query(origin.buffer(config.transit_threshold_m))
                if stop_tree is not None
                else []
            )
            transit_count = len(nearby_stops)
            available: dict[str, bool | None] = {}
            nearest: dict[str, float | None] = {}
            for kind in SERVICE_TYPES:
                if kind == "school" and not school_available:
                    available[kind] = None
                    nearest[kind] = None
                else:
                    tree = service_trees[kind]
                    candidates: Any = (
                        tree.query(origin.buffer(config.service_threshold_m))
                        if tree is not None
                        else []
                    )
                    distances = [
                        origin.distance(services[kind][int(index)])
                        for index in candidates
                    ]
                    nearest_distance = min(distances) if distances else None
                    available[kind] = nearest_distance is not None
                    nearest[kind] = nearest_distance
            transit_score, service_score, total_score = score_components(
                transit_count, available, config
            )
            flags = result_status(available, population)
            stops_per_1000 = transit_count / population * 1000 if population else None
            service_count = sum(value is True for value in available.values())
            services_per_1000 = (
                service_count / population * 1000 if population else None
            )
            rows.append(
                (
                    run_id,
                    geoid,
                    geometry.wkt,
                    transit_count,
                    transit_count > 0,
                    available["hospital"],
                    available["grocery_store"],
                    available["library"],
                    available["fire_station"],
                    available["school"],
                    service_count,
                    nearest["hospital"],
                    nearest["grocery_store"],
                    nearest["library"],
                    nearest["fire_station"],
                    nearest["school"],
                    transit_score,
                    service_score,
                    total_score,
                    population,
                    stops_per_1000,
                    services_per_1000,
                    flags,
                    Jsonb({"calculation": ANALYSIS_VERSION}),
                )
            )
        insert_sql = (
            "INSERT INTO analysis.block_group_results("
            "run_id, geoid, geometry, transit_stop_count, "
            "transit_within_threshold, hospitals_available, "
            "grocery_stores_available, libraries_available, "
            "fire_stations_available, schools_available, "
            "essential_categories_available, nearest_hospital_m, "
            "nearest_grocery_store_m, nearest_library_m, "
            "nearest_fire_station_m, nearest_school_m, "
            "transit_access_score, service_access_score, "
            "total_accessibility_score, population, transit_stops_per_1000, "
            "service_locations_per_1000, status_flags, quality_flags) VALUES ("
            "%s,%s,ST_Multi(ST_SetSRID(ST_GeomFromText(%s),26916)),"
            "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        )
        with connection.cursor() as cursor:
            cursor.executemany(insert_sql, rows)
        connection.execute(
            "UPDATE analysis.runs SET status='succeeded', completed_at=now(), "
            "population_available=%s, row_count=%s WHERE run_id=%s",
            (any(row[19] is not None for row in rows), len(rows), run_id),
        )
    summary = {
        "run_id": run_id,
        "calculation_version": ANALYSIS_VERSION,
        "configuration_version": config.configuration_version,
        "configuration_hash": config.hash,
        "row_count": len(rows),
        "population_available": any(row[19] is not None for row in rows),
        "status": "succeeded",
        "generated_at": datetime.now(UTC).isoformat(),
    }
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / f"analysis-{run_id}-summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return summary


def export_run(
    url: str, run_id: str, output_root: Path = Path("data/processed")
) -> dict[str, str]:
    import psycopg

    output_root.mkdir(parents=True, exist_ok=True)
    with psycopg.connect(url) as connection:
        rows = connection.execute(
            "SELECT geoid, ST_AsGeoJSON(geometry), transit_stop_count, "
            "essential_categories_available, transit_access_score, "
            "service_access_score, total_accessibility_score, population, "
            "transit_stops_per_1000, service_locations_per_1000, status_flags "
            "FROM analysis.block_group_results WHERE run_id=%s ORDER BY geoid",
            (run_id,),
        ).fetchall()
    csv_path = output_root / f"analysis-{run_id}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "geoid",
                "transit_stop_count",
                "essential_categories_available",
                "transit_access_score",
                "service_access_score",
                "total_accessibility_score",
                "population",
                "transit_stops_per_1000",
                "service_locations_per_1000",
                "status_flags",
            ]
        )
        writer.writerows([row[0], *row[2:]] for row in rows)
    geojson_path = output_root / f"analysis-{run_id}.geojson"
    features = []
    for row in rows:
        properties = {
            "geoid": row[0],
            "transit_stop_count": row[2],
            "essential_categories_available": row[3],
            "transit_access_score": row[4],
            "service_access_score": row[5],
            "total_accessibility_score": row[6],
            "population": row[7],
            "transit_stops_per_1000": row[8],
            "service_locations_per_1000": row[9],
            "status_flags": row[10],
        }
        features.append(
            {
                "type": "Feature",
                "geometry": json.loads(row[1]),
                "properties": properties,
            }
        )
    geojson_path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}),
        encoding="utf-8",
    )
    return {"csv": str(csv_path), "geojson": str(geojson_path)}
