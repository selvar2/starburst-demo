# Session Summary — Starburst MCP2 Dev

**Date:** 2026-04-22  
**Branch:** `dev3`  
**Repo:** `selvar2/starburst-demo`

---

## What Was Built

### 1. Keepalive Process
- **File:** `gen-ai-project/starburst-mcp2/keepalive.py`
- Pings Starburst with `SELECT 1` every 60 seconds to prevent free-cluster idle suspension
- Logs to `keepalive.log`, auto-trims to last 10 entries every 5 minutes
- Launched via `nohup` on container start/create

### 2. Headless JWT OAuth Client
- **File:** `gen-ai-project/starburst-mcp2/starburst_client_jwt.py`
- `StarburstClientJWT` class — drop-in replacement for `StarburstClient`
- Completes OAuth flow without browser popup by monkey-patching `webbrowser.open`
- Used for CI/headless environments where browser is unavailable

### 3. FastAPI Chatbot Servers
- **`app_jwt.py`** — port 8000, uses headless JWT auth
- **`app.py`** — port 8001, uses browser OAuth
- Endpoints: `GET /`, `GET /api/schema`, `POST /api/query`, `POST /api/chat`, `POST /api/export/{fmt}`
- Schema pre-warmed in background thread on startup (5-min TTL cache)

### 4. Frontend Fix — Relative API URL
- **File:** `gen-ai-project/starburst-mcp2/index.html` (line 275)
- Changed `const API='http://localhost:8000'` → `const API=''`
- Fixes "Failed to connect to server" error when accessed via public Codespaces port
- Relative URL works from any hostname (localhost or public Codespaces URL)

### 5. Claude Marketplace Plugin Auto-Sync
- **File:** `.devcontainer/sync-marketplace.sh`
- Idempotent script: symlinks marketplace plugin assets into `.claude/` on every container start
- Uses **relative symlinks** (`realpath --relative-to`) — works on any clone path
- Asset types synced:
  - `claude-marketplace/plugins/*/agents/*.md` → `.claude/agents/`
  - `claude-marketplace/plugins/*/commands/*.md` → `.claude/commands/`
  - `claude-marketplace/plugins/*/skills/*/SKILL.md` → `.claude/skills/<name>/SKILL.md`
- Skip logic: checks if symlink already points to correct relative path before re-creating
- Idempotency verified: run 1 → `installed=3 skipped=0`, run 2 → `installed=0 skipped=3`

### 6. DevContainer Lifecycle Updates
- **`setup.sh`** (`postCreateCommand` — runs once on container creation):
  - Step 7: calls `sync-marketplace.sh`
  - Step 8: launches `keepalive.py` in background via `nohup`
- **`start.sh`** (`postStartCommand` — runs on every container start/restart):
  - Step 7: calls `sync-marketplace.sh`
  - Step 8: launches `keepalive.py` if not already running (via `pgrep` check)

---

## Assets Registered in `.claude/`

| Type    | File                                          | Source (relative symlink)                                                        |
|---------|-----------------------------------------------|----------------------------------------------------------------------------------|
| Agent   | `.claude/agents/sys-prompt-agent.md`          | `../../claude-marketplace/plugins/sys-prompt-generator/agents/sys-prompt-agent.md` |
| Command | `.claude/commands/generate-system-prompt.md`  | `../../claude-marketplace/plugins/sys-prompt-generator/commands/generate-system-prompt.md` |
| Skill   | `.claude/skills/system-prompt-generator/SKILL.md` | `../../../claude-marketplace/plugins/sys-prompt-generator/skills/system-prompt-generator/SKILL.md` |

---

## Dependencies Added

```
python-dotenv
trino
```

Added to `setup.sh` and `start.sh` so they auto-install on container start.

---

