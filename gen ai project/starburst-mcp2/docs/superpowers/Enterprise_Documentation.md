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

---
---

# Version 2: StarQuery AI — Chatbot Web UI, JWT Auth & Data Visualization
## Session Date: 2026-04-14/15 | Branch: `dev3` | Author: AI Pair Programmer (Claude Opus 4.6)

---

## Overview

This session built a complete **chatbot-driven web application** (StarQuery AI) on top of the Starburst MCP server, adding:

1. **Natural Language to SQL Translation** — Regex-based NL→SQL engine with dynamic catalog/schema context parsing
2. **Interactive Web UI** — Single-page application with dark/light mode, schema browser, Chart.js visualizations, and multi-format exports
3. **Headless JWT Authentication** — Programmatic OAuth2 flow that eliminates browser popups entirely
4. **Token Caching** — Persistent token storage to disk with auto-refresh
5. **Performance Optimization** — Parallel schema fetching via ThreadPoolExecutor, in-memory schema cache with TTL
6. **Cluster Keepalive** — Background process pinging Starburst every 60 seconds with log rotation

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    StarQuery AI — Frontend                   │
│  ┌──────────┐  ┌────────────────────┐  ┌─────────────────┐  │
│  │ Sidebar  │  │   Chat Interface   │  │ Chart Config    │  │
│  │ Schema   │  │ Messages + Tables  │  │ Type/Axis/Color │  │
│  │ Browser  │  │ Charts + Exports   │  │ Panel           │  │
│  └──────────┘  └────────────────────┘  └─────────────────┘  │
│  index.html (Tailwind + Chart.js + SheetJS + html2canvas)   │
└─────────────────────┬───────────────────────────────────────┘
                      │ fetch() REST API
              ┌───────▼───────┐
              │  FastAPI       │
              │  app_jwt.py    │
              │  ┌───────────┐ │
              │  │ NL→SQL    │ │  Regex patterns + raw SQL passthrough
              │  │ Translator│ │  Dynamic catalog/schema context parsing
              │  └───────────┘ │
              │  ┌───────────┐ │
              │  │ Schema    │ │  5-min TTL cache + parallel fetch
              │  │ Cache     │ │  ThreadPoolExecutor (10 workers)
              │  └───────────┘ │
              │  ┌───────────┐ │
              │  │ Export    │ │  CSV, XLSX (openpyxl), HTML
              │  │ Engine    │ │
              │  └───────────┘ │
              └───────┬───────┘
                      │ StarburstClientJWT
                      │ (headless OAuth2 — no browser)
              ┌───────▼───────┐
              │  Starburst     │
              │  Galaxy        │
              │  mcp2ohio      │
              │  (Iceberg/S3)  │
              └───────────────┘
```

---

## Environment Setup

### Prerequisites

```bash
pip install fastapi uvicorn[standard] openpyxl python-multipart trino python-dotenv pyyaml requests
```

### .env Configuration

```env
STARBURST_HOST=datateam-free-cluster.trino.galaxy.starburst.io
STARBURST_PORT=443
STARBURST_CATALOG=mcp2ohio
STARBURST_SCHEMA=test_writes
STARBURST_USER=your_email@company.com/accountadmin
STARBURST_PASSWORD=your_password
STARBURST_CLIENT_ID=service_name@domain.galaxy.starburst.io
STARBURST_CLIENT_SECRET=GXY$your_secret_here
```

### File Structure

```
gen ai project/starburst-mcp2/
├── app.py                      # FastAPI server (original OAuth client)
├── app_jwt.py                  # FastAPI server (JWT headless auth)
├── index.html                  # StarQuery AI frontend (single-page app)
├── starburst_client.py         # Original client (browser OAuth popup)
├── starburst_client_jwt.py     # JWT client (headless, no browser)
├── token_cache.py              # Token persistence to disk
├── keepalive.py                # Cluster keepalive (every 60s)
├── keepalive.log               # Keepalive log (auto-trimmed to 10 entries)
├── token_cache.json            # Cached token (auto-created)
├── STARBURST-AUTH.md           # Auth reference for AI agents
├── server.py                   # MCP server entry point (unchanged)
├── permission_manager.py       # Permission system (unchanged)
├── permissions.yaml            # Permission config (unchanged)
├── .env                        # Credentials (never committed)
├── backups/                    # Timestamped backups
│   ├── app_backup_20260415_070104.py
│   ├── app_jwt_backup_20260415_070104.py
│   └── app_backup_20260415_072525.py
└── docs/superpowers/
    ├── Enterprise_Documentation.md
    └── End_User_Documentation.md
