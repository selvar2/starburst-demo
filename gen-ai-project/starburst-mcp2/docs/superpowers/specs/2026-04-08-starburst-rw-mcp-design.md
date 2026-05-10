# Starburst Read-Write MCP Server — Design Spec

**Date:** 2026-04-08
**Status:** Approved
**Project:** starburst-mcp2
**Author:** Claude + prakashrajr666

---

## 1. Goal

Build a custom Python MCP server that provides full read AND write access to Starburst Galaxy via Trino. This server is independent of the existing native `starburst-galaxy` MCP server (read-only) which remains untouched.

## 2. Constraints

- DO NOT modify or delete the existing `starburst-galaxy` native MCP server
- DO NOT modify or delete the existing `starburst-mcp` Python client project
- Build entirely from scratch in `c:\Users\Lenovo\gen ai project\starburst-mcp2\`
- Reference `starburst-mcp/starburst_client.py` for patterns only (no imports)
- OAuth2 authentication (not BasicAuth)
- Configurable per-developer write permissions via `permissions.yaml`

## 3. Architecture

### File Structure

```
starburst-mcp2/
├── CLAUDE.md                        # Project instructions (existing)
├── starburst-mcp2-session.md        # Session memory (existing)
├── starburst-s3-policy.json         # IAM policy (existing)
├── .env                             # OAuth + connection config (NEW)
├── .env.example                     # Template for .env (NEW)
├── permissions.yaml                 # Developer write permissions (NEW)
├── requirements.txt                 # Python dependencies (NEW)
├── server.py                        # MCP server entry point (NEW)
├── starburst_client.py              # Trino client with OAuth (NEW)
├── permission_manager.py            # Permission checking logic (NEW)
└── tools/                           # MCP tool handlers (NEW)
    ├── __init__.py
    ├── read_tools.py                # SELECT, SHOW, DESCRIBE tools
    └── write_tools.py               # INSERT, UPDATE, DELETE, CREATE, DROP, TRUNCATE, MERGE
```

### Data Flow

```
Claude Code → MCP Protocol → server.py
  → permission_manager.py (check if operation allowed for developer)
  → tools/read_tools.py OR tools/write_tools.py
  → starburst_client.py (OAuth + Trino DBAPI)
  → Starburst Galaxy (free-cluster)
  → mcp2ohio catalog → S3 (starburst-mcp2-lake-ohio)
```

## 4. Authentication

OAuth2 client credentials flow via Trino DBAPI.

```
Client ID:     claude_mcp@datateam.galaxy.starburst.io
Client Secret: (from .env, masked)
Token URL:     https://datateam.galaxy.starburst.io/oauth2/token
Grant Type:    client_credentials
```

The Trino Python client supports OAuth via `trino.auth.OAuth2Authentication`. If client_credentials flow is not directly supported, we fall back to JWT bearer token obtained manually and passed as `extra_credential`.

## 5. MCP Tools (14 total)

### Read Tools (5)

| Tool | Parameters | SQL |
|------|-----------|-----|
| `execute_query` | `query: str`, `read_only: bool=false` | Any SQL (permission-gated) |
| `list_catalogs` | none | `SHOW CATALOGS` |
| `show_schemas` | `catalog: str` | `SHOW SCHEMAS FROM <catalog>` |
| `show_tables` | `catalog: str`, `schema: str` | `SHOW TABLES FROM <catalog>.<schema>` |
| `describe_table` | `catalog: str`, `schema: str`, `table: str` | `DESCRIBE <catalog>.<schema>.<table>` |

### Write Tools — DDL (5)

| Tool | Parameters | SQL |
|------|-----------|-----|
| `create_schema` | `catalog: str`, `schema: str` | `CREATE SCHEMA <catalog>.<schema>` |
| `create_table` | `catalog: str`, `schema: str`, `table: str`, `columns: list[{name, type}]` | `CREATE TABLE ...` |
| `drop_table` | `catalog: str`, `schema: str`, `table: str`, `confirm: bool` | `DROP TABLE <catalog>.<schema>.<table>` |
| `drop_schema` | `catalog: str`, `schema: str`, `confirm: bool` | `DROP SCHEMA <catalog>.<schema>` |
| `truncate_table` | `catalog: str`, `schema: str`, `table: str`, `confirm: bool` | `TRUNCATE TABLE <catalog>.<schema>.<table>` |

### Write Tools — DML (4)

| Tool | Parameters | SQL |
|------|-----------|-----|
| `insert_data` | `catalog: str`, `schema: str`, `table: str`, `rows: list[dict]` | `INSERT INTO ... VALUES (...)` |
| `update_data` | `catalog: str`, `schema: str`, `table: str`, `set_values: dict`, `where: str` | `UPDATE ... SET ... WHERE ...` |
| `delete_data` | `catalog: str`, `schema: str`, `table: str`, `where: str` | `DELETE FROM ... WHERE ...` |
| `merge_data` | `catalog: str`, `schema: str`, `table: str`, `source_query: str`, `on_condition: str`, `when_matched: str`, `when_not_matched: str` | `MERGE INTO ... USING ...` |

### Dangerous Operation Safeguards

- `drop_table`, `drop_schema`, `truncate_table` require `confirm: true` parameter
- If `confirm` is missing or false, return warning message instead of executing
- All operations check `permissions.yaml` before execution

## 6. Developer Permission System

### permissions.yaml

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

### Permission Resolution Order

1. Load developer entry from `developers` section
2. Resolve base `profile` (merge profile permissions over `defaults`)
3. Apply `overrides` (if any) on top
4. Cache result for the session
5. On each tool call, check if the required operation is `true`
6. If denied: return `"Operation '<op>' not permitted for developer '<dev>'. Profile: <profile>"`

### Hot Reload

- `permissions.yaml` is re-read on each tool call (file mtime check)
- No server restart needed to change permissions

## 7. Connection Config (.env)

```
# OAuth
STARBURST_CLIENT_ID=claude_mcp@datateam.galaxy.starburst.io
STARBURST_CLIENT_SECRET=<secret>
STARBURST_TOKEN_URL=https://datateam.galaxy.starburst.io/oauth2/token