## Key Bugs Fixed

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| `ModuleNotFoundError: dotenv` | Package not installed | `pip install python-dotenv` |
| `ModuleNotFoundError: trino` | Package not installed | `pip install trino` |
| "Failed to connect to server" in public port | Hardcoded `localhost:8000` in `index.html` | Changed to `const API=''` (relative URL) |
| `git push` rejected | Remote had newer commits | `git pull --rebase origin dev3` then push |
| Absolute symlinks break on fresh clone | `ln -s` used full `/workspaces/...` paths | Rewrote with `realpath --relative-to` |

---

## Commits Pushed to `dev3`

| Commit | Message |
|--------|---------|
| `4865554` | Fix headless OAuth flow: follow authorize URL before redirect, add query runner scripts |
| `8be6b39` | chore: add token_cache.json and session memory file |
| `3aa728c` | feat: JWT auth, keepalive improvements, and StarQuery UI updates |
| `118c342` | feat: StarQuery AI chatbot — NL-to-SQL web UI with charts and exports |
| `aa567f8` | feat: OAuth primary auth with BasicAuth fallback and connection reuse |
| `8a37010` | feat: auto-sync Claude marketplace plugins on container start/create |

---

## How to Run

```bash
# Start chatbot server (headless JWT, port 8000)
nohup python3 -m uvicorn app_jwt:app --host 0.0.0.0 --port 8000 > /tmp/app_jwt.log 2>&1 &

# Start original server (browser OAuth, port 8001)
nohup python3 -m uvicorn app:app --host 0.0.0.0 --port 8001 > /tmp/app.log 2>&1 &

# Start keepalive manually
nohup python3 keepalive.py >> keepalive.log 2>&1 &

# Sync marketplace plugins manually
bash .devcontainer/sync-marketplace.sh
```

---

## Project Stack

- **Data warehouse:** Starburst Galaxy (Trino-based)
- **Backend:** Python, FastAPI, Uvicorn
- **Auth:** OAuth 2.0 (headless JWT or browser-based)
- **MCP server:** `mcp` Python library (`FastMCP`)
- **Frontend:** Vanilla JS, Chart.js (served from FastAPI)
- **DevContainer:** VS Code Remote Containers / GitHub Codespaces
- **AI integration:** Claude Code with custom agents, commands, and skills via marketplace plugins

---

## Session — 2026-04-22 (Continuation)

### UI Fixes & Feature Additions

#### Fix 1 — Table Column Header Overlap
- **File:** `gen-ai-project/starburst-mcp2/index.html`
- **Root cause:** `.data-table th` had `position:sticky;top:0` but no `z-index`, causing headers to render behind `<td>` data rows on scroll. Semi-transparent background `rgba(0,0,0,.15)` let row content bleed through.
- **Fix:** Added `z-index:2` to sticky `<th>`, changed background to `var(--surface3)` (solid color for both dark and light themes).

#### Fix 2 — App Renamed to "Data Analytics AI"
- **File:** `gen-ai-project/starburst-mcp2/index.html`
- Changed `<title>`, sidebar logo text, and welcome screen heading from "StarQuery AI" → "Data Analytics AI" in three locations.

#### Fix 3 — Enterprise-Grade PDF Export
- **File:** `gen-ai-project/starburst-mcp2/index.html`
- **Old approach:** html2canvas screenshot of dark UI (non-standard, low contrast, captured UI chrome).
- **New approach:** Full jsPDF programmatic drawing with:
  - Navy header bar (`#1a2348`) with white app name + timestamp
  - Blue accent stripe below header
  - Report title block with row/column count
  - SQL pill in monospace box
  - Table with dark header row (`#1e2850`), alternating white/light-gray rows, column separators
  - Auto-pagination with repeated header on each new page
  - Footer with "Confidential & Internal Use Only" text + page number
  - PDF saved as landscape A4

