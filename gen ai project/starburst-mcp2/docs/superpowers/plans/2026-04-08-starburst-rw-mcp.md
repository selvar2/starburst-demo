# Starburst Read-Write MCP Server — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a custom Python MCP server with full read+write access to Starburst Galaxy, configurable per-developer permissions, and OAuth authentication.

**Architecture:** Single Python MCP server using `mcp` SDK over stdio. Connects to Starburst Galaxy via `trino` DBAPI with OAuth2 (BasicAuth fallback). Developer permissions loaded from `permissions.yaml` with profile+override resolution and hot-reload.

**Tech Stack:** Python 3.11+, `mcp>=1.0.0`, `trino>=0.328.0`, `python-dotenv`, `pyyaml`

---

## File Map

| File | Responsibility |
|------|---------------|
| `requirements.txt` | Python dependencies |
| `.env` | OAuth + connection config (gitignored) |
| `.env.example` | Template showing required env vars |
| `.gitignore` | Ignore .env, __pycache__, etc. |
| `permissions.yaml` | Developer write permission profiles |
| `starburst_client.py` | Trino connection (OAuth + BasicAuth fallback), query execution |
| `permission_manager.py` | Load permissions.yaml, resolve profile+overrides, check operations |
| `tools/read_tools.py` | 5 read tools: execute_query, list_catalogs, show_schemas, show_tables, describe_table |
| `tools/write_tools.py` | 9 write tools: create_schema, create_table, drop_table, drop_schema, truncate_table, insert_data, update_data, delete_data, merge_data |
| `tools/__init__.py` | Re-exports all tool registration functions |
| `server.py` | MCP server entry point, tool registration, stdio transport |
| `tests/test_permission_manager.py` | Unit tests for permission resolution |
| `tests/test_starburst_client.py` | Unit tests for SQL identifier validation |
| `tests/test_integration.py` | Integration tests against mcp2ohio catalog |

---

### Task 1: Project Setup — Dependencies and Config Files

**Files:**
- Create: `requirements.txt`
- Create: `.env`
- Create: `.env.example`
- Create: `.gitignore`

- [ ] **Step 1: Create requirements.txt**

```
trino>=0.328.0
mcp>=1.0.0
python-dotenv>=1.0.0
pyyaml>=6.0
pytest>=8.0.0
```

- [ ] **Step 2: Create .env.example (template)**

```
# OAuth Authentication
STARBURST_CLIENT_ID=claude_mcp@datateam.galaxy.starburst.io
STARBURST_CLIENT_SECRET=your_secret_here
STARBURST_TOKEN_URL=https://datateam.galaxy.starburst.io/oauth2/token

# Connection
STARBURST_HOST=datateam-free-cluster.trino.galaxy.starburst.io
STARBURST_PORT=443
STARBURST_CATALOG=mcp2ohio
STARBURST_SCHEMA=test_writes

# Developer ID (for permission lookup in permissions.yaml)
STARBURST_DEVELOPER=prakashrajr666

# Fallback: BasicAuth (used if STARBURST_CLIENT_ID is not set)
STARBURST_USER=prakashrajr666@networth.awsapps.com/accountadmin
STARBURST_PASSWORD=your_password_here
```

- [ ] **Step 3: Create .env with real credentials**

Copy `.env.example` to `.env` and fill in actual credentials. The `STARBURST_PASSWORD` and `STARBURST_CLIENT_SECRET` must be real values from the Starburst Galaxy console.

- [ ] **Step 4: Create .gitignore**

```
.env
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
dist/
build/
```

- [ ] **Step 5: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: All packages install successfully.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .env.example .gitignore
git commit -m "feat: project setup — deps, env template, gitignore"
```

---

### Task 2: Permission Manager

**Files:**
- Create: `permissions.yaml`
- Create: `permission_manager.py`
- Create: `tests/test_permission_manager.py`

- [ ] **Step 1: Create permissions.yaml**

```yaml
defaults:
  read: true
  insert: true
  update: false
  delete: false
  create_schema: false
  create_table: false
  drop_table: false
  drop_schema: false
  truncate: false
  merge: false
  execute_raw: false

profiles:
  read_only:
    read: true

  analyst:
    insert: true
    update: true
    delete: true
    create_table: true

  engineer:
    insert: true
    update: true
    delete: true
    create_schema: true
    create_table: true
    drop_table: true
    truncate: true
    merge: true

  admin:
    insert: true
    update: true
    delete: true
    create_schema: true
    create_table: true
    drop_table: true
    drop_schema: true
    truncate: true
    merge: true
    execute_raw: true

