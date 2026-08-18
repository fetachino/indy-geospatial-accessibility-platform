"""Command-line interface for catalog inspection and source acquisition."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from indy_accessibility_data.acquisition import (
    DEFAULT_CACHE_DIR,
    AcquisitionError,
    acquire_dataset,
)
from indy_accessibility_data.catalog import (
    DEFAULT_CATALOG_PATH,
    CatalogError,
    Dataset,
    load_catalog,
)


def build_parser() -> argparse.ArgumentParser:
    """Create the stable public CLI parser."""
    parser = argparse.ArgumentParser(
        prog="python -m indy_accessibility_data",
        description="Inspect and acquire cataloged project source data.",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG_PATH,
        help="path to datasets.json",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    catalog_parser = subparsers.add_parser("catalog", help="list catalog datasets")
    catalog_parser.add_argument("--verbose", action="store_true")

    acquire_parser = subparsers.add_parser(
        "acquire", help="download and validate one or more datasets"
    )
    acquire_parser.add_argument("dataset_ids", nargs="*")
    acquire_parser.add_argument("--all", action="store_true", dest="all_datasets")
    acquire_parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    acquire_parser.add_argument("--force", action="store_true")
    acquire_parser.add_argument("--validate-existing", action="store_true")
    acquire_parser.add_argument(
        "--skip-unavailable",
        action="store_true",
        help="continue when credentials or a network source are unavailable",
    )
    acquire_parser.add_argument("--timeout", type=float, default=90.0)
    return parser


def main(arguments: list[str] | None = None) -> int:
    """Run the data CLI and return a process exit code."""
    parser = build_parser()
    options = parser.parse_args(arguments)
    try:
        catalog = load_catalog(options.catalog)
        if options.command == "catalog":
            for dataset in catalog.datasets:
                print(_catalog_line(dataset, verbose=options.verbose))
            return 0

        if options.all_datasets and options.dataset_ids:
            parser.error("provide dataset ids or --all, not both")
        if not options.all_datasets and not options.dataset_ids:
            parser.error("provide at least one dataset id or --all")
        datasets = (
            catalog.datasets
            if options.all_datasets
            else [catalog.dataset(dataset_id) for dataset_id in options.dataset_ids]
        )
        failures = 0
        for dataset in datasets:
            try:
                result = acquire_dataset(
                    dataset,
                    cache_dir=options.cache_dir,
                    force=options.force,
                    validate_existing=options.validate_existing,
                    timeout=options.timeout,
                )
            except AcquisitionError as error:
                print(f"ERROR: {error}", file=sys.stderr)
                failures += 1
                if not options.skip_unavailable:
                    return 1
                continue
            action = "downloaded" if result.downloaded else "validated cached"
            print(
                f"{dataset.id}: {action} {result.path} "
                f"({result.bytes} bytes, sha256={result.sha256})"
            )
        return 1 if failures and not options.skip_unavailable else 0
    except (CatalogError, AcquisitionError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


def _catalog_line(dataset: Dataset, *, verbose: bool) -> str:
    status = dataset.authoritative_status
    base = f"{dataset.id}: {dataset.name} [{status}]"
    if not verbose:
        return base
    return (
        f"{base}\n  organization: {dataset.source_organization}"
        f"\n  format: {dataset.expected_format}"
        f"\n  source: {dataset.source_page_url}"
        f"\n  limitations: {'; '.join(dataset.known_limitations)}"
    )