#### Fix 4 — Suggestion Chips: Natural Language Labels with Hidden SQL
- **File:** `gen-ai-project/starburst-mcp2/index.html`
- **Old behavior:** Chips displayed raw SQL strings (e.g., `SELECT * FROM mcp2ohio.test_writes.demo LIMIT 100`).
- **New behavior:** Chips show friendly NL labels (e.g., "📄 Show all data from demo") but execute the actual SQL silently.
- **Implementation:**
  - `sendMessage(prefill, sqlOverride)` — decouples display text shown in chat from the query sent to backend.
  - `getSuggestions(data)` — returns `{label, sql}` objects instead of raw SQL strings. Context-aware: different suggestions after SHOW TABLES, DESCRIBE, SELECT *, aggregations, or default state.
  - `getChipIcon(label)` helper — maps label prefixes to emoji icons (📋 list, 🔍 describe, 🔢 count, 📊 aggregate, 📄 show data, 💡 default).
  - Chip renderer updated to call `sendMessage('${display}', '${q}')` with both label and SQL.

#### Example Chip Mappings (Before → After)
| Label shown on chip | SQL sent to backend |
|---|---|
| Show all tables | SHOW TABLES IN mcp2ohio.test_writes |
| Describe demo table | DESCRIBE mcp2ohio.test_writes.demo |
| Show all data from demo | SELECT * FROM mcp2ohio.test_writes.demo LIMIT 100 |
| Count rows in demo | SELECT COUNT(*) FROM mcp2ohio.test_writes.demo |
| Sum amount by category | SELECT category, SUM(amount) FROM mcp2ohio.test_writes.demo GROUP BY category ORDER BY SUM(amount) DESC |

### Pending Enhancement (Identified, Not Yet Implemented)
- **Chip disambiguation for same table name across schemas/catalogs:** Current chips show "Show all data from demo" — if multiple schemas/catalogs have a table named `demo`, the chip text is ambiguous. Enhancement needed: include `catalog.schema` in the chip label (e.g., "Show all data from mcp2ohio.test_writes.demo") so the NL→SQL translation can correctly resolve the fully-qualified table name. This was identified by the user via IDE selection at end of session.

---

# Compaction Summary — 2026-05-10

**Branch:** `dev6-cp-dev3` (based on `dev3@db6bb19`)
**Repo:** `starburst-mcp6/gen-ai-project/starburst-mcp2`

## Primary Request and Intent

Extend the FastAPI chatbot at `/api/chat` (in `app_jwt.py`) to support natural-language input for both technical users (raw SQL) and non-technical / business users (NL phrasings). Each phase added support for a specific operation:

- Initial: Read project files, diagnose backend connection failure, restart app cleanly
- Path renames after folder rename `gen ai project/` → `gen-ai-project/`
- Compare `dev3` vs `dev6-cp-dev3` branches, fresh-clone `dev3`
- Add NL DDL/DML support generally
- Add business-user NL **INSERT** grammar
- Add business-user NL **UPDATE** grammar
- Push to GitHub `dev6-cp-dev3` branch
- Add business-user NL **DELETE** grammar (destructive, confirm-gated)
- Add business-user NL **TRUNCATE** grammar (destructive, confirm-gated)
- Add business-user NL **DROP TABLE** grammar (destructive, confirm-gated)
- Add business-user NL **CREATE SCHEMA / DROP SCHEMA / CREATE TABLE** (DDL)

**Cross-cutting requirements:**
- Every code change must have a timestamped backup with header comments (why/before/after/restore)
- All changes logged to both `starburst-mcp2-session.md` and `session-2026-05-09.md`
- No guessing on missing object context; FQ `catalog.schema.table` required
- Destructive ops gated by `requires_confirm:true` until `context.confirm:true`
- Preserve all existing technical-user SQL forms
- Use throwaway tables for live validation, never real data

## Key Technical Concepts

