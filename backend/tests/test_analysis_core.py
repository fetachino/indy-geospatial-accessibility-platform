from pathlib import Path

from shapely.geometry import GeometryCollection, Point

from indy_accessibility_analysis.core import (
    category_metric,
    load_config,
    score_components,
)


def test_threshold_boundary_is_inclusive() -> None:
    assert category_metric(Point(0, 0), [Point(400, 0)], 400) == (True, 400)
    assert category_metric(Point(0, 0), [Point(400.1, 0)], 400)[0] is False
    assert category_metric(Point(0, 0), [GeometryCollection()], 400) == (False, None)


def test_score_is_bounded_deterministic_and_config_driven() -> None:
    config = load_config()
    scores = score_components(3, {"hospital": True, "grocery_store": False}, config)
    assert scores == score_components(
        3, {"hospital": True, "grocery_store": False}, config
    )
    assert all(0 <= value <= 100 for value in scores)
    assert score_components(0, {"hospital": None}, config)[1] == 0


def test_config_hash_changes_when_threshold_changes(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        '{"configuration_version":"x","transit_threshold_m":401,'
        '"service_threshold_m":1600,"transit_target_count":3,'
        '"transit_weight":0.4,"service_weight":0.6,'
        '"service_categories":["hospital"]}',
        encoding="utf-8",
    )
    assert load_config().hash != load_config(config_path).hash
