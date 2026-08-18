"""Pure geometry rules shared by fixture and database ETL paths."""

from dataclasses import dataclass
from typing import Any

from pyproj import Transformer
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

from . import ANALYSIS_EPSG


@dataclass(frozen=True)
class GeometryDecision:
    geometry: BaseGeometry | None
    action: str
    reason: str | None = None


def project_geometry(geometry: BaseGeometry, source_epsg: int) -> BaseGeometry:
    """Transform a geometry while preserving x/y order."""
    if source_epsg == ANALYSIS_EPSG:
        return geometry
    transformer = Transformer.from_crs(source_epsg, ANALYSIS_EPSG, always_xy=True)
    return transform(transformer.transform, geometry)


def validate_geometry(
    geometry: BaseGeometry,
    *,
    source_epsg: int,
    expected_type: str,
    county_geometry: BaseGeometry | None = None,
) -> GeometryDecision:
    """Project, conservatively repair, and reject unsafe geometries."""
    projected = project_geometry(geometry, source_epsg)
    if projected.is_empty:
        return GeometryDecision(None, "quarantined", "empty geometry")
    action = "loaded"
    if not projected.is_valid:
        repaired = projected.buffer(0)
        if repaired.is_empty or not repaired.is_valid:
            return GeometryDecision(
                None, "quarantined", "invalid geometry could not be repaired"
            )
        projected = repaired
        action = "repaired"
    if expected_type == "Point" and projected.geom_type != "Point":
        return GeometryDecision(
            None, "quarantined", f"expected Point, got {projected.geom_type}"
        )
    if expected_type == "MultiPolygon" and projected.geom_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        return GeometryDecision(
            None, "quarantined", f"expected polygon, got {projected.geom_type}"
        )
    if county_geometry is not None and not county_geometry.covers(projected):
        return GeometryDecision(
            None, "quarantined", "geometry is outside Marion County"
        )
    return GeometryDecision(projected, action)


def feature_source_id(properties: dict[str, Any], fallback: str) -> str:
    """Choose a stable source identifier without inventing business IDs."""
    for key in ("source_id", "id", "OBJECTID", "GEOID", "stop_id", "route_id"):
        value = properties.get(key)
        if value not in (None, ""):
            return str(value)
    return fallback
