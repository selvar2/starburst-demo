# Enterprise Technical Documentation
## Starburst MCP Server — Cross-Platform Setup, OAuth Fix & Full CRUD Validation
### Session Date: 2026-04-08 | Branch: `dev1` | Author: AI Pair Programmer (Claude Opus 4.6)

---

## Overview

This session addressed three critical engineering objectives for the Starburst Galaxy Read-Write MCP (Model Context Protocol) Server:

1. **Cross-platform MCP configuration** — Replacing hardcoded Windows paths with portable `python3` + relative path references, enabling seamless operation in GitHub Codespaces (Linux) and local environments.
2. **DevContainer lifecycle automation** — Implementing idempotent pre-build and post-start scripts that guarantee fresh dependency installation, environment auto-detection, and MCP server health validation on every container create/restart.
3. **OAuth browser popup elimination** — Diagnosing and resolving a blocking issue where Starburst Galaxy's interactive OAuth consent screen appeared on every MCP tool invocation, making demos unusable.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Claude Code / MCP Client                                     │
│  (stdio transport)                                            │
│                                                               │
│  mcp.json ──► python3 ./gen ai project/.../server.py          │
└──────────────┬───────────────────────────────────────────────┘
               │ JSON-RPC 2.0 over stdin/stdout
               ▼
┌──────────────────────────────────────────────────────────────┐
│  server.py (FastMCP)                                          │
│  ├── 5 Read Tools (list_catalogs, show_schemas, show_tables,  │
│  │                  describe_table, execute_query)             │
│  └── 9 Write Tools (create_schema, create_table, drop_table,  │
│                      drop_schema, truncate_table, insert_data, │
│                      update_data, delete_data, merge_data)     │
└──────────────┬───────────────────────────────────────────────┘
               │ Trino DBAPI (HTTPS:443)
               │ BasicAuth (STARBURST_USER/STARBURST_PASSWORD)
               ▼