```

---

## Implementation Steps

### 1. FastAPI Backend (`app.py` / `app_jwt.py`)

#### API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/` | Serve `index.html` |
| `GET` | `/api/schema?refresh=0\|1` | Schema browser data (cached, parallel fetch) |
| `POST` | `/api/query` | Execute raw SQL |
| `POST` | `/api/chat` | NL→SQL translation + execution |
| `POST` | `/api/export/{csv\|xlsx\|html}` | Export data as file download |

#### NL→SQL Translation Engine

The `_nl_to_sql()` function processes natural language in this order:

1. **Exact matches** — `show all tables`, `show schemas` → direct SQL
2. **Raw SQL passthrough** — if input starts with SQL keyword + contains dots → execute as-is
3. **Regex NL patterns** — `describe X`, `show all data from X`, `count rows in X`, `top N col from X`, `sum/avg/min/max of col from X`, `group by col from X`
4. **Fallback raw SQL** — any remaining SQL keyword input → passthrough
5. **No match** → return help message with examples

#### Dynamic Context Parsing

The `_extract_context()` function parses catalog/schema from NL input:

```python
# Input: "show all data from iceberg_tables, iceberg_tables is part of system schema and part of mcp2ohio catalog"
# Extracted: catalog=mcp2ohio, schema=system
# Generated SQL: SELECT * FROM mcp2ohio.system.iceberg_tables LIMIT 100
```

Supported patterns:
- `from X schema in Y catalog`
- `is part of X schema and part of Y catalog`
- `in X schema`
- `in Y catalog`

#### Cross-Schema Table Lookup

When a table is not found in the default schema, `_try_other_schemas()` searches:
1. In-memory schema cache (instant)
2. Fallback: `information_schema.tables` query (single round-trip)

#### Aggregate Column Aliasing

```python
# Before: SELECT name, COUNT(*) FROM demo GROUP BY name → columns: [name, _col1]
# After:  SELECT name, COUNT(*) AS count FROM demo GROUP BY name → columns: [name, count]
```

Regex `_AGG_ALIAS_RE` adds aliases to `COUNT`, `SUM`, `AVG`, `MIN`, `MAX` functions without existing `AS` clauses.

### 2. Parallel Schema Fetching

**Problem:** Sequential schema fetch made 1 + N + M queries (SHOW SCHEMAS + SHOW TABLES per schema + DESCRIBE per table). With 3 schemas and 14 tables = ~37 seconds.

**Solution:** Three-step parallel pipeline:

```python
# Step 1: SHOW SCHEMAS (single query)
# Step 2: SHOW TABLES for all schemas in parallel (ThreadPoolExecutor)
# Step 3: DESCRIBE for all tables across all schemas in parallel (max 10 workers)
```

**Result:** 37s → 16s (57% reduction)

Additional optimizations:
- 5-minute TTL in-memory cache (`_schema_cache`)
- Background thread pre-warm on startup
- `?refresh=1` query param to bust cache
- Frontend refresh button (↻) with spin animation

### 3. Headless JWT Authentication (`starburst_client_jwt.py`)

**Problem:** Starburst Galaxy's `OAuth2Authentication()` opens a browser for interactive login on every first connection.

**Discovery Process:**
1. Starburst Galaxy does NOT support `client_credentials` grant (token endpoint returns 405)
2. Galaxy service accounts work as BasicAuth credentials, but user required JWT specifically
3. Found Galaxy's SPA login API by inspecting JS bundles

**Solution:** Intercept `webbrowser.open` and complete OAuth programmatically:

```python
# Step 1: POST /api/v1/login {email, password} → 200 (session cookie set)
# Step 2: GET initiate_url (from Trino 401 challenge) → sets authorize cookies
# Step 3: GET /oauth/v2/redirect → 303 → callback with auth code (completes flow)
```

Implementation uses `unittest.mock.patch("webbrowser.open", side_effect=handler)` to monkey-patch the browser call. Trino client internally caches and auto-refreshes the token.

### 4. Token Cache (`token_cache.py`)

```python
# First run:
#   → No token_cache.json → headless login → save {host, email, created_at, expires_at}
# Second run:
#   → Found token_cache.json → check expires_at → if valid, skip login
# Expired:
#   → expires_at < now → headless login again → overwrite file
```

CLI test:
```bash
$ python token_cache.py
Testing token cache...
No cached token found. Will login fresh.
Connected!
  Auth mode: jwt-cached
Query result (3 rows):
  Columns: ['id', 'name', 'amount']
Token saved to: token_cache.json

$ python token_cache.py  # second run
Found cached token:
  Host:    datateam-free-cluster.trino.galaxy.starburst.io
  Expires: Wed Apr 15 07:08:16 2026
```

### 5. Frontend (`index.html`)

