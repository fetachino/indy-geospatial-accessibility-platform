"""Idempotent migration runner; psycopg is imported only when used."""

import os
import re
from pathlib import Path

MIGRATIONS = Path(__file__).resolve().parents[3] / "database" / "migrations"


def database_url() -> str:
    value = os.getenv("DATABASE_URL")
    if value:
        return value
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "indy_accessibility")
    user = os.getenv("POSTGRES_USER", "indy_accessibility")
    password = os.getenv("POSTGRES_PASSWORD")
    if not password:
        raise RuntimeError("Set POSTGRES_PASSWORD or DATABASE_URL before connecting")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def apply_migrations(url: str | None = None) -> list[str]:
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "Install the project dependencies to use PostGIS ETL"
        ) from exc
    applied: list[str] = []
    with psycopg.connect(url or database_url()) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS etl")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS etl.schema_migrations "
            "(version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        for path in sorted(MIGRATIONS.glob("*.sql")):
            version = re.match(r"(\d+)_", path.name)
            if not version:
                raise RuntimeError(
                    f"Migration must start with a numeric version: {path.name}"
                )
            key = path.name
            if connection.execute(
                "SELECT 1 FROM etl.schema_migrations WHERE version = %s", (key,)
            ).fetchone():
                continue
            connection.execute(path.read_text(encoding="utf-8"))
            connection.execute(
                "INSERT INTO etl.schema_migrations(version) VALUES (%s)", (key,)
            )
            applied.append(key)
    return applied