┌──────────────────────────────────────────────────────────────┐
│  Starburst Galaxy                                             │
│  Host: datateam-free-cluster.trino.galaxy.starburst.io        │
│  Catalog: mcp2ohio │ Schema: test_writes                      │
│  Developer: prakashrajr666                                    │
└──────────────────────────────────────────────────────────────┘
```

---

## Environment Setup

### Pre-existing State
- **Repository:** `selvar2/starburst-demo`
- **Branch:** `dev1` (starting commit: `823db78`)
- **Runtime:** GitHub Codespaces, Python 3.12.1
- **Prior config:** Windows-only `mcp.json` with hardcoded `C:\Users\Lenovo\...` paths

### Files Created / Modified

| File | Action | Purpose |
|------|--------|---------|
| `mcp.json` | Created | Cross-platform MCP server registration |
| `.devcontainer/devcontainer.json` | Created | Container lifecycle configuration |
| `.devcontainer/setup.sh` | Created → Updated | Post-create: fresh dep install + validation |
| `.devcontainer/start.sh` | Created → Updated | Post-start: env detection + health check |
| `gen ai project/starburst-mcp2/.env` | Created | Starburst Galaxy credentials (gitignored) |
| `gen ai project/starburst-mcp2/starburst_client.py` | Modified | BasicAuth + connection reuse |
| `gen ai project/starburst-mcp2/.gitignore` | Modified | Added `.oauth_token_cache.json` |
| `gen ai project/starburst-mcp2/requirements.txt` | Modified | Added `requests>=2.31.0` |

---

## Implementation Steps

### Step 1: Cross-Platform MCP Configuration

**Problem:** Original `mcp.json` used hardcoded Windows paths:
```json
{
  "mcpServers": {
    "starburst-rw": {
      "command": "C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
      "args": ["C:\\Users\\Lenovo\\gen ai project\\starburst-mcp2\\server.py"]
    }
  }
}
```

**Solution:**
```json
{
  "mcpServers": {
    "starburst-rw": {
      "command": "python3",
      "args": ["./gen ai project/starburst-mcp2/server.py"]
    }
  }
}
```

**Rationale:** `python3` resolves via `$PATH` on Linux/macOS/Codespaces. Relative path anchors to the workspace root where Claude Code invokes the server.

### Step 2: DevContainer Lifecycle Automation

**`devcontainer.json`** — Key configuration:
```json
{
  "image": "mcr.microsoft.com/devcontainers/python:3.13",
  "postCreateCommand": "bash .devcontainer/setup.sh",
  "postStartCommand": "bash .devcontainer/start.sh",
  "remoteEnv": {
    "PYTHONUNBUFFERED": "1",
    "PIP_NO_CACHE_DIR": "1"
  }
}
```

**`setup.sh` (postCreateCommand)** — Runs once after container build:
1. Auto-detects Python (`python3` → `python` fallback)
2. Force-reinstalls pip: `pip install --upgrade pip --force-reinstall`
3. Force-reinstalls all deps: `pip install --force-reinstall -r requirements.txt`
4. Verifies core imports: `trino`, `mcp`, `dotenv`, `yaml`
5. Validates `server.py` module loading
6. Checks `.env` existence

**`start.sh` (postStartCommand)** — Runs on every container start:
1. Detects environment via `$CODESPACES` / `$REMOTE_CONTAINERS` env vars
2. Verifies deps are installed (auto-reinstalls if missing)
3. Parses `.env` safely using `grep` + `cut` (no `source` — avoids shell expansion of `$` in passwords)
4. Displays connection info (host, port, catalog, auth mode)
5. Runs MCP initialize handshake health check

**Bug found and fixed:** Original `start.sh` used `source <(grep ... .env)` which caused `$ChangeMe` in `GXY$ChangeMe` password to be interpreted as a shell variable, triggering `unbound variable` error. Fixed by switching to `grep`/`cut` based parsing.

### Step 3: OAuth Browser Popup Investigation & Resolution

**Problem:** Every MCP tool call triggered a Starburst Galaxy OAuth consent screen ("Third party application access") requiring manual browser interaction. This made demos impossible.

**Root Cause Analysis:**

1. `starburst_client.py` line 45 used `OAuth2Authentication()` from `trino.auth`
2. This class uses an **interactive browser-based OAuth flow** driven by Trino's server
3. The `.env` had `STARBURST_CLIENT_ID`, `STARBURST_CLIENT_SECRET`, `STARBURST_TOKEN_URL` — but these were **read and never passed** to the auth object
4. `get_connection()` was called on **every query** (no connection reuse), triggering re-authentication each time

**Investigation — Trino OAuth2Authentication internals** (`trino/auth.py`):

| Class | Purpose | Browser Required? |
|-------|---------|------------------|
| `OAuth2Authentication` | Interactive browser flow, Trino-server-driven | Yes |
| `JWTAuthentication` | Pass pre-fetched Bearer token | No |
| `BasicAuthentication` | Username/password | No |

**Attempted Fix 1 — Client Credentials Grant:**
```python
# Attempted: POST to STARBURST_TOKEN_URL with client_credentials
resp = requests.post(token_url, data={
    "grant_type": "client_credentials",
    "client_id": "...", "client_secret": "..."
})
# Result: 405 Method Not Allowed
```

**Finding:** Starburst Galaxy's `/oauth2/token` endpoint is the Galaxy UI consent page, not a standard RFC 6749 token endpoint. It does not support `client_credentials` or any programmatic grant type.

**Final Fix — BasicAuth with Connection Reuse:**

```python
# Before (popup on every query):
def _get_auth(self):
    if self.auth_mode == "oauth":
        return OAuth2Authentication()  # ← opens browser each time
    return BasicAuthentication(self.user, self.password)

def get_connection(self):
    return connect(...)  # ← new connection per query

# After (zero popups, connection reused):
def _get_auth(self):
    return BasicAuthentication(self.user, self.password)

def get_connection(self):
    if self._conn is not None:
        try:
            cur = self._conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchall()
            return self._conn
        except Exception:
            self._conn = None
    self._conn = connect(...)
    return self._conn