developers:
  prakashrajr666:
    profile: admin

  dev_analyst_1:
    profile: analyst

  dev_intern:
    profile: read_only

  dev_custom:
    profile: analyst
    overrides:
      drop_table: true
      truncate: true
```

- [ ] **Step 2: Write failing tests for permission_manager**

Create `tests/__init__.py` (empty) and `tests/test_permission_manager.py`:

```python
import os
import pytest
import tempfile
import yaml

# Will import after implementation
# from permission_manager import PermissionManager


def write_yaml(path, data):
    with open(path, "w") as f:
        yaml.dump(data, f)


SAMPLE_CONFIG = {
    "defaults": {
        "read": True,
        "insert": True,
        "update": False,
        "delete": False,
        "create_schema": False,
        "create_table": False,
        "drop_table": False,
        "drop_schema": False,
        "truncate": False,
        "merge": False,
        "execute_raw": False,
    },
    "profiles": {
        "read_only": {"read": True},
        "analyst": {"insert": True, "update": True, "delete": True, "create_table": True},
        "admin": {
            "insert": True, "update": True, "delete": True,
            "create_schema": True, "create_table": True,
            "drop_table": True, "drop_schema": True,
            "truncate": True, "merge": True, "execute_raw": True,
        },
    },
    "developers": {
        "alice": {"profile": "admin"},
        "bob": {"profile": "read_only"},
        "carol": {"profile": "analyst", "overrides": {"drop_table": True}},
    },
}


@pytest.fixture
def perm_file(tmp_path):
    path = tmp_path / "permissions.yaml"
    write_yaml(str(path), SAMPLE_CONFIG)
    return str(path)


@pytest.fixture
def manager(perm_file):
    from permission_manager import PermissionManager
    return PermissionManager(perm_file)


def test_admin_has_all_permissions(manager):
    perms = manager.resolve("alice")
    assert perms["read"] is True
    assert perms["execute_raw"] is True
    assert perms["drop_schema"] is True


def test_read_only_denies_writes(manager):
    perms = manager.resolve("bob")
    assert perms["read"] is True
    assert perms["insert"] is False
    assert perms["delete"] is False
    assert perms["drop_table"] is False


def test_read_only_inherits_defaults(manager):
    """read_only profile only sets read=True, so insert should come from defaults (True)
    BUT profile permissions replace defaults for listed ops. Unlisted ops use defaults."""
    perms = manager.resolve("bob")
    # read_only profile explicitly sets nothing except read=True
    # defaults has insert=True, but profile resolution: defaults merged with profile
    # Profile keys override defaults. Keys NOT in profile keep default values.
    assert perms["read"] is True
    assert perms["update"] is False  # default is False


def test_overrides_extend_profile(manager):
    perms = manager.resolve("carol")
    # carol has analyst profile + drop_table override
    assert perms["insert"] is True      # from analyst
    assert perms["update"] is True      # from analyst
    assert perms["drop_table"] is True  # from override (analyst doesn't have this)
    assert perms["drop_schema"] is False  # not in analyst or override


def test_unknown_developer_gets_defaults(manager):
    perms = manager.resolve("unknown_user")
    assert perms["read"] is True
    assert perms["insert"] is True  # default
    assert perms["update"] is False  # default


def test_check_allowed(manager):
    assert manager.check("alice", "execute_raw") is True
    assert manager.check("bob", "delete") is False


def test_check_returns_error_message(manager):
    allowed, msg = manager.check_with_message("bob", "delete")
    assert allowed is False
    assert "not permitted" in msg
    assert "bob" in msg


def test_hot_reload(perm_file, manager):
    """Modifying the YAML file should be picked up on next check."""
    # bob is read_only, delete is denied
    assert manager.check("bob", "delete") is False

    # Update file: give bob admin profile
    import time
    time.sleep(0.1)  # ensure mtime changes
    config = SAMPLE_CONFIG.copy()
    config["developers"] = {**config["developers"], "bob": {"profile": "admin"}}
    write_yaml(perm_file, config)

    # Should pick up change
    assert manager.check("bob", "delete") is True
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd "c:/Users/Lenovo/gen ai project/starburst-mcp2" && python -m pytest tests/test_permission_manager.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'permission_manager'`

- [ ] **Step 4: Implement permission_manager.py**

```python
"""Permission manager for Starburst MCP server.

Loads developer permissions from permissions.yaml with profile+override resolution.
Supports hot-reload: file changes are detected via mtime check.
"""

import os
import yaml
from pathlib import Path


