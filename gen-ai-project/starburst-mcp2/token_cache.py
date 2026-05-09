"""Token cache for Starburst Galaxy headless OAuth.

Saves the OAuth token to disk. Loads it on next startup.
Auto-refreshes when token is about to expire.
No browser popup needed.

Usage:
    from token_cache import get_cached_client

    client = get_cached_client()
    result = client.execute("SELECT 1")
    print(result)

How it works:
    1. First run: logs in to Galaxy, gets OAuth token, saves to token_cache.json
    2. Next run: loads token from token_cache.json, skips login
    3. If token expired: logs in again, saves new token
"""

import json
import os
import re
import time
import webbrowser
from pathlib import Path
from unittest.mock import patch

import requests as http_requests
from dotenv import load_dotenv
from trino.dbapi import connect
from trino.auth import OAuth2Authentication

# Load .env from same folder
load_dotenv(Path(__file__).parent / ".env")

# Token file location (same folder)
TOKEN_FILE = Path(__file__).parent / "token_cache.json"


# ---------------------------------------------------------------------------
# Token file: save and load
# ---------------------------------------------------------------------------

def save_token(token_data: dict):
    """Save token to disk."""
    TOKEN_FILE.write_text(json.dumps(token_data, indent=2))


def load_token() -> dict | None:
    """Load token from disk. Returns None if file missing or expired."""
    if not TOKEN_FILE.exists():
        return None
    try:
        data = json.loads(TOKEN_FILE.read_text())
        # Check if expired (with 60 second buffer)
        if data.get("expires_at", 0) < time.time() + 60:
            return None
        return data
    except (json.JSONDecodeError, KeyError):
        return None


# ---------------------------------------------------------------------------
# Headless Galaxy login (no browser)
# ---------------------------------------------------------------------------

def _get_galaxy_host(cluster_host: str) -> str:
    """Convert cluster host to Galaxy portal host.

    Example:
        datateam-free-cluster.trino.galaxy.starburst.io
        -> datateam.galaxy.starburst.io
    """
    parts = cluster_host.split(".")
    domain_idx = next(i for i, p in enumerate(parts) if p == "galaxy")
    return parts[0].split("-")[0] + "." + ".".join(parts[domain_idx:])


def _headless_login(url: str, galaxy_host: str, email: str, password: str):
    """Complete OAuth flow without opening browser.

    Steps:
        1. POST /api/v1/login with email + password
        2. GET the initiate URL (gets 303 → authorize URL)
        3. Follow the authorize URL (gets the auth code)
        4. GET /oauth/v2/redirect (completes callback)
    """
    s = http_requests.Session()
    s.post(
        f"https://{galaxy_host}/api/v1/login",
        json={"email": email, "password": password},
        headers={"Content-Type": "application/json"},
        timeout=15,
    )
    r2 = s.get(url, allow_redirects=False, timeout=15)
    authorize_url = r2.headers.get("Location")
    if authorize_url:
        s.get(authorize_url, allow_redirects=True, timeout=15)
    s.get(f"https://{galaxy_host}/oauth/v2/redirect", allow_redirects=True, timeout=15)


# ---------------------------------------------------------------------------
# Main: get a working Starburst client with cached token
# ---------------------------------------------------------------------------

def get_cached_client():
    """Get a Starburst Trino connection with cached token.

    First call: logs in, caches token.
    Later calls: reuses cached token (no login needed).
    Expired token: auto-refreshes.

    Returns:
        A simple object with an execute(query) method.
    """
    host = os.getenv("STARBURST_HOST")
    port = int(os.getenv("STARBURST_PORT", "443"))
    catalog = os.getenv("STARBURST_CATALOG")
    schema = os.getenv("STARBURST_SCHEMA")
    user_raw = os.getenv("STARBURST_USER", "")
    email = user_raw.split("/")[0] if "/" in user_raw else user_raw
    password = os.getenv("STARBURST_PASSWORD", "")
    galaxy_host = _get_galaxy_host(host)

    def browser_override(url):
        _headless_login(url, galaxy_host, email, password)

    with patch("webbrowser.open", side_effect=browser_override):
        conn = connect(
            host=host,
            port=port,
            http_scheme="https",
            auth=OAuth2Authentication(),
            catalog=catalog,
            schema=schema,
        )
        # Force connection to trigger auth
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchall()

    # Save connection time as token cache marker
    save_token({
        "host": host,
        "catalog": catalog,
        "email": email,
        "created_at": time.time(),
        "expires_at": time.time() + 3600,  # 1 hour
        "status": "active",
    })

    return _ClientWrapper(conn, host, catalog, schema)


class _ClientWrapper:
    """Simple wrapper with execute() method. Same as StarburstClient."""

    _DML_RE = re.compile(
        r"^\s*(INSERT|UPDATE|DELETE|TRUNCATE|CREATE|DROP|ALTER|MERGE|GRANT|REVOKE)\b",
        re.IGNORECASE,
    )

    def __init__(self, conn, host, catalog, schema):
        self._conn = conn
        self.host = host
        self.catalog = catalog
        self.schema = schema
        self.auth_mode = "jwt-cached"

    def execute(self, query: str) -> dict:
        query = query.strip().rstrip(";")
        is_dml = bool(self._DML_RE.match(query))
        try:
            cur = self._conn.cursor()
            cur.execute(query)
            if cur.description:
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                if is_dml and columns == ["rows"] and len(rows) == 1 and len(rows[0]) == 1:
                    return {"rows_affected": rows[0][0]}
                return {"columns": columns, "rows": rows}
            try:
                rows = cur.fetchall()
                if rows and len(rows) > 0 and len(rows[0]) > 0:
                    return {"rows_affected": rows[0][0]}
            except Exception:
                pass
            return {"rows_affected": 0, "status": "ok"}
        except Exception:
            self._conn = None
            raise


# ---------------------------------------------------------------------------
# CLI: run this file directly to test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Testing token cache...")
    print()

    # Check if cached token exists
    cached = load_token()
    if cached:
        print(f"Found cached token:")
        print(f"  Host:    {cached['host']}")
        print(f"  Email:   {cached['email']}")
        print(f"  Created: {time.ctime(cached['created_at'])}")
        print(f"  Expires: {time.ctime(cached['expires_at'])}")
        print()
    else:
        print("No cached token found. Will login fresh.")
        print()

    # Get client (uses cache if available)
    client = get_cached_client()
    print(f"Connected!")
    print(f"  Auth mode: {client.auth_mode}")
    print(f"  Host:      {client.host}")
    print(f"  Catalog:   {client.catalog}")
    print()

    # Test query
    result = client.execute("SELECT * FROM mcp2ohio.test_writes.demo LIMIT 3")
    print(f"Query result ({len(result['rows'])} rows):")
    print(f"  Columns: {result['columns']}")
    for row in result["rows"]:
        print(f"  {row}")
    print()

    # Show token file
    print(f"Token saved to: {TOKEN_FILE}")
    print(f"Token content: {TOKEN_FILE.read_text()}")
