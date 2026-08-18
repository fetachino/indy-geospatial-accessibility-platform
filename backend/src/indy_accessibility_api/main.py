"""FastAPI application entry point."""

import json
import os
from typing import Any, Literal

import psycopg
from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .db import connection
from .schemas import (
    CategoryMetadata,
    Distribution,
    GeoJSONFeatureCollection,
    RunMetadata,
    RunSummary,
)


class HealthResponse(BaseModel):
    """Stable response returned by the service health check."""

    status: Literal["ok"]
    service: str


app = FastAPI(
    title="Indy Geospatial Accessibility API",
    summary="API foundation for Marion County accessibility indicators.",
    version="0.1.0",
)

origins = [
    item.strip()
    for item in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if item.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
api = APIRouter(prefix="/api/v1", tags=["accessibility"])


def db_error() -> HTTPException:
    return HTTPException(
        status_code=503, detail="Accessibility data is temporarily unavailable"
    )


def bbox_values(bbox: str | None) -> tuple[float, float, float, float] | None:
    if bbox is None:
        return None
    try:
        values = tuple(float(value) for value in bbox.split(","))
    except ValueError as exc:
        raise HTTPException(
            status_code=422, detail="bbox must be min_lon,min_lat,max_lon,max_lat"
        ) from exc
    if len(values) != 4 or not (
        -180 <= values[0] < values[2] <= 180 and -90 <= values[1] < values[3] <= 90
    ):
        raise HTTPException(status_code=422, detail="bbox bounds are invalid")
    return (values[0], values[1], values[2], values[3])


def feature_collection(rows: list[tuple[Any, ...]]) -> GeoJSONFeatureCollection:
    return GeoJSONFeatureCollection(
        type="FeatureCollection", features=[json.loads(row[0]) for row in rows]
    )


@api.get(
    "/runs/latest", response_model=RunMetadata, summary="Latest completed analysis run"
)
def latest_run() -> RunMetadata:
    try:
        with next(connection()) as conn:
            row = conn.execute(
                "SELECT run_id, calculation_version, configuration_version, "
                "configuration_hash, status, population_available, row_count, "
                "source_lineage FROM analysis.runs WHERE status='succeeded' "
                "ORDER BY completed_at DESC NULLS LAST LIMIT 1"
            ).fetchone()
    except (RuntimeError, psycopg.Error) as exc:
        raise db_error() from exc
    if row is None:
        raise HTTPException(
            status_code=404, detail="No completed analysis run is available"
        )
    return RunMetadata(
        run_id=str(row[0]),
        calculation_version=row[1],
        configuration_version=row[2],
        configuration_hash=row[3],
        status=row[4],
        population_available=row[5],
        row_count=row[6],
        source_lineage=row[7],
    )


@api.get(
    "/runs/latest/summary",
    response_model=RunSummary,
    summary="Latest run metadata and score distribution",
)
def latest_summary() -> RunSummary:
    run = latest_run()
    try:
        with next(connection()) as conn:
            stats = conn.execute(
                "SELECT min(total_accessibility_score), "
                "max(total_accessibility_score), "
                "avg(total_accessibility_score), "
                "count(*) FILTER (WHERE total_accessibility_score < 20), "
                "count(*) FILTER (WHERE total_accessibility_score >= 20 "
                "AND total_accessibility_score < 40), "
                "count(*) FILTER (WHERE total_accessibility_score >= 40 "
                "AND total_accessibility_score < 60), "
                "count(*) FILTER (WHERE total_accessibility_score >= 60 "
                "AND total_accessibility_score < 80), "
                "count(*) FILTER (WHERE total_accessibility_score >= 80) "
                "FROM analysis.block_group_results WHERE run_id=%s",
                (run.run_id,),
            ).fetchone()
    except psycopg.Error as exc:
        raise db_error() from exc
    if stats is None or stats[0] is None:
        raise HTTPException(
            status_code=404, detail="No results exist for the latest run"
        )
    return RunSummary(
        run=run,
        score_distribution=Distribution(
            minimum=stats[0],
            maximum=stats[1],
            mean=stats[2],
            buckets={
                "0-19": stats[3],
                "20-39": stats[4],
                "40-59": stats[5],
                "60-79": stats[6],
                "80-100": stats[7],
            },
        ),
    )


@api.get(
    "/metadata",
    response_model=CategoryMetadata,
    summary="Available categories and thresholds",
)
def metadata() -> CategoryMetadata:
    return CategoryMetadata(
        categories=["hospital", "grocery_store", "library", "fire_station", "school"],
        service_threshold_m=1600,
        transit_threshold_m=400,
    )


@api.get(
    "/block-groups",
    response_model=GeoJSONFeatureCollection,
    summary="Block-group accessibility features",
)
def block_groups(
    bbox: str | None = Query(default=None),
    min_score: float = Query(default=0, ge=0, le=100),
    max_score: float = Query(default=100, ge=0, le=100),
    limit: int = Query(default=1000, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
) -> GeoJSONFeatureCollection:
    if min_score > max_score:
        raise HTTPException(
            status_code=422, detail="min_score must not exceed max_score"
        )
    bounds = bbox_values(bbox)
    where = ["run_id=%s", "total_accessibility_score BETWEEN %s AND %s"]
    params: list[Any] = []
    try:
        run = latest_run()
        params.extend([run.run_id, min_score, max_score])
        if bounds:
            where.append(
                "geometry && ST_Transform(ST_MakeEnvelope(%s,%s,%s,%s,4326),26916)"
            )
            params.extend(bounds)
        params.extend([limit, offset])
        with next(connection()) as conn:
            rows = conn.execute(
                "SELECT json_build_object('type','Feature','geometry', "
                "ST_AsGeoJSON(ST_Transform(geometry,4326))::json, "
                "'properties',json_build_object('geoid',geoid, "
                "'total_accessibility_score',total_accessibility_score, "
                "'transit_access_score',transit_access_score, "
                "'service_access_score',service_access_score, "
                "'transit_stop_count',transit_stop_count, "
                "'status_flags',status_flags))::text FROM "
                "analysis.block_group_results WHERE "
                + " AND ".join(where)
                + " ORDER BY geoid LIMIT %s OFFSET %s",
                params,
            ).fetchall()
    except (RuntimeError, psycopg.Error) as exc:
        raise db_error() from exc
    return feature_collection(rows)


@api.get("/block-groups/{geoid}", summary="Block-group accessibility detail")
def block_group_detail(geoid: str) -> dict[str, Any]:
    if not geoid.isdigit() or len(geoid) not in {12, 15}:
        raise HTTPException(
            status_code=422, detail="geoid must be a Census geographic identifier"
        )
    try:
        run = latest_run()
        with next(connection()) as conn:
            row = conn.execute(
                "SELECT ST_AsGeoJSON(ST_Transform(geometry,4326)), geoid, "
                "transit_stop_count, transit_access_score, service_access_score, "
                "total_accessibility_score, status_flags FROM "
                "analysis.block_group_results WHERE run_id=%s AND geoid=%s",
                (run.run_id, geoid),
            ).fetchone()
    except (RuntimeError, psycopg.Error) as exc:
        raise db_error() from exc
    if row is None:
        raise HTTPException(status_code=404, detail="Block group not found")
    return {
        "type": "Feature",
        "geometry": json.loads(row[0]),
        "properties": {
            "geoid": row[1],
            "transit_stop_count": row[2],
            "transit_access_score": row[3],
            "service_access_score": row[4],
            "total_accessibility_score": row[5],
            "status_flags": row[6],
        },
    }


@api.get(
    "/transit/stops",
    response_model=GeoJSONFeatureCollection,
    summary="Transit stops by bounding box",
)
def transit_stops(
    bbox: str | None = Query(default=None),
    limit: int = Query(default=2000, ge=1, le=10000),
) -> GeoJSONFeatureCollection:
    bounds = bbox_values(bbox)
    clause = ""
    params: list[Any] = []
    if bounds:
        clause = (
            "WHERE geometry && ST_Transform(ST_MakeEnvelope(%s,%s,%s,%s,4326),26916)"
        )
        params.extend(bounds)
    params.append(limit)
    try:
        with next(connection()) as conn:
            rows = conn.execute(
                "SELECT ST_AsGeoJSON(ST_Transform(geometry,4326)) FROM transit.stops "
                + clause
                + " LIMIT %s",
                params,
            ).fetchall()
    except (RuntimeError, psycopg.Error) as exc:
        raise db_error() from exc
    return feature_collection(rows)


@api.get(
    "/services",
    response_model=GeoJSONFeatureCollection,
    summary="Essential services by category",
)
def services(
    category: str = Query(...),
    bbox: str | None = Query(default=None),
    limit: int = Query(default=2000, ge=1, le=10000),
) -> GeoJSONFeatureCollection:
    if category not in {
        "hospital",
        "grocery_store",
        "library",
        "fire_station",
        "school",
    }:
        raise HTTPException(status_code=422, detail="Unsupported service category")
    bounds = bbox_values(bbox)
    clause = ""
    params: list[Any] = [category]
    if bounds:
        clause = (
            " AND geometry && ST_Transform(ST_MakeEnvelope(%s,%s,%s,%s,4326),26916)"
        )
        params.extend(bounds)
    params.append(limit)
    try:
        with next(connection()) as conn:
            rows = conn.execute(
                "SELECT ST_AsGeoJSON(ST_Transform(geometry,4326)) "
                "FROM services.service_locations WHERE service_type=%s"
                + clause
                + " LIMIT %s",
                params,
            ).fetchall()
    except (RuntimeError, psycopg.Error) as exc:
        raise db_error() from exc
    return feature_collection(rows)


app.include_router(api)


@app.get("/health", response_model=HealthResponse, tags=["operations"])
def health_check() -> HealthResponse:
    """Report that the API process is ready to accept requests."""
    return HealthResponse(
        status="ok",
        service="indy-geospatial-accessibility-api",
    )
