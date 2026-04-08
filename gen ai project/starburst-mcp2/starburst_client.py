"""Starburst Galaxy Trino client with OAuth2 and BasicAuth fallback.

Provides connection management and query execution for the MCP server.
Validates identifiers to prevent SQL injection.
"""

import os
import re
from pathlib import Path
from dotenv import load_dotenv
from trino.dbapi import connect
from trino.auth import BasicAuthentication, OAuth2Authentication

load_dotenv(Path(__file__).parent / ".env")

_RESERVED = {
    "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
    "TABLE", "SCHEMA", "DATABASE", "FROM", "WHERE", "SET", "INTO",
    "VALUES", "TRUNCATE", "MERGE", "GRANT", "REVOKE", "INDEX",
}

_IDENT_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")


class StarburstClient:
    def __init__(self):
        self.host = os.getenv("STARBURST_HOST")
        self.port = int(os.getenv("STARBURST_PORT", "443"))
        self.catalog = os.getenv("STARBURST_CATALOG")
        self.schema = os.getenv("STARBURST_SCHEMA")

        self.client_id = os.getenv("STARBURST_CLIENT_ID")
        self.client_secret = os.getenv("STARBURST_CLIENT_SECRET")
        self.token_url = os.getenv("STARBURST_TOKEN_URL")
        self.user = os.getenv("STARBURST_USER")
        self.password = os.getenv("STARBURST_PASSWORD")

        if self.client_id and self.client_secret:
            self.auth_mode = "oauth"
        else:
            self.auth_mode = "basic"

    def _get_auth(self):
        if self.auth_mode == "oauth":
            return OAuth2Authentication()
        return BasicAuthentication(self.user, self.password)

    def get_connection(self):
        return connect(
            host=self.host,
            port=self.port,
            http_scheme="https",
            auth=self._get_auth(),
            catalog=self.catalog,
            schema=self.schema,
        )

    def execute(self, query: str) -> dict:
        """Execute a query. Returns {columns, rows} for SELECT or {rows_affected} for DML/DDL."""
        query = query.strip().rstrip(";")
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(query)
            if cur.description:
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                return {"columns": columns, "rows": rows}
            try:
                rows = cur.fetchall()
                if rows and len(rows) > 0 and len(rows[0]) > 0:
                    return {"rows_affected": rows[0][0]}
            except Exception:
                pass
            return {"rows_affected": 0, "status": "ok"}
        finally:
            conn.close()

    @staticmethod
    def validate_identifier(name: str):
        """Validate a SQL identifier (catalog, schema, or table name)."""
        if not name or not _IDENT_RE.match(name):
            raise ValueError(
                f"Invalid identifier: '{name}'. "
                "Must start with a letter and contain only letters, digits, underscores."
            )
        if name.upper() in _RESERVED:
            raise ValueError(
                f"Invalid identifier: '{name}' is a SQL reserved word."
            )

    @staticmethod
    def qualified_name(*parts: str) -> str:
        """Build a fully-qualified name like "catalog"."schema"."table"."""
        return ".".join(f'"{p}"' for p in parts)