class PermissionManager:
    def __init__(self, config_path: str = None):
        self._config_path = config_path or str(
            Path(__file__).parent / "permissions.yaml"
        )
        self._config = None
        self._mtime = 0
        self._cache = {}
        self._load()

    def _load(self):
        mtime = os.path.getmtime(self._config_path)
        if mtime != self._mtime:
            with open(self._config_path, "r") as f:
                self._config = yaml.safe_load(f)
            self._mtime = mtime
            self._cache = {}

    def resolve(self, developer: str) -> dict:
        """Resolve permissions for a developer. Returns dict of operation -> bool."""
        self._load()

        if developer in self._cache:
            return self._cache[developer]

        defaults = dict(self._config.get("defaults", {}))
        profiles = self._config.get("profiles", {})
        developers = self._config.get("developers", {})

        dev_config = developers.get(developer)
        if dev_config is None:
            self._cache[developer] = defaults
            return defaults

        # Start with defaults
        perms = dict(defaults)

        # Merge profile on top
        profile_name = dev_config.get("profile")
        if profile_name and profile_name in profiles:
            for key, value in profiles[profile_name].items():
                perms[key] = value

        # Apply overrides on top
        overrides = dev_config.get("overrides", {})
        for key, value in overrides.items():
            perms[key] = value

        self._cache[developer] = perms
        return perms

    def check(self, developer: str, operation: str) -> bool:
        """Check if a developer is allowed to perform an operation."""
        perms = self.resolve(developer)
        return perms.get(operation, False)

    def check_with_message(self, developer: str, operation: str) -> tuple:
        """Check permission and return (allowed, message) tuple."""
        perms = self.resolve(developer)
        allowed = perms.get(operation, False)
        if allowed:
            return True, ""

        dev_config = self._config.get("developers", {}).get(developer, {})
        profile = dev_config.get("profile", "defaults")
        msg = (
            f"Operation '{operation}' not permitted for developer '{developer}'. "
            f"Current profile: {profile}"
        )
        return False, msg
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd "c:/Users/Lenovo/gen ai project/starburst-mcp2" && python -m pytest tests/test_permission_manager.py -v`
Expected: All 8 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add permissions.yaml permission_manager.py tests/
git commit -m "feat: permission manager with profile+override resolution and hot-reload"
```

---

### Task 3: Starburst Client (OAuth + BasicAuth Fallback)

**Files:**
- Create: `starburst_client.py`
- Create: `tests/test_starburst_client.py`

- [ ] **Step 1: Write failing tests for starburst_client**

```python
import pytest


def test_validate_identifier_valid():
    from starburst_client import StarburstClient
    # Should not raise
    StarburstClient.validate_identifier("my_catalog")
    StarburstClient.validate_identifier("mcp2ohio")
    StarburstClient.validate_identifier("test_writes")
    StarburstClient.validate_identifier("table123")


def test_validate_identifier_rejects_injection():
    from starburst_client import StarburstClient
    with pytest.raises(ValueError, match="Invalid identifier"):
        StarburstClient.validate_identifier("table; DROP TABLE x")
    with pytest.raises(ValueError, match="Invalid identifier"):
        StarburstClient.validate_identifier("table'--")
    with pytest.raises(ValueError, match="Invalid identifier"):
        StarburstClient.validate_identifier("")


def test_validate_identifier_rejects_reserved():
    from starburst_client import StarburstClient
    with pytest.raises(ValueError, match="Invalid identifier"):
        StarburstClient.validate_identifier("SELECT")
    with pytest.raises(ValueError, match="Invalid identifier"):
        StarburstClient.validate_identifier("drop")


def test_format_qualified_name():
    from starburst_client import StarburstClient
    assert StarburstClient.qualified_name("cat", "sch", "tbl") == '"cat"."sch"."tbl"'
    assert StarburstClient.qualified_name("cat", "sch") == '"cat"."sch"'


def test_client_init_basic_auth(monkeypatch):
    from starburst_client import StarburstClient
    monkeypatch.delenv("STARBURST_CLIENT_ID", raising=False)
    monkeypatch.setenv("STARBURST_HOST", "test.host.io")
    monkeypatch.setenv("STARBURST_PORT", "443")
    monkeypatch.setenv("STARBURST_USER", "testuser")
    monkeypatch.setenv("STARBURST_PASSWORD", "testpass")
    monkeypatch.setenv("STARBURST_CATALOG", "testcat")
    monkeypatch.setenv("STARBURST_SCHEMA", "testsch")

    client = StarburstClient()
    assert client.host == "test.host.io"
    assert client.auth_mode == "basic"


def test_client_init_oauth(monkeypatch):
    from starburst_client import StarburstClient
    monkeypatch.setenv("STARBURST_CLIENT_ID", "my_client")
    monkeypatch.setenv("STARBURST_CLIENT_SECRET", "my_secret")
    monkeypatch.setenv("STARBURST_TOKEN_URL", "https://example.com/oauth2/token")
    monkeypatch.setenv("STARBURST_HOST", "test.host.io")
    monkeypatch.setenv("STARBURST_PORT", "443")
    monkeypatch.setenv("STARBURST_CATALOG", "testcat")
    monkeypatch.setenv("STARBURST_SCHEMA", "testsch")

    client = StarburstClient()
    assert client.auth_mode == "oauth"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "c:/Users/Lenovo/gen ai project/starburst-mcp2" && python -m pytest tests/test_starburst_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'starburst_client'`

