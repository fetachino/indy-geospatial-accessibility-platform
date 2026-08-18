"""Optional ArcGIS Pro preparation helper.

This module is safe to import without ArcPy. The CLI exits with a helpful
message when run outside an ArcGIS Pro Python environment.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = {
    "geoid",
    "total_accessibility_score",
    "transit_access_score",
    "service_access_score",
    "transit_stop_count",
    "status_flags",
}


def load_config(path: Path) -> dict[str, Any]:
    """Load and minimally validate a JSON ArcGIS preparation config."""
    config = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or not isinstance(
        config.get("field_aliases"), dict
    ):
        raise ValueError("config must contain a field_aliases object")
    return config


def validate_csv_fields(path: Path) -> set[str]:
    """Return CSV fields and fail clearly when the export is not compatible."""
    with path.open(newline="", encoding="utf-8") as stream:
        fields = set(csv.DictReader(stream).fieldnames or [])
    missing = REQUIRED_FIELDS - fields
    if missing:
        raise ValueError(
            f"export is missing required fields: {', '.join(sorted(missing))}"
        )
    return fields


def arcypy_available() -> bool:
    try:
        import arcpy  # noqa: F401
    except ImportError:
        return False
    return True


def run_arcgis(input_path: Path, output_gdb: Path, config: dict[str, Any]) -> None:
    try:
        import arcpy  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "ArcPy is unavailable. Run this command from an ArcGIS Pro Python "
            "environment; "
            "the open-source MapLibre workflow does not require ArcPy."
        ) from exc
    if input_path.suffix.lower() == ".csv":
        validate_csv_fields(input_path)
    output_gdb.parent.mkdir(parents=True, exist_ok=True)
    arcpy.env.overwriteOutput = True
    name = input_path.stem.replace("-", "_")
    target = str(output_gdb / name)
    if input_path.suffix.lower() in {".geojson", ".json"}:
        arcpy.conversion.JSONToFeatures(str(input_path), target)
    else:
        arcpy.conversion.TableToTable(str(input_path), str(output_gdb), name)
    for field, alias in config["field_aliases"].items():
        if arcpy.ListFields(target, field):
            arcpy.management.AlterField(target, field, new_field_alias=alias)
    print(f"Created ArcGIS output: {target}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-gdb", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        if args.input.suffix.lower() == ".csv":
            validate_csv_fields(args.input)
        run_arcgis(args.input, args.output_gdb, config)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ArcGIS preparation unavailable: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
