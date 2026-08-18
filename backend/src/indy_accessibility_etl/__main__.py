"""Command line entry point for migrations and fixture validation."""

import argparse
import json
from pathlib import Path

from .fixture import load_fixture, load_fixture_to_database
from .migrations import apply_migrations, database_url
from .production import load_production_to_database, run_production_etl


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m indy_accessibility_etl")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("migrate")
    subparsers.add_parser("load-fixture")
    subparsers.add_parser("load-fixture-db")
    subparsers.add_parser("production")
    subparsers.add_parser("production-db")
    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--output-root", default="data/processed")
    export = subparsers.add_parser("export")
    export.add_argument("run_id")
    export.add_argument("--output-root", default="data/processed")
    args = parser.parse_args()
    if args.command == "migrate":
        print(json.dumps({"applied": apply_migrations()}))
    elif args.command == "load-fixture":
        fixture_result = load_fixture()
        print(
            json.dumps(
                {
                    "loaded": len(fixture_result.loaded),
                    "audit": list(fixture_result.audit),
                }
            )
        )
    elif args.command == "load-fixture-db":
        print(json.dumps(load_fixture_to_database(database_url())))
    elif args.command in {"production", "production-db"}:
        if args.command == "production":
            production_result = run_production_etl()
            print(
                json.dumps(
                    {
                        "loaded": len(production_result.records),
                        "audit": len(production_result.audit),
                        "unsupported": production_result.unsupported,
                    }
                )
            )
        else:
            production_result = load_production_to_database(database_url())
            print(
                json.dumps(
                    {
                        "loaded": len(production_result.records),
                        "audit": len(production_result.audit),
                        "unsupported": production_result.unsupported,
                    }
                )
            )
    elif args.command == "analyze":
        from indy_accessibility_analysis.runner import run_analysis

        print(json.dumps(run_analysis(database_url(), Path(args.output_root))))
    else:
        from indy_accessibility_analysis.runner import export_run

        print(
            json.dumps(export_run(database_url(), args.run_id, Path(args.output_root)))
        )


if __name__ == "__main__":
    main()