```

---

## Execution Logs

### MCP Initialize Handshake
```json
{
  "serverInfo": {
    "name": "starburst-rw",
    "version": "1.27.0"
  },
  "instructions": "Connected to: datateam-free-cluster.trino.galaxy.starburst.io | Catalog: mcp2ohio | Developer: prakashrajr666 | Auth: basic"
}
```

### Full CRUD Test Results

| Operation | Tool | Input | Result |
|-----------|------|-------|--------|
| List Catalogs | `list_catalogs` | `{}` | 7 catalogs: galaxy, mcp2ohio, sample, starburst, system, tpcds, tpch |
| Show Schemas | `show_schemas` | `{"catalog":"mcp2ohio"}` | 3 schemas: information_schema, system, test_writes |
| Show Tables | `show_tables` | `{"catalog":"mcp2ohio","schema":"test_writes"}` | 1 table: demo |
| Describe Table | `describe_table` | `{"catalog":"mcp2ohio","schema":"test_writes","table":"demo"}` | id (integer), name (varchar), amount (double) |
| SELECT | `execute_query` | `SELECT * FROM ... ORDER BY id` | 1 row: (1, hello, 150.0) |
| INSERT | `insert_data` | `{"rows":"[{\"id\":99,...}]"}` | Inserted 1 row |
| Verify INSERT | `execute_query` | `SELECT *` | 2 rows: (1, hello, 150.0), (99, mcp_test, 42.5) |
| UPDATE | `update_data` | `set: name=mcp_updated, where: id=99` | Updated 1 row |
| DELETE | `delete_data` | `where: id=99` | Deleted 1 row |
| Verify cleanup | `execute_query` | `SELECT *` | 1 row: original state restored |
| INSERT (user request) | `insert_data` | `{"id":2,"name":"test2","amount":200}` | Inserted 1 row — persisted |

### Post-Fix Multi-Query Test (4 queries, zero popups)
```
id=1: init ok
id=3: 7 row(s) returned — list_catalogs
id=4: 3 row(s) returned — show_schemas
id=5: 1 row(s) returned — show_tables
id=6: 2 row(s) returned — SELECT *
```

---

## Errors & Resolutions

| Error | Cause | Resolution |
|-------|-------|------------|
| `unbound variable` in `start.sh` | `source .env` expanded `$ChangeMe` in password `GXY$ChangeMe` | Replaced `source` with `grep`/`cut` parsing |
| `405 Method Not Allowed` on `/oauth2/token` | Starburst Galaxy endpoint is UI consent page, not RFC 6749 token endpoint | Abandoned `client_credentials` approach |
| OAuth popup on every query | `OAuth2Authentication()` uses interactive browser flow; new connection per query | Switched to BasicAuth + connection reuse |

---

## Alternatives Considered

| Approach | Verdict | Reason |
|----------|---------|--------|
| Client Credentials OAuth Grant | Rejected | Galaxy's token endpoint doesn't support it (HTTP 405) |
| OAuth + disk-cached token via `JWTAuthentication` | Rejected | No standard token endpoint to call; Trino server drives the flow |
| Install `keyring` for trino's built-in token cache | Rejected | Still requires initial browser consent; unsuitable for headless MCP |
| BasicAuth with connection reuse | **Selected** | Zero popups, uses existing credentials, connection reused across queries |

---

## Performance Notes

- **Connection reuse** eliminates the overhead of TCP/TLS handshake + authentication on every query. A `SELECT 1` liveness check runs before reusing a cached connection.
- **`PIP_NO_CACHE_DIR=1`** ensures clean builds at the cost of slightly longer `postCreateCommand` execution (~15s extra).
- **`--force-reinstall`** in `setup.sh` guarantees no stale packages survive container rebuilds.

---

## Security Considerations

- `.env` file containing credentials is in `.gitignore` — never committed to the repository
- `.oauth_token_cache.json` is in `.gitignore` as a precaution
- BasicAuth credentials are transmitted over HTTPS (port 443) — encrypted in transit
- `validate_identifier()` prevents SQL injection in catalog/schema/table names
- All DML tools use parameterized-style operations through the Trino client

---

## Git History

| Commit | Message |
|--------|---------|
| `80674b1` | `feat: add cross-platform MCP config and devcontainer setup` |
| `b03c37e` | `fix: robust devcontainer scripts with fresh installs and auto-detection` |
| `8652f3d` | `fix: switch to BasicAuth with connection reuse — no browser popup` |

---

## Conclusion

This session transformed the MCP server from a Windows-only, popup-riddled development setup into a fully portable, demo-ready system. The server now operates headlessly with BasicAuth, reuses connections for performance, auto-installs dependencies on container lifecycle events, and has been validated with a complete CRUD test cycle against live Starburst Galaxy infrastructure. All changes are pushed to `dev1`.