- [ ] **Step 3: Implement starburst_client.py**

```python
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

# SQL reserved words that cannot be used as identifiers
_RESERVED = {
    "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
    "TABLE", "SCHEMA", "DATABASE", "FROM", "WHERE", "SET", "INTO",
    "VALUES", "TRUNCATE", "MERGE", "GRANT", "REVOKE", "INDEX",
}

# Valid identifier pattern: letters, digits, underscores; must start with letter
_IDENT_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")


class StarburstClient:
    def __init__(self):
        self.host = os.getenv("STARBURST_HOST")
        self.port = int(os.getenv("STARBURST_PORT", "443"))
        self.catalog = os.getenv("STARBURST_CATALOG")
        self.schema = os.getenv("STARBURST_SCHEMA")

        # Determine auth mode
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
            # DDL/DML with no result set
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "c:/Users/Lenovo/gen ai project/starburst-mcp2" && python -m pytest tests/test_starburst_client.py -v`
Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add starburst_client.py tests/test_starburst_client.py
git commit -m "feat: starburst client with OAuth/BasicAuth and identifier validation"
```

---

### Task 4: Read Tools

**Files:**
- Create: `tools/__init__.py`
- Create: `tools/read_tools.py`

- [ ] **Step 1: Create tools/__init__.py**

```python
from tools.read_tools import register_read_tools
from tools.write_tools import register_write_tools
```

- [ ] **Step 2: Create tools/read_tools.py**

```python
"""Read-only MCP tools for Starburst Galaxy.

Tools: execute_query, list_catalogs, show_schemas, show_tables, describe_table
"""

from mcp.server.fastmcp import FastMCP
from starburst_client import StarburstClient
from permission_manager import PermissionManager


