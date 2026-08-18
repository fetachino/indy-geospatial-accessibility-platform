"""Command line entry point for migrations and fixture validation."""

import argparse
import json

from .fixture import load_fixture, load_fixture_to_database
from .migrations import apply_migrations, database_url


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m indy_accessibility_etl")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("migrate")
    subparsers.add_parser("load-fixture")
    subparsers.add_parser("load-fixture-db")
    args = parser.parse_args()
    if args.command == "migrate":
        print(json.dumps({"applied": apply_migrations()}))
    elif args.command == "load-fixture":
        result = load_fixture()
        print(json.dumps({"loaded": len(result.loaded), "audit": list(result.audit)}))
    else:
        print(json.dumps(load_fixture_to_database(database_url())))


if __name__ == "__main__":
    main()