- FastAPI chatbot at `/api/chat` with Pydantic models (`ChatRequest`, `QueryRequest`, `ExportRequest`)
- Starburst Galaxy + Trino DBAPI via `StarburstClientJWT` (headless OAuth2; monkey-patches `webbrowser.open`)
- `PermissionManager` with YAML config (profiles: `read_only`, `analyst`, `engineer`, `admin`; developer overrides)
- Regex-based NL→SQL parsing in `_nl_to_sql(message, catalog, schema)`
- Destructive-confirm gate via `_enforce_destructive_confirm` and `context.confirm: true`
- FQ validation via `_validate_fq` and `StarburstClient.validate_identifier`
- Type whitelist `_TYPE_MAP` for CREATE TABLE column types
- Paren-aware comma splitter `_split_top_level_commas` for sized types
- Trigger-regex pattern: each NL operation has its own `_NL_<OP>_TRIGGER` regex; dispatch order matters
- Backup files in `gen-ai-project/starburst-mcp2/backup/app_jwt.<TS>.bak.py` with header comments
- Git workflow on branch `dev6-cp-dev3` based on `dev3@db6bb19`

## Files and Code Sections

### `gen-ai-project/starburst-mcp2/app_jwt.py` (main file, all NL parsers)

- Imports: `os`, `PermissionManager`. Module init: `client = StarburstClient()`, `_perms = PermissionManager()`, `_developer = os.getenv("STARBURST_DEVELOPER", "unknown")`
- Exceptions: `FQValidationError`, `PermissionDenied`, `ConfirmRequired`
- `_DESTRUCTIVE_PERMS = {"drop_table", "drop_schema", "truncate", "delete"}`
- `_classify_sql(sql)` returns `(op_label, perm_key)` from `_CLASSIFY_PREFIXES` list
- `_validate_fq(sql, op_label)` extracts target via per-op `_TARGET_PATTERNS`, requires 3-part FQ (or 2-part for CREATE/DROP SCHEMA)
- `_check_permission(perm_key)` uses `PermissionManager.check_with_message`
- `_enforce_destructive_confirm(perm_key, op_label, target, confirm)` raises `ConfirmRequired` for destructive ops without confirm

**Business-user NL parsers** (in dispatch order in `_nl_to_sql`):

| Trigger | Parser | Output |
|---|---|---|
| `_NL_INSERT_TRIGGER` | `_nl_insert_to_sql(message)` | INSERT INTO with `_render_value` for type coercion |
| `_NL_UPDATE_TRIGGER` | `_nl_update_to_sql(message)` | uses `_SET_PAIR_RE`, `_CHANGE_PAIR_RE`, `_WHERE_RE`; mandatory WHERE |
| `_NL_DROP_TABLE_TRIGGER` | `_nl_drop_table_to_sql(message)` | DROP TABLE FQ |
| `_NL_DROP_SCHEMA_TRIGGER` | `_nl_drop_schema_to_sql(message)` | DROP SCHEMA cat.sch |
| `_NL_CREATE_SCHEMA_TRIGGER` | `_nl_create_schema_to_sql(message)` | CREATE SCHEMA cat.sch |
| `_NL_CREATE_TABLE_TRIGGER` | `_nl_create_table_to_sql(message)` | uses `_TYPE_MAP`, `_normalize_col_type`, `_split_top_level_commas` |
| `_NL_DELETE_TRIGGER` | `_nl_delete_to_sql(message)` | mandatory WHERE |
| `_NL_TRUNCATE_TRIGGER` | `_nl_truncate_to_sql(message)` | TRUNCATE TABLE FQ |

- `/api/chat` wraps `_nl_to_sql` in try/except for `FQValidationError`, then runs classify → validate_fq → check_permission → enforce_destructive_confirm → `_exec`
- `_exec` normalizes `rows_affected`/`status` for non-SELECT results

### `gen-ai-project/starburst-mcp2/tests/test_app_jwt_nl.py` (122 unit tests)

- 48 tests through Phase 6 (DDL/DML general)
- 10 tests for INSERT
- 11 tests for UPDATE
- 11 tests for DELETE
- 11 tests for TRUNCATE
- 12 tests for DROP TABLE
- 19 tests for CREATE/DROP SCHEMA + CREATE TABLE

