import importlib.util
from pathlib import Path

import pytest

_MODULE_PATH = Path("arcgis/prepare_accessibility.py")
_SPEC = importlib.util.spec_from_file_location("arcgis_prepare", _MODULE_PATH)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


def test_arcgis_config_and_field_validation(tmp_path: Path) -> None:
    config_path = Path("arcgis/config.example.json")
    config = _MODULE.load_config(config_path)
    assert config["analysis_crs"] == "EPSG:26916"
    csv_path = tmp_path / "results.csv"
    csv_path.write_text(
        ",".join(sorted(_MODULE.REQUIRED_FIELDS)) + "\n", encoding="utf-8"
    )
    assert _MODULE.validate_csv_fields(csv_path) == _MODULE.REQUIRED_FIELDS


def test_arcgis_missing_fields_are_actionable(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("geoid\nabc\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required fields"):
        _MODULE.validate_csv_fields(path)


def test_arcypy_detection_is_honest() -> None:
    assert isinstance(_MODULE.arcypy_available(), bool)
