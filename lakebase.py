"""
Lakebase (Databricks-managed Postgres) connection helper.

Connects using a LAKEBASE_URL from Databricks secrets.
All queries use the movie_night schema.
"""

import base64
import os
from contextlib import contextmanager

import psycopg2
from databricks.sdk import WorkspaceClient
from psycopg2.extras import RealDictCursor

_w = WorkspaceClient()

_SCOPE = os.environ.get("LAKEBASE_SECRET_SCOPE", "database")
_KEY = os.environ.get("LAKEBASE_SECRET_KEY", "movie-lakebase-url")


def _lakebase_url() -> str:
    """Fetch and decode the Lakebase connection URL from the Databricks secret scope.
    
    Note: The secret is DOUBLE base64-encoded, so we decode it twice.
    """
    secret = _w.secrets.get_secret(scope=_SCOPE, key=_KEY)
    
    # First decode
    first_decode = base64.b64decode(secret.value).decode("utf-8")
    
    # Second decode (double-encoded)
    conn_url = base64.b64decode(first_decode).decode("utf-8")
    
    return conn_url


@contextmanager
def get_connection():
    """Yield a raw psycopg2 connection with a RealDictCursor factory."""
    conn = psycopg2.connect(_lakebase_url(), cursor_factory=RealDictCursor)
    try:
        # Set search path to movie_night schema
        with conn.cursor() as cur:
            cur.execute("SET search_path TO movie_night, public")
            conn.commit()
        yield conn
    finally:
        conn.close()


def run_query(sql: str, params: tuple | dict | None = None) -> list[dict]:
    """Run a read query against Lakebase and return rows as list[dict]."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def execute(sql: str, params: tuple | dict | None = None):
    """Execute a write query (INSERT/UPDATE/DELETE) against Lakebase."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
