"""Small database boundary with client-safe error handling in the routes."""

import os
from collections.abc import Iterator

import psycopg


def database_url() -> str:
    value = os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL is not configured")
    return value


def connection() -> Iterator[psycopg.Connection]:
    with psycopg.connect(database_url()) as conn:
        yield conn