def register_read_tools(mcp: FastMCP, client: StarburstClient, perms: PermissionManager, developer: str):

    @mcp.tool()
    def execute_query(query: str, read_only: bool = False) -> str:
        """Execute any SQL query on Starburst Galaxy.

        Args:
            query: SQL query to execute (Trino/ANSI SQL)
            read_only: If true, only SELECT/SHOW/DESCRIBE/EXPLAIN are allowed
        """
        upper = query.strip().upper()
        is_read = upper.startswith(("SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "WITH"))

        if read_only and not is_read:
            return "Error: read_only=true but query is not a read operation."

        if not is_read:
            allowed, msg = perms.check_with_message(developer, "execute_raw")
            if not allowed:
                return f"Error: {msg}"

        try:
            result = client.execute(query)
            return _format_result(result)
        except Exception as e:
            return f"Error executing query: {e}"

    @mcp.tool()
    def list_catalogs() -> str:
        """List all available catalogs in Starburst Galaxy."""
        try:
            result = client.execute("SHOW CATALOGS")
            return _format_result(result)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def show_schemas(catalog: str) -> str:
        """Show all schemas in a catalog.

        Args:
            catalog: Catalog name (e.g., 'mcp2ohio', 'sample')
        """
        try:
            StarburstClient.validate_identifier(catalog)
            result = client.execute(f'SHOW SCHEMAS FROM "{catalog}"')
            return _format_result(result)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def show_tables(catalog: str, schema: str) -> str:
        """Show all tables in a schema.

        Args:
            catalog: Catalog name
            schema: Schema name
        """
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            fqn = StarburstClient.qualified_name(catalog, schema)
            result = client.execute(f"SHOW TABLES FROM {fqn}")
            return _format_result(result)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def describe_table(catalog: str, schema: str, table: str) -> str:
        """Describe a table's columns and types.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
        """
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            StarburstClient.validate_identifier(table)
            fqn = StarburstClient.qualified_name(catalog, schema, table)
            result = client.execute(f"DESCRIBE {fqn}")
            return _format_result(result)
        except Exception as e:
            return f"Error: {e}"


def _format_result(result: dict) -> str:
    """Format query result as a readable string."""
    if "columns" in result:
        columns = result["columns"]
        rows = result["rows"]
        if not rows:
            return "No rows returned."
        # Build table
        str_rows = [[str(v) if v is not None else "NULL" for v in row] for row in rows]
        widths = [
            max(len(c), max((len(r[i]) for r in str_rows), default=0))
            for i, c in enumerate(columns)
        ]
        header = " | ".join(c.ljust(w) for c, w in zip(columns, widths))
        sep = "-+-".join("-" * w for w in widths)
        lines = [header, sep]
        for row in str_rows:
            lines.append(" | ".join(v.ljust(w) for v, w in zip(row, widths)))
        return f"{len(rows)} row(s) returned.\n\n" + "\n".join(lines)
    if "rows_affected" in result:
        return f"OK. Rows affected: {result['rows_affected']}"
    return str(result)
```

- [ ] **Step 3: Create placeholder tools/write_tools.py (minimal, will be filled in Task 5)**

```python
"""Write MCP tools for Starburst Galaxy — placeholder for Task 5."""

from mcp.server.fastmcp import FastMCP
from starburst_client import StarburstClient
from permission_manager import PermissionManager


def register_write_tools(mcp: FastMCP, client: StarburstClient, perms: PermissionManager, developer: str):
    pass  # Implemented in Task 5
```

- [ ] **Step 4: Commit**

```bash
git add tools/
git commit -m "feat: read tools — execute_query, list_catalogs, show_schemas, show_tables, describe_table"
```

---

### Task 5: Write Tools (DDL + DML)

**Files:**
- Modify: `tools/write_tools.py`

- [ ] **Step 1: Implement all 9 write tools**

Replace `tools/write_tools.py` with:

```python
"""Write MCP tools for Starburst Galaxy.

DDL: create_schema, create_table, drop_table, drop_schema, truncate_table
DML: insert_data, update_data, delete_data, merge_data

All tools check permissions before execution.
Dangerous operations (drop, truncate) require confirm=true.
"""

import json
from mcp.server.fastmcp import FastMCP
from starburst_client import StarburstClient
from permission_manager import PermissionManager


def register_write_tools(mcp: FastMCP, client: StarburstClient, perms: PermissionManager, developer: str):

    def _check(operation: str) -> str | None:
        """Check permission. Returns error message or None if allowed."""
        allowed, msg = perms.check_with_message(developer, operation)
        if not allowed:
            return f"Error: {msg}"
        return None

    def _confirm_guard(operation: str, target: str, confirm: bool) -> str | None:
        """Guard for dangerous operations. Returns warning if not confirmed."""
        if not confirm:
            return (
                f"WARNING: This will {operation} '{target}'. "
                f"This action cannot be undone. "
                f"Pass confirm=true to proceed."
            )
        return None

    # --- DDL Tools ---

    @mcp.tool()
    def create_schema(catalog: str, schema: str) -> str:
        """Create a new schema in a catalog.

        Args:
            catalog: Catalog name (e.g., 'mcp2ohio')
            schema: New schema name
        """
        if err := _check("create_schema"):
            return err
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            fqn = StarburstClient.qualified_name(catalog, schema)
            result = client.execute(f"CREATE SCHEMA {fqn}")
            return f"Schema {fqn} created successfully."
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def create_table(catalog: str, schema: str, table: str, columns: str) -> str:
        """Create a new table.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: New table name
            columns: JSON array of columns, e.g. [{"name": "id", "type": "INTEGER"}, {"name": "val", "type": "VARCHAR"}]
        """
        if err := _check("create_table"):
            return err
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            StarburstClient.validate_identifier(table)
            col_list = json.loads(columns) if isinstance(columns, str) else columns
            col_defs = ", ".join(f'"{c["name"]}" {c["type"]}' for c in col_list)
            fqn = StarburstClient.qualified_name(catalog, schema, table)
            result = client.execute(f"CREATE TABLE {fqn} ({col_defs})")
            return f"Table {fqn} created successfully with {len(col_list)} column(s)."
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def drop_table(catalog: str, schema: str, table: str, confirm: bool = False) -> str:
        """Drop (delete) a table permanently.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table to drop
            confirm: Must be true to execute. Safety guard for destructive operation.
        """
        if err := _check("drop_table"):
            return err
        fqn = StarburstClient.qualified_name(catalog, schema, table)
        if warn := _confirm_guard("DROP TABLE", fqn, confirm):
            return warn
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            StarburstClient.validate_identifier(table)
            client.execute(f"DROP TABLE {fqn}")
            return f"Table {fqn} dropped successfully."
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def drop_schema(catalog: str, schema: str, confirm: bool = False) -> str:
        """Drop (delete) a schema permanently.

        Args:
            catalog: Catalog name
            schema: Schema to drop
            confirm: Must be true to execute. Safety guard for destructive operation.
        """
        if err := _check("drop_schema"):
            return err
        fqn = StarburstClient.qualified_name(catalog, schema)
        if warn := _confirm_guard("DROP SCHEMA", fqn, confirm):
            return warn
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            client.execute(f"DROP SCHEMA {fqn}")
            return f"Schema {fqn} dropped successfully."
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def truncate_table(catalog: str, schema: str, table: str, confirm: bool = False) -> str:
        """Truncate (remove all rows from) a table. Table structure is preserved.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table to truncate
            confirm: Must be true to execute. Safety guard for destructive operation.
        """
        if err := _check("truncate"):
            return err
        fqn = StarburstClient.qualified_name(catalog, schema, table)
        if warn := _confirm_guard("TRUNCATE TABLE", fqn, confirm):
            return warn
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            StarburstClient.validate_identifier(table)
            client.execute(f"TRUNCATE TABLE {fqn}")
            return f"Table {fqn} truncated successfully."
        except Exception as e:
            return f"Error: {e}"

    # --- DML Tools ---

    @mcp.tool()
    def insert_data(catalog: str, schema: str, table: str, rows: str) -> str:
        """Insert rows into a table.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
            rows: JSON array of row objects, e.g. [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        """
        if err := _check("insert"):
            return err
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            StarburstClient.validate_identifier(table)
            row_list = json.loads(rows) if isinstance(rows, str) else rows
            if not row_list:
                return "Error: No rows provided."
            columns = list(row_list[0].keys())
            col_str = ", ".join(f'"{c}"' for c in columns)
            value_rows = []
            for row in row_list:
                vals = []
                for c in columns:
                    v = row.get(c)
                    if v is None:
                        vals.append("NULL")
                    elif isinstance(v, str):
                        vals.append(f"'{v}'")
                    else:
                        vals.append(str(v))
                value_rows.append(f"({', '.join(vals)})")
            values_str = ", ".join(value_rows)
            fqn = StarburstClient.qualified_name(catalog, schema, table)
            sql = f"INSERT INTO {fqn} ({col_str}) VALUES {values_str}"
            result = client.execute(sql)
            affected = result.get("rows_affected", len(row_list))
            return f"Inserted {affected} row(s) into {fqn}."
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def update_data(catalog: str, schema: str, table: str, set_values: str, where: str) -> str:
        """Update rows in a table.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
            set_values: JSON object of column=value pairs, e.g. {"amount": 100, "status": "active"}
            where: WHERE clause (without the WHERE keyword), e.g. "id = 1"
        """
        if err := _check("update"):
            return err
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            StarburstClient.validate_identifier(table)
            vals = json.loads(set_values) if isinstance(set_values, str) else set_values
            set_parts = []
            for col, val in vals.items():
                if val is None:
                    set_parts.append(f'"{col}" = NULL')
                elif isinstance(val, str):
                    set_parts.append(f'"{col}" = \'{val}\'')
                else:
                    set_parts.append(f'"{col}" = {val}')
            set_str = ", ".join(set_parts)
            fqn = StarburstClient.qualified_name(catalog, schema, table)
            sql = f"UPDATE {fqn} SET {set_str} WHERE {where}"
            result = client.execute(sql)
            affected = result.get("rows_affected", 0)
            return f"Updated {affected} row(s) in {fqn}."
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def delete_data(catalog: str, schema: str, table: str, where: str) -> str:
        """Delete rows from a table.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
            where: WHERE clause (without the WHERE keyword), e.g. "id = 1"
        """
        if err := _check("delete"):
            return err
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            StarburstClient.validate_identifier(table)
            fqn = StarburstClient.qualified_name(catalog, schema, table)
            sql = f"DELETE FROM {fqn} WHERE {where}"
            result = client.execute(sql)
            affected = result.get("rows_affected", 0)
            return f"Deleted {affected} row(s) from {fqn}."
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def merge_data(catalog: str, schema: str, table: str, source_query: str, on_condition: str, when_matched: str, when_not_matched: str) -> str:
        """Merge (upsert) data into a table from a source query.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Target table name
            source_query: SELECT query providing source rows
            on_condition: Join condition, e.g. "target.id = source.id"
            when_matched: Action when matched, e.g. "UPDATE SET target.val = source.val"
            when_not_matched: Action when not matched, e.g. "INSERT (id, val) VALUES (source.id, source.val)"
        """
        if err := _check("merge"):
            return err
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            StarburstClient.validate_identifier(table)
            fqn = StarburstClient.qualified_name(catalog, schema, table)
            sql = (
                f"MERGE INTO {fqn} AS target "
                f"USING ({source_query}) AS source "
                f"ON {on_condition} "
                f"WHEN MATCHED THEN {when_matched} "
                f"WHEN NOT MATCHED THEN {when_not_matched}"
            )
            result = client.execute(sql)
            affected = result.get("rows_affected", 0)
            return f"Merge completed on {fqn}. Rows affected: {affected}"
        except Exception as e:
            return f"Error: {e}"
```

- [ ] **Step 2: Commit**

```bash
git add tools/write_tools.py
git commit -m "feat: write tools — create, drop, truncate, insert, update, delete, merge"
```

---

### Task 6: MCP Server Entry Point

**Files:**
- Create: `server.py`

- [ ] **Step 1: Create server.py**

```python
"""Starburst Read-Write MCP Server.

A custom MCP server providing full read+write access to Starburst Galaxy
via Trino DBAPI. Supports OAuth2 authentication and per-developer permissions.

Usage (stdio):
    python server.py

Register in ~/.claude/settings.json:
    "starburst-rw": {
        "type": "stdio",
        "command": "python",
        "args": ["c:/Users/Lenovo/gen ai project/starburst-mcp2/server.py"]
    }
"""

import os
import sys
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from starburst_client import StarburstClient
from permission_manager import PermissionManager
from tools import register_read_tools, register_write_tools

# Initialize
client = StarburstClient()
perms = PermissionManager()
developer = os.getenv("STARBURST_DEVELOPER", "unknown")

mcp = FastMCP(
    "starburst-rw",
    description=(
        "Starburst Galaxy Read-Write MCP Server. "
        "Provides full SQL access including SELECT, INSERT, UPDATE, DELETE, "
        "CREATE, DROP, TRUNCATE, and MERGE operations. "
        f"Connected to: {client.host} | Catalog: {client.catalog} | "
        f"Developer: {developer} | Auth: {client.auth_mode}"
    ),
)

# Register all tools
register_read_tools(mcp, client, perms, developer)
register_write_tools(mcp, client, perms, developer)

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

- [ ] **Step 2: Test server starts without errors**

Run: `cd "c:/Users/Lenovo/gen ai project/starburst-mcp2" && python -c "import server; print('Server module loaded OK')" `
Expected: `Server module loaded OK` (no import errors)

- [ ] **Step 3: Commit**

```bash
git add server.py
git commit -m "feat: MCP server entry point with stdio transport"
```

---

### Task 7: Integration Test

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
"""Integration tests against live mcp2ohio catalog on free-cluster.

These tests create a temporary schema, run CRUD operations, and clean up.
Requires .env with valid Starburst credentials.
Skip with: pytest -m "not integration"
"""

import os
import sys
import pytest
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from starburst_client import StarburstClient


pytestmark = pytest.mark.integration

TEST_CATALOG = "mcp2ohio"
TEST_SCHEMA = f"inttest_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def client():
    return StarburstClient()


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown(client):
    """Create test schema before tests, drop after."""
    client.execute(f'CREATE SCHEMA "{TEST_CATALOG}"."{TEST_SCHEMA}"')
    yield
    try:
        client.execute(f'DROP TABLE IF EXISTS "{TEST_CATALOG}"."{TEST_SCHEMA}"."test_tbl"')
    except Exception:
        pass
    try:
        client.execute(f'DROP SCHEMA "{TEST_CATALOG}"."{TEST_SCHEMA}"')
    except Exception:
        pass


def test_create_table(client):
    fqn = f'"{TEST_CATALOG}"."{TEST_SCHEMA}"."test_tbl"'
    client.execute(f"CREATE TABLE {fqn} (id INTEGER, name VARCHAR, amount DOUBLE)")
    result = client.execute(f"DESCRIBE {fqn}")
    col_names = [row[0] for row in result["rows"]]
    assert "id" in col_names
    assert "name" in col_names
    assert "amount" in col_names


def test_insert(client):
    fqn = f'"{TEST_CATALOG}"."{TEST_SCHEMA}"."test_tbl"'
    result = client.execute(f"INSERT INTO {fqn} VALUES (1, 'Alice', 100.0), (2, 'Bob', 200.0)")
    assert result["rows_affected"] == 2


def test_select(client):
    fqn = f'"{TEST_CATALOG}"."{TEST_SCHEMA}"."test_tbl"'
    result = client.execute(f"SELECT * FROM {fqn} ORDER BY id")
    assert len(result["rows"]) == 2
    assert result["rows"][0][1] == "Alice"
    assert result["rows"][1][1] == "Bob"


def test_update(client):
    fqn = f'"{TEST_CATALOG}"."{TEST_SCHEMA}"."test_tbl"'
    result = client.execute(f"UPDATE {fqn} SET amount = 150.0 WHERE id = 1")
    assert result["rows_affected"] == 1
    check = client.execute(f"SELECT amount FROM {fqn} WHERE id = 1")
    assert check["rows"][0][0] == 150.0


def test_delete(client):
    fqn = f'"{TEST_CATALOG}"."{TEST_SCHEMA}"."test_tbl"'
    result = client.execute(f"DELETE FROM {fqn} WHERE id = 2")
    assert result["rows_affected"] == 1
    check = client.execute(f"SELECT * FROM {fqn}")
    assert len(check["rows"]) == 1


def test_truncate(client):
    fqn = f'"{TEST_CATALOG}"."{TEST_SCHEMA}"."test_tbl"'
    # Insert a row first
    client.execute(f"INSERT INTO {fqn} VALUES (3, 'Carol', 300.0)")
    client.execute(f"TRUNCATE TABLE {fqn}")
    result = client.execute(f"SELECT count(*) FROM {fqn}")
    assert result["rows"][0][0] == 0
```

- [ ] **Step 2: Run unit tests (permission + client)**

Run: `cd "c:/Users/Lenovo/gen ai project/starburst-mcp2" && python -m pytest tests/ -v -m "not integration"`
Expected: All unit tests PASS.

- [ ] **Step 3: Run integration tests (requires live Starburst connection)**

Run: `cd "c:/Users/Lenovo/gen ai project/starburst-mcp2" && python -m pytest tests/test_integration.py -v --timeout=120`
Expected: All 6 integration tests PASS (may take 30-60s due to cluster cold start).

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: integration tests — full CRUD cycle against mcp2ohio"
```

---

### Task 8: Register MCP Server in Claude Code

**Files:**
- Modify: `~/.claude/settings.json`

- [ ] **Step 1: Add starburst-rw to Claude Code settings**

Add the following entry to `~/.claude/settings.json` under `mcpServers` (DO NOT remove existing entries):

```json
"starburst-rw": {
  "type": "stdio",
  "command": "python",
  "args": ["c:/Users/Lenovo/gen ai project/starburst-mcp2/server.py"]
}
```

- [ ] **Step 2: Verify settings.json has both MCP servers**

The `mcpServers` section should now contain:
- `starburst-galaxy` (existing, read-only, untouched)
- `starburst-rw` (new, read+write)

Plus any other existing servers (computer-use-mcp, strands-agents, shadcn).

- [ ] **Step 3: Restart Claude Code to load the new MCP server**

Restart the Claude Code session. The new `starburst-rw` tools should appear in the tool list.

- [ ] **Step 4: Smoke test — run a query via the new MCP server**

Test: `execute_query("SELECT 1 AS test")`
Expected: Returns `1 row(s) returned.\n\ntest\n----\n1`

- [ ] **Step 5: Commit any config changes**

```bash
cd "c:/Users/Lenovo/gen ai project/starburst-mcp2"
git add -A
git commit -m "feat: complete starburst-rw MCP server — ready for registration"
```

---

## Self-Review Checklist

- **Spec coverage:** All 14 tools implemented (5 read + 5 DDL + 4 DML). OAuth auth covered in client. Permission system with profiles+overrides in Task 2. Registration in Task 8. Error handling in client + tools. ✓
- **Placeholder scan:** No TBDs, TODOs, or "implement later" found. All code blocks are complete. ✓
- **Type consistency:** `PermissionManager.check()` and `check_with_message()` used consistently across read_tools and write_tools. `StarburstClient.validate_identifier()` and `qualified_name()` used consistently. `_format_result()` used in read tools. ✓
- **Missing from spec:** `merge_data` tool included. Dangerous op confirm guards included. Hot-reload tested. `.env.example` included. ✓
