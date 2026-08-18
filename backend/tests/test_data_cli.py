"""Behavior tests for the public data-acquisition CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

from indy_accessibility_data.cli import build_parser, main


def test_catalog_command_lists_authority_status(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["catalog"]) == 0

    output = capsys.readouterr().out
    assert "indygo_gtfs" in output
    assert "[authoritative]" in output


def test_verbose_catalog_includes_source_and_limitations(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["catalog", "--verbose"]) == 0

    output = capsys.readouterr().out
    assert "organization:" in output
    assert "limitations:" in output


def test_acquire_reports_missing_environment_without_network(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = main(
        [
            "acquire",
            "acs_2024_block_group_demographics",
            "--cache-dir",
            str(tmp_path),
        ]
    )

    assert result == 1
    assert "CENSUS_API_KEY" in capsys.readouterr().err


def test_skip_unavailable_returns_success_and_reports_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = main(
        [
            "acquire",
            "acs_2024_block_group_demographics",
            "--cache-dir",
            str(tmp_path),
            "--skip-unavailable",
        ]
    )

    assert result == 0
    assert "ERROR:" in capsys.readouterr().err


def test_cli_reports_catalog_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = main(["--catalog", str(tmp_path / "missing.json"), "catalog"])

    assert result == 1
    assert "data catalog not found" in capsys.readouterr().err


def test_parser_rejects_conflicting_or_missing_acquisition_selection() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        main(["acquire"])
    with pytest.raises(SystemExit):
        main(["acquire", "indygo_gtfs", "--all"])
    assert parser.prog == "python -m indy_accessibility_data"