### `starburst-mcp2-session.md` (persistent session memory, gitignored)
BEFORE/AFTER blocks for every feature.

### `session-2026-05-09.md` (3,106 lines, comprehensive session doc)
12 Phases with full code blocks, smoke I/O, examples.

### Backup files (7 total in `gen-ai-project/starburst-mcp2/backup/`)
- `app_jwt.20260509_204843.bak.py` (NL DDL/DML general)
- `app_jwt.20260509_232040.bak.py` (NL INSERT)
- `app_jwt.20260509_235603.bak.py` (NL UPDATE)
- `app_jwt.20260510_110001.bak.py` (NL DELETE)
- `app_jwt.20260510_111719.bak.py` (NL TRUNCATE)
- `app_jwt.20260510_113724.bak.py` (NL DROP TABLE)
- `app_jwt.20260510_115304.bak.py` (NL CREATE/DROP SCHEMA + CREATE TABLE)

Each has header comment with timestamp, source, branch, why, before, after, restore command.

### Permission config (`gen-ai-project/starburst-mcp2/permissions.yaml`)
- Developer `prakashrajr666` has `admin` profile
- `STARBURST_DEVELOPER` env var drives `_check_permission`

### Key code snippets

`_TYPE_MAP` (CREATE TABLE):
```python
_TYPE_MAP = {
    "int": "INTEGER", "integer": "INTEGER",
    "bigint": "BIGINT", "long": "BIGINT",
    "smallint": "SMALLINT", "short": "SMALLINT", "tinyint": "TINYINT",
    "varchar": "VARCHAR", "string": "VARCHAR", "text": "VARCHAR", "char": "CHAR",
    "double": "DOUBLE", "float": "DOUBLE", "real": "REAL",
    "decimal": "DECIMAL", "numeric": "DECIMAL",
    "boolean": "BOOLEAN", "bool": "BOOLEAN",
    "date": "DATE", "timestamp": "TIMESTAMP", "datetime": "TIMESTAMP",
    "time": "TIME", "json": "JSON", "uuid": "UUID",
}
```

`_split_top_level_commas`:
```python
def _split_top_level_commas(s: str) -> list[str]:
    parts, buf, depth = [], [], 0
    for ch in s:
        if   ch == '(': depth += 1; buf.append(ch)
        elif ch == ')': depth = max(0, depth - 1); buf.append(ch)
        elif ch == ',' and depth == 0:
            parts.append(''.join(buf).strip()); buf = []
        else: buf.append(ch)
    tail = ''.join(buf).strip()
    if tail: parts.append(tail)
    return [p for p in parts if p]
```

## Errors and Fixes

