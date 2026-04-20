"""Starburst Galaxy Trino client with headless OAuth2 (JWT) auth.

No browser popup — programmatically completes the OAuth2 flow using
Galaxy login API + redirect endpoint. Token is managed by the Trino
client internally with auto-refresh.

Drop-in replacement for starburst_client.StarburstClient.
"""

import os
import re
import webbrowser
from pathlib import Path

import requests as http_requests
from dotenv import load_dotenv
from trino.dbapi import connect
from trino.auth import OAuth2Authentication

load_dotenv(Path(__file__).parent / ".env")

_RESERVED = {
    "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
    "TABLE", "SCHEMA", "DATABASE", "FROM", "WHERE", "SET", "INTO",
    "VALUES", "TRUNCATE", "MERGE", "GRANT", "REVOKE", "INDEX",
}

_IDENT_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")


class _HeadlessOAuth:
    """Handles the Galaxy OAuth2 flow without opening a browser."""

    def __init__(self, galaxy_host: str, email: str, password: str):
        self.galaxy_host = galaxy_host
        self.email = email
        self.password = password

    def handle_redirect(self, url: str, *args, **kwargs):
        """Called instead of webbrowser.open/open_new — completes OAuth programmatically."""
        s = http_requests.Session()
        # Step 1: Login to Galaxy portal
        s.post(
            f"https://{self.galaxy_host}/api/v1/login",
            json={"email": self.email, "password": self.password},
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        # Step 2: Hit the initiate URL — returns 303 → authorize URL
        r2 = s.get(url, allow_redirects=False, timeout=15)
        # Step 3: Follow the authorize redirect (gets the auth code)
        authorize_url = r2.headers.get("Location")
        if authorize_url:
            s.get(authorize_url, allow_redirects=True, timeout=15)
        # Step 4: Hit redirect endpoint to complete the callback
        s.get(
            f"https://{self.galaxy_host}/oauth/v2/redirect",
            allow_redirects=True,
            timeout=15,
        )


class StarburstClientJWT:
    """Drop-in replacement for StarburstClient with headless OAuth2 (no browser)."""

    def __init__(self):
        self.host = os.getenv("STARBURST_HOST")
        self.port = int(os.getenv("STARBURST_PORT", "443"))
        self.catalog = os.getenv("STARBURST_CATALOG")
        self.schema = os.getenv("STARBURST_SCHEMA")

        # Galaxy portal host (derived from cluster host)
        # e.g. datateam-free-cluster.trino.galaxy.starburst.io -> datateam.galaxy.starburst.io
        parts = self.host.split(".")
        domain_idx = next(i for i, p in enumerate(parts) if p == "galaxy")
        self.galaxy_host = parts[0].split("-")[0] + "." + ".".join(parts[domain_idx:])

        # User credentials for headless login
        user_raw = os.getenv("STARBURST_USER", "")
        self.email = user_raw.split("/")[0] if "/" in user_raw else user_raw
        self.password = os.getenv("STARBURST_PASSWORD", "")

        self._headless = _HeadlessOAuth(self.galaxy_host, self.email, self.password)
        self.auth_mode = "jwt"
        self._conn = None

        # Permanently patch webbrowser so ALL OAuth redirects are handled
        # headlessly — including token refreshes on later queries.
        webbrowser.open = self._headless.handle_redirect
        webbrowser.open_new = self._headless.handle_redirect
        webbrowser.open_new_tab = self._headless.handle_redirect

    def _get_auth(self):
        return OAuth2Authentication()

    def get_connection(self):
        if self._conn is not None:
            try:
                cur = self._conn.cursor()
                cur.execute("SELECT 1")
                cur.fetchall()
                return self._conn
            except Exception:
                self._conn = None

        self._conn = connect(
            host=self.host,
            port=self.port,
            http_scheme="https",
            auth=self._get_auth(),
            catalog=self.catalog,
            schema=self.schema,
        )
        # Force a connection to trigger auth now
        cur = self._conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchall()

        return self._conn

    _DML_RE = re.compile(
        r"^\s*(INSERT|UPDATE|DELETE|TRUNCATE|CREATE|DROP|ALTER|MERGE|GRANT|REVOKE)\b",
        re.IGNORECASE,
    )

    def execute(self, query: str) -> dict:
        """Execute a query. Returns {columns, rows} for SELECT or {rows_affected} for DML/DDL."""
        query = query.strip().rstrip(";")
        is_dml = bool(self._DML_RE.match(query))
        conn = self.get_connection()
        try:
            cur = conn.cursor()
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

    @staticmethod
    def validate_identifier(name: str):
        if not name or not _IDENT_RE.match(name):
            raise ValueError(f"Invalid identifier: '{name}'.")
        if name.upper() in _RESERVED:
            raise ValueError(f"Invalid identifier: '{name}' is a SQL reserved word.")

    @staticmethod
    def qualified_name(*parts: str) -> str:
        return ".".join(f'"{p}"' for p in parts)