Single-page application, 800+ lines, self-contained with CDN dependencies:

| Dependency | CDN | Purpose |
|-----------|-----|---------|
| Tailwind CSS | cdn.tailwindcss.com | Styling |
| Chart.js | cdn.jsdelivr.net/npm/chart.js | Visualizations |
| SheetJS | cdn.sheetjs.com | Excel export |
| html2canvas | cdnjs.cloudflare.com | PDF/JPEG export |
| jsPDF | cdnjs.cloudflare.com | PDF generation |
| Google Fonts (Inter) | fonts.googleapis.com | Typography |

#### UI Components

- **Left Sidebar (280px, collapsible):** Schema browser tree (catalog → schema → tables), conversation history, dark/light toggle, schema refresh button
- **Center Panel:** Chat interface with user/bot messages, SQL code blocks with syntax highlighting, data tables, Chart.js visualizations, export toolbar
- **Right Panel (320px, collapsible):** Chart type selector (bar/pie/line/area), axis column dropdowns, color theme picker

#### Chart Features

- Per-bar/per-slice colors for single-dataset charts
- Chart title derived from column names (`count by name`, `name vs id, amount`)
- Axis labels from column names
- Tooltips with percentages for pie charts
- Legend with circle dot style, responsive positioning
- Theme-aware colors (dark/light mode)
- Rounded bar corners (`borderRadius: 6`)

#### Export Features

| Format | Method | Library |
|--------|--------|---------|
| CSV | Backend `/api/export/csv` | Python `csv` module |
| Excel | Backend `/api/export/xlsx` | `openpyxl` |
| HTML | Backend `/api/export/html` | Styled HTML table |
| PDF | Frontend capture | `html2canvas` + `jsPDF` |
| JPEG | Frontend capture | `html2canvas` (captures full message bubble) |

#### Smart Suggestion Chips

After every bot response, contextual follow-up queries appear:

- After `SHOW TABLES` → `DESCRIBE catalog.schema.table`, `SELECT * FROM catalog.schema.table LIMIT 100`
- After `SELECT *` → `SELECT COUNT(*)`, `DESCRIBE`, `GROUP BY`, `SUM/AVG` on numeric columns
- After `COUNT/SUM/AVG` → `SELECT *`, `DESCRIBE`, `Show all tables`

All suggestions use fully qualified table names (`mcp2ohio.test_writes.demo`).

### 6. Cluster Keepalive (`keepalive.py`)

```python
# Pings: SELECT 1 AS result (every 60 seconds)
# Logs:  keepalive.log with timestamp
# Trim:  Every 5 minutes, keeps only last 10 log entries
# Auth:  Uses original StarburstClient (OAuth with cached token)
```

---

## Execution Logs

### Latency Benchmarks

| Step | Latency | Notes |
|------|---------|-------|
| Python import + client init | 295ms | One-time startup cost |
| OAuth handshake (first connect) | 4,822ms | Headless, no browser |
| Single query (SHOW TABLES) | 3,275ms | Network round-trip (India→US) |
| Single query (SELECT * demo) | 3,237ms | Consistent ~3.3s |
| Schema fetch — sequential | 37,000ms | 3 schemas, 14 tables |
| Schema fetch — parallel | 16,000ms | ThreadPoolExecutor |
| Schema fetch — cached | 0ms | In-memory, 5-min TTL |

### MCP Server Test (stdio JSON-RPC)

```bash
$ python -c "
import json, subprocess, sys
init = json.dumps({'jsonrpc':'2.0','id':1,'method':'initialize','params':{...}})
call = json.dumps({'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'execute_query','arguments':{'query':'SELECT * FROM mcp2ohio.test_writes.demo LIMIT 10'}}})
proc = subprocess.run([sys.executable, 'server.py'], input=init+'\n'+call, capture_output=True, text=True)
"
# Output: {"jsonrpc":"2.0","id":2,"result":{"content":[{"type":"text","text":"3 row(s) returned.\n\nid | name  | amount\n---+-------+-------\n2  | test2 | 200.0\n3  | test3 | 300.0\n1  | hello | 150.0"}]}}
```

---

## Errors & Resolutions

