from typing import Any

import psycopg
import pytest
from fastapi.testclient import TestClient

from indy_accessibility_api import db, main
from indy_accessibility_api.db import database_url


class FakeResult:
    def __init__(
        self,
        row: tuple[Any, ...] | None = None,
        rows: list[tuple[Any, ...]] | None = None,
    ) -> None:
        self.row = row
        self.rows = rows or []

    def fetchone(self) -> tuple[Any, ...] | None:
        return self.row

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self.rows


class FakeConnection:
    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(self, sql: str, _params: object = ()) -> FakeResult:
        if "FROM analysis.runs" in sql:
            return FakeResult(
                ("run-1", "calc", "config", "hash", "succeeded", False, 1, {})
            )
        if "min(total" in sql:
            return FakeResult((0.0, 80.0, 40.0, 1, 0, 0, 0, 0))
        if "json_build_object" in sql:
            return FakeResult(
                rows=[('{"type":"Feature","geometry":null,"properties":{}}',)]
            )
        if "analysis.block_group_results" in sql:
            return FakeResult(("{}", "180970001001", 2, 50.0, 40.0, 46.0, []))
        return FakeResult(rows=[('{"type":"Point"}',)])


def test_validation_and_metadata() -> None:
    client = TestClient(main.app)
    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/metadata").json()["transit_threshold_m"] == 400
    assert client.get("/api/v1/block-groups?bbox=bad").status_code == 422
    assert (
        client.get("/api/v1/block-groups?min_score=90&max_score=10").status_code == 422
    )
    assert client.get("/api/v1/services?category=unknown").status_code == 422
    assert client.get("/api/v1/block-groups/not-a-geoid").status_code == 422


def test_database_url_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    assert database_url() == "postgresql://example"
    monkeypatch.delenv("DATABASE_URL")
    monkeypatch.setenv("POSTGRES_PASSWORD", "local-only")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    assert database_url() == "postgresql://indy_accessibility:local-only@localhost:5432/indy_accessibility"
    monkeypatch.delenv("POSTGRES_PASSWORD")
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        database_url()


def test_connection_context(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeConnection:
        def __enter__(self) -> "FakeConnection":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    monkeypatch.setattr(db.psycopg, "connect", lambda _url: FakeConnection())  # type: ignore[attr-defined]
    with db.connection() as conn:
        assert conn is not None


def test_connection_logs_and_reraises_database_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")

    def fail_connect(_url: str) -> Any:
        raise psycopg.OperationalError("connection refused")

    monkeypatch.setattr(psycopg, "connect", fail_connect)
    with pytest.raises(psycopg.OperationalError), db.connection():
        pass


def test_client_safe_database_error() -> None:
    assert main.db_error().status_code == 503


def test_api_features_and_summary_with_fake_database(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from contextlib import contextmanager

    @contextmanager
    def fake_connection() -> Any:
        yield FakeConnection()

    monkeypatch.setattr(main, "connection", fake_connection)
    client = TestClient(main.app)
    assert client.get("/api/v1/runs/latest").status_code == 200
    assert client.get("/api/v1/runs/latest/summary").status_code == 200
    assert client.get("/api/v1/block-groups").json()["type"] == "FeatureCollection"
    assert client.get("/api/v1/block-groups/180970001001").json()["type"] == "Feature"
    assert client.get("/api/v1/transit/stops").json()["type"] == "FeatureCollection"
    assert (
        client.get("/api/v1/services?category=hospital").json()["type"]
        == "FeatureCollection"
    )