# Connection
STARBURST_HOST=datateam-free-cluster.trino.galaxy.starburst.io
STARBURST_PORT=443
STARBURST_CATALOG=mcp2ohio
STARBURST_SCHEMA=test_writes

# Developer (for permission lookup)
STARBURST_DEVELOPER=prakashrajr666

# Fallback: BasicAuth (if OAuth not configured)
STARBURST_USER=prakashrajr666@networth.awsapps.com/accountadmin
STARBURST_PASSWORD=<password>
```

The client attempts OAuth first. If `STARBURST_CLIENT_ID` is not set, falls back to BasicAuth using `STARBURST_USER`/`STARBURST_PASSWORD`.

## 8. Error Handling

| Error | Response |
|-------|----------|
| Permission denied | `"Operation not permitted for developer. Profile: X"` |
| Connection failure | `"Failed to connect to Starburst Galaxy: <error>"` |
| SQL syntax error | `"SQL error: <trino error message>"` with query_id |
| Table not found | Forward Trino's `TABLE_NOT_FOUND` error |
| Catalog read-only | `"Catalog <name> only allows read-only access"` |
| Missing confirm flag | `"Dangerous operation requires confirm=true. This will <action>."` |
| OAuth token expired | Auto-refresh token, retry once |

## 9. Registration in Claude Code

Add to `~/.claude/settings.json` under `mcpServers`:

```json
"starburst-rw": {
  "type": "stdio",
  "command": "python",
  "args": ["c:/Users/Lenovo/gen ai project/starburst-mcp2/server.py"],
  "env": {}
}
```

This is a NEW entry. The existing `starburst-galaxy` (native read-only) remains untouched.

## 10. Dependencies (requirements.txt)

```
trino>=0.328.0
mcp>=1.0.0
python-dotenv>=1.0.0
pyyaml>=6.0
```

## 11. Testing Strategy

### Unit Tests
- Permission resolution (profile + overrides + defaults)
- SQL generation for each tool (parameterized, no injection)
- Identifier validation (catalog/schema/table names)

### Integration Tests (against mcp2ohio)
- Full CRUD cycle: CREATE SCHEMA → CREATE TABLE → INSERT → SELECT → UPDATE → DELETE → DROP TABLE → DROP SCHEMA
- Permission denial for unauthorized operations
- OAuth token refresh
- DDL with confirm=true/false

### Verified Working (from exploration)
- CREATE SCHEMA on mcp2ohio: SUCCESS
- CREATE TABLE on mcp2ohio: SUCCESS
- INSERT: SUCCESS (2 rows)
- UPDATE: SUCCESS (1 row modified)
- DELETE: SUCCESS (1 row removed)
- SELECT: SUCCESS (verified data integrity)

## 12. Out of Scope

- Multi-cluster support (only free-cluster for now)
- Transaction management (Trino has limited transaction support)
- Batch file uploads to S3
- Schema migration tooling
- Web UI for permission management
