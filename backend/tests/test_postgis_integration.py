import os

import pytest

DATABASE_URL = os.getenv("POSTGIS_TEST_DATABASE_URL")


@pytest.mark.skipif(
    not DATABASE_URL, reason="POSTGIS_TEST_DATABASE_URL is not configured"
)
def test_postgis_schema_and_postgis_extension() -> None:
    psycopg = pytest.importorskip("psycopg")
    from indy_accessibility_etl.migrations import apply_migrations

    apply_migrations(DATABASE_URL)
    with psycopg.connect(DATABASE_URL) as connection:
        assert connection.execute("SELECT PostGIS_Version()").fetchone()[0]
        schemas = connection.execute(
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name IN ("
            "'boundaries', 'demographics', 'transit', 'services', 'etl')"
        ).fetchall()
        assert {row[0] for row in schemas} == {
            "boundaries",
            "demographics",
            "transit",
            "services",
            "etl",
        }


@pytest.mark.skipif(
    not DATABASE_URL, reason="POSTGIS_TEST_DATABASE_URL is not configured"
)
def test_fixture_load_is_transactional_and_repeatable() -> None:
    from indy_accessibility_etl.fixture import load_fixture_to_database

    first = load_fixture_to_database(DATABASE_URL)
    second = load_fixture_to_database(DATABASE_URL)
    assert first["loaded"] == second["loaded"] == 1