| Error | Root Cause | Resolution |
|-------|-----------|------------|
| `"metric" is not a registered controller` | Chart.js has no "metric" chart type | Skip chart rendering for `metric`/`table` suggestions |
| `Table 'mcp2ohio.test_writes.all' does not exist` | "show all tables" matched `show (\w+)` → captured "all" as table name | Added "show all tables" to exact match list before regex patterns |
| `DESCRIBE mcp2ohio.test_writes.mcp2ohio` | Raw SQL `DESCRIBE mcp2ohio.x.y` matched NL `describe` pattern | Move raw SQL check (with dots) before NL regex patterns |
| `SHOW all tables` syntax error | "Show all tables" treated as raw SQL after `SHOW` matched `_SQL_START` | Exact NL matches checked before raw SQL passthrough |
| Table rows blank in UI | `r["Table"]` used on array rows (should be `r[0]`) | Changed to index-based access `r[i]` |
| Pie chart all same color | `backgroundColor` was single color, not array | Per-slice color array for pie/doughnut/single-dataset bar |
| JPEG export blank image | Captured empty chart canvas area | Capture full message bubble `document.getElementById(msgId)` |
| Schema fetch blocks async event loop | Synchronous Starburst queries in `async def startup()` | Background thread via `threading.Thread(daemon=True)` |
| Schema fetch timeout (37s) | Sequential N+1 queries | Parallel `ThreadPoolExecutor` (37s → 16s) |
| Cross-schema table not found | NL translator hardcodes `test_writes` schema | `_try_other_schemas()` searches cached schema data |

---

## Alternatives Considered

| Decision | Chosen | Alternative | Rationale |
|----------|--------|-------------|-----------|
| NL→SQL engine | Regex patterns | LLM-powered (Claude API) | Regex is fast, free, deterministic; LLM needed for JOINs/subqueries |
| Auth | Monkey-patch webbrowser.open | client_credentials grant | Galaxy doesn't support client_credentials (405); BasicAuth works but user required JWT flow |
| Frontend | Single HTML file (CDN deps) | React/Next.js SPA | Single file is portable, no build step, easy to serve from FastAPI |
| Chart library | Chart.js (CDN) | D3.js, Plotly | Chart.js is lightweight, well-documented, sufficient for bar/pie/line |
| Schema cache | In-memory dict + TTL | Redis, localStorage | Simple, no external dependencies, sufficient for single-server |
| Export | Backend CSV/XLSX + Frontend PDF/JPEG | All backend or all frontend | Split gives best UX: backend for data formats, frontend for visual capture |

---

## Performance Notes

- **Network latency is the bottleneck** — ~3.3s per query (India → US East Ohio). Cannot be reduced without deploying closer to Starburst cluster.
- **Parallel schema fetch** reduces wall-clock time by 57% (37s → 16s) but increases concurrent connections to Starburst.
- **Schema cache (5-min TTL)** eliminates repeat schema queries. Manual refresh via `?refresh=1`.
- **Keepalive (60s interval)** prevents free cluster auto-suspend (5-min idle threshold). Uses lightweight `SELECT 1` query.
- **Log rotation** keeps `keepalive.log` at max 10 entries — no disk growth.

---

## Security Considerations

- `.env` file contains credentials — never committed to git (in `.gitignore`)
- `token_cache.json` contains token metadata (no raw token) — excluded from git
- CORS enabled for all origins (`allow_origins=["*"]`) — development only, restrict in production
- SQL injection mitigated by `validate_identifier()` for NL-generated queries; raw SQL passthrough trusts user input
- Aggregate alias regex only applies to known functions (`COUNT/SUM/AVG/MIN/MAX`) — no arbitrary SQL injection vector
- Galaxy login credentials transmitted over HTTPS to `datateam.galaxy.starburst.io`

---

## Dummy Data Tables Created

| Table | Rows | Columns | Best Chart Queries |
|-------|------|---------|-------------------|
| `sales_by_region` | 20 | region, quarter, revenue, units_sold, profit | `SELECT region, SUM(revenue) ... GROUP BY region` |
| `employees` | 20 | name, department, role, salary, performance_score, years_experience, city | `SELECT department, AVG(salary) ... GROUP BY department` |
| `web_analytics` | 15 | page, month, visitors, bounce_rate, avg_session_minutes, conversions | `SELECT page, SUM(visitors) ... GROUP BY page` |
| `products` | 15 | product_name, category, price, stock, rating, reviews | `SELECT category, AVG(rating) ... GROUP BY category` |

---

## Git History (v2)

| Commit | Message |
|--------|---------|
| `118c342` | `feat: StarQuery AI chatbot — NL-to-SQL web UI with charts and exports` |

---

## Conclusion (v2)

This session built StarQuery AI — a production-quality chatbot web interface for querying Starburst Galaxy via natural language. The system features headless JWT authentication (zero browser interaction), parallel schema fetching, Chart.js visualizations with smart chart suggestions, multi-format data exports, and a cluster keepalive mechanism. The NL→SQL translator supports dynamic catalog/schema context parsing, cross-schema table resolution, and aggregate column aliasing. All code is deployed on branch `dev3` with timestamped backups for rollback capability.
