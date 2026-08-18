"""Pure scoring and proximity functions; no database or network side effects."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from shapely.geometry.base import BaseGeometry

CONFIG_PATH = Path(__file__).with_name("config.json")


@dataclass(frozen=True)
class AnalysisConfig:
    configuration_version: str
    transit_threshold_m: float
    service_threshold_m: float
    transit_target_count: int
    transit_weight: float
    service_weight: float
    service_categories: tuple[str, ...]

    @property
    def hash(self) -> str:
        payload = json.dumps(self.__dict__, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


def load_config(path: Path = CONFIG_PATH) -> AnalysisConfig:
    values = json.loads(path.read_text(encoding="utf-8"))
    if values["transit_weight"] + values["service_weight"] != 1:
        raise ValueError("transit_weight and service_weight must sum to 1")
    return AnalysisConfig(
        values["configuration_version"],
        values["transit_threshold_m"],
        values["service_threshold_m"],
        values["transit_target_count"],
        values["transit_weight"],
        values["service_weight"],
        tuple(values["service_categories"]),
    )


def nearest_distances(
    origin: BaseGeometry, facilities: list[BaseGeometry]
) -> list[float]:
    return sorted(
        origin.distance(item)
        for item in facilities
        if item is not None and not item.is_empty
    )


def category_metric(
    origin: BaseGeometry, facilities: list[BaseGeometry], threshold: float
) -> tuple[bool, float | None]:
    distances = nearest_distances(origin, facilities)
    if not distances:
        return False, None
    return distances[0] <= threshold, distances[0]


def score_components(
    transit_count: int,
    category_available: dict[str, bool | None],
    config: AnalysisConfig,
) -> tuple[float, float, float]:
    """Score formula: transit=min(count/target,1)*100; services=100*available/known.

    Unknown categories (source unavailable) are excluded from the service
    denominator. Total = transit_weight * transit + service_weight * services.
    """
    transit_score = (
        min(max(transit_count, 0) / max(config.transit_target_count, 1), 1.0) * 100
    )
    known = [value for value in category_available.values() if value is not None]
    service_score = (sum(known) / len(known) * 100) if known else 0.0
    total = (
        config.transit_weight * transit_score + config.service_weight * service_score
    )
    return (
        round(transit_score, 6),
        round(service_score, 6),
        round(max(0.0, min(total, 100.0)), 6),
    )


def result_status(
    category_available: dict[str, bool | None], population: int | None
) -> list[str]:
    flags = []
    if any(value is None for value in category_available.values()):
        flags.append("category_unavailable")
    if population is None:
        flags.append("acs_population_unavailable")
    return flags
