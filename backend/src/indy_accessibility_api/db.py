"""Small database boundary with client-safe error handling in the routes."""

import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from urllib.parse import urlsplit

import psycopg

logger = logging.getLogger(__name__)


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
        raise RuntimeError(
            "Set DATABASE_URL or POSTGRES_PASSWORD before starting the API"
        )
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    url = database_url()
    target = urlsplit(url)
    logger.info(
        "Opening PostGIS connection host=%s port=%s database=%s user=%s",
        target.hostname or "unknown",
        target.port or "default",
        target.path.lstrip("/") or "unknown",
        target.username or "unknown",
    )
    try:
        with psycopg.connect(url) as conn:
            yield conn
    except psycopg.Error:
        logger.exception(
            "PostGIS connection/query failed host=%s database=%s user=%s",
            target.hostname or "unknown",
            target.path.lstrip("/") or "unknown",
            target.username or "unknown",
        )
        raise