- **Missing .env file** (initial run): `AttributeError: 'NoneType' has no attribute 'split'` at `starburst_client_jwt.py:74` because `STARBURST_HOST` was None. Fixed when user manually added `.env`.
- **Numeric literal `1.0` triggered raw-SQL dot-passthrough** (test_nl_insert failed): Input `"insert into demo values (1, 'a', 1.0)"` had a dot in `1.0` so the existing dot-passthrough returned the raw text, bypassing INSERT NL pattern. Fixed by moving DDL/DML NL patterns ABOVE the dot-passthrough in `_nl_to_sql`.
- **`FQValidationError` raised inside `_nl_to_sql` wasn't caught by `/api/chat`** (smokes 4&5 returned HTTP 500 instead of 400): The try/except in `/api/chat` only wrapped the classify-time validator, not the parse-time call. Fixed by wrapping `_nl_to_sql(req.message, catalog, schema)` in try/except `FQValidationError`.
- **`_NL_INSERT_TRIGGER` "^in catalog" branch could collide with UPDATE**: Refined to require `add|insert ... row|record` verb after "in catalog" prefix.
- **`_NL_DELETE_TRIGGER` "^in catalog/schema ... delete|remove" branch was too broad**: Would match "permanently remove the table" and route to `_nl_delete_to_sql`. Fixed by requiring `(?:row|record)` after `(?:delete|remove)` in those branches.
- **`_NL_CREATE_TABLE_TRIGGER` had `\.\w+\.\w+` continuation that intercepted raw SQL** "CREATE TABLE <FQ> (cols)": Tightened trigger to require an NL marker (`named`, `in/on/of catalog/schema`, or `with columns`).
- **Comma inside `decimal(10,2)`** broke column splitter: Naive `cols_text.split(',')` produced `["...varchar(100)", " price as decimal(10", "2)"]`. Fixed by adding `_split_top_level_commas()` that tracks paren depth.
- **Auto-mode classifier blocked `Remove-Item .git -Recurse -Force` and `git checkout -B dev3 origin/dev3`**: User explicitly authorized via direct chat message ("already removed files, clone only").
- **Background bash subshell didn't preserve cd** (uvicorn started in wrong dir, exited 127): Switched to `python -m uvicorn app_jwt:app --port 8000 --host 127.0.0.1 --app-dir "gen-ai-project/starburst-mcp2"` instead of `cd && python ...`.
- **UnicodeEncodeError when piping JSON arrows through python on Windows** (`'charmap' codec can't encode character '→'`): Fixed by using ASCII-only characters in inline `python -c` invocations.

## Problem Solving

- **Solved:** Architecture decision to extend `app_jwt.py` directly rather than refactoring around shared service module (kept changes minimal, avoided premature abstraction)
- **Solved:** Trigger collision among multiple "^in catalog ..." branches by gating each on a specific second-keyword (row/record vs. table vs. schema vs. truncate/empty/clear)
- **Solved:** Order-dependent dispatch — DROP TABLE trigger placed BEFORE DELETE trigger in `_nl_to_sql` so "permanently remove the table" doesn't fall through
- **Solved:** All destructive ops gated through existing `_enforce_destructive_confirm` reusing the same confirm protocol
- **Solved:** Live cluster validation done with throwaway `scratch_table*` / `scratch_sch*` objects, all dropped at end (never real data)

## Current Work (Phase 12 — most recent feature)

The user's most recent feature task was implementing business-user NL grammar for three DDL operations: `CREATE SCHEMA`, `DROP SCHEMA`, and `CREATE TABLE`. This was completed end-to-end:

- Backed up `app_jwt.py` to `gen-ai-project/starburst-mcp2/backup/app_jwt.20260510_115304.bak.py`
- Added `_TYPE_MAP` (15 type aliases), `_normalize_col_type()`, `_split_top_level_commas()`
- Added 3 triggers + 3 parsers, wired between DROP TABLE and DELETE in `_nl_to_sql`
- Fixed 2 implementation bugs: comma split inside `decimal(10,2)` and CREATE TABLE trigger intercepting raw SQL
- All 122 NL unit tests pass; 136 unit total + 6 integration
- 9 live HTTP smokes against throwaway `scratch_sch` / `scratch_sch_2` / `scratch_table` / `scratch_dev` (all dropped at end)
- Logged AFTER state to both `starburst-mcp2-session.md` and `session-2026-05-09.md` (Phase 12 section)
- Server live at `http://127.0.0.1:8000/`, returned HTTP 200
- File sizes: `session-2026-05-09.md` = 3,106 lines; `starburst-mcp2-session.md` = 1,041 lines

## Pending Tasks / Optional Next Step

- **Push Phases 10–12** (TRUNCATE, DROP TABLE, CREATE/DROP SCHEMA, CREATE TABLE) to the `dev6-cp-dev3` branch on GitHub. Only Phase 9 and earlier was pushed in commit `bc67ed4`. Phases 10–12 are uncommitted/unpushed locally.
- No explicitly pending feature requests — the user's most recent feature request (Phase 12 DDL) was completed.
