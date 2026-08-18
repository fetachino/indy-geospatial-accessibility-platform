import os

import psycopg
import pytest

URL = os.getenv("POSTGIS_TEST_DATABASE_URL")


@pytest.mark.skipif(not URL, reason="POSTGIS_TEST_DATABASE_URL is not configured")
def test_analysis_schema_and_fixture_run() -> None:
    from indy_accessibility_analysis.runner import run_analysis

    url = URL
    assert url is not None
    summary = run_analysis(url)
    assert summary["status"] == "succeeded"
    assert isinstance(summary["row_count"], int)
    assert summary["row_count"] > 0
    assert isinstance(summary["run_id"], str)
    run_id = summary["run_id"]
    with psycopg.connect(url) as connection:
        run_count = connection.execute("SELECT count(*) FROM analysis.runs").fetchone()
        result_count = connection.execute(
            "SELECT count(*) FROM analysis.block_group_results WHERE run_id=%s",
            (run_id,),
        ).fetchone()
        assert run_count is not None and run_count[0] >= 1
        assert result_count is not None and result_count[0] == summary["row_count"]
