"""Pydantic contracts for the versioned accessibility API."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class RunMetadata(BaseModel):
    run_id: str
    calculation_version: str
    configuration_version: str
    configuration_hash: str
    status: Literal["succeeded"]
    population_available: bool
    row_count: int = Field(ge=0)
    source_lineage: dict[str, Any]


class Distribution(BaseModel):
    minimum: float
    maximum: float
    mean: float
    buckets: dict[str, int]


class RunSummary(BaseModel):
    run: RunMetadata
    score_distribution: Distribution


class GeoJSONFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"]
    features: list[dict[str, Any]]
    crs: dict[str, Any] = {"type": "name", "properties": {"name": "EPSG:4326"}}


class CategoryMetadata(BaseModel):
    categories: list[str]
    service_threshold_m: float
    transit_threshold_m: float
    score_range: tuple[float, float] = (0, 100)
