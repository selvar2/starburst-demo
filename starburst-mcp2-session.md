---
name: starburst-mcp2-session
description: Persistent development session memory for starburst-mcp2 project — tracks all actions, state, and recovery path
type: project
---

# PROJECT MEMORY FILE

## PROJECT OVERVIEW

- **Goal:** Build a full AI-powered Starburst Galaxy query interface with NL→SQL, charts, exports
- **Description:** StarQuery — web chatbot that translates natural language to SQL, runs against Starburst Galaxy, and returns charts/tables/exports
- **Tech Stack:** Python, FastAPI, Uvicorn, Trino DBAPI2, OAuth2 (headless JWT), Vanilla JS, Chart.js
- **Repository:** `selvar2/starburst-demo` → branch `dev3`
- **Codespaces path:** `/workspaces/starburst-demo`
- **Project folder:** `gen ai project/starburst-mcp2/`

---

## CURRENT STATE

### Completed
- Starburst Galaxy connection via Python trino client (BasicAuth + OAuth2)
- `StarburstClient` — original client with browser OAuth
- `StarburstClientJWT` — headless OAuth client (no browser popup, works in CI/Codespaces)
- `keepalive.py` — background ping every 60s to prevent free-cluster idle suspension
- `app_jwt.py` — FastAPI chatbot server on port 8000, headless JWT auth
- `app.py` — FastAPI server on port 8001, browser OAuth
- `index.html` — frontend fixed: `const API=''` (relative URL, works on public Codespaces port)
- `run_query_jwt.py` — headless JWT query runner (validated working)
- MCP server (`server.py`) registered in Claude Code settings
- `.github/agents/` folder committed to dev3
- Claude marketplace plugin auto-sync system (`.devcontainer/sync-marketplace.sh`)
- `setup.sh` + `start.sh` updated: auto-run sync + launch keepalive on container start
- `.claude/commands/generate-system-prompt.md` — real file copy (not symlink), visible in Claude Code `/` menu
- `.claude/agents/sys-prompt-agent.md` — real file copy
- `.claude/skills/system-prompt-generator/SKILL.md` — real file copy
- `compact_session_summary.md` — full session documentation at repo root
- 2026-05-09: `app_jwt.py` verified running on port 8000 from the repo virtualenv; `GET /`, `GET /api/schema`, and `POST /api/query` all succeeded

### In Progress
- Nothing currently in progress

### Known Issues / Notes
- Free-cluster cold start: 20-60 seconds
- `app_jwt.py` must be started manually after container restart (not auto-started by devcontainer)
- OAuth tokens cached in `token_cache.json` — headless flow re-uses cached token if valid
- Claude Code slash commands require **real files** (not symlinks) in `.claude/commands/` — sync script updated to use `cp` not `ln -sf`
- Fresh environments that only install `requirements.txt` will miss StarQuery web UI packages (`fastapi`, `uvicorn[standard]`, `openpyxl`, `python-multipart`) until they are installed separately

---

## SESSION LOGS

### [2026-04-22 Fix — Table Column Header Overlap]

#### ACTION TYPE: CODE
#### PURPOSE: Fix overlapping column names in data table UI
#### PRE-EXECUTION
- `.data-table th` had `position:sticky;top:0` but no `z-index`, causing header cells to render behind `<td>` rows when scrolling
- Background was `rgba(0,0,0,.15)` (semi-transparent) — content bled through on scroll

#### EXECUTION RESULT
Changed in `index.html`:
- `.data-table th` background → `var(--surface3)` (solid color for both dark and light themes)
- Added `z-index:2` to sticky header so it stays above data rows

#### STATUS: SUCCESS
#### OBSERVATIONS: Classic sticky-header z-index bug. Fix works for any number of columns and any row count.
#### NEXT STEP: None — fix complete.

### [2026-04-08 Session Start]

#### ACTION TYPE: CONFIG
#### PURPOSE: Set up persistent development memory system

Created `CLAUDE.md` and `starburst-mcp2-session.md`. Both files created successfully. Project was greenfield.

#### STATUS: SUCCESS
#### NEXT STEP: Begin development tasks.

---

### [2026-04-08 Task 1 — First Starburst Query]

#### ACTION TYPE: CLI
#### PURPOSE: Query sample.burstbank.account via Python trino client

```
SELECT * FROM "sample"."burstbank"."account" LIMIT 10
→ 10 rows, 21 columns (custkey, acctkey, products, cc_*, mortgage_*, auto_loan_*)
Connection: datateam-free-cluster.trino.galaxy.starburst.io:443
```

#### STATUS: SUCCESS

---

### [2026-04-08 Tasks 2–6 — MCP Discovery + Registration]

#### ACTION TYPE: CODE / CONFIG
#### PURPOSE: Discover Starburst native MCP server, register in Claude Code

- Audited `starburst-mcp/` (Python CLI, not MCP server)
- Found native Starburst MCP at `https://datateam.mcp.galaxy.starburst.io`
- OAuth client created: `claude_mcp@datateam.galaxy.starburst.io`
- Registered in `~/.claude/settings.json` as `starburst-galaxy` HTTP MCP server
- AI SQL functions discovered: `starburst.ai.prompt()`, `analyze_sentiment()`, `translate()`, `classify()`, `fix_grammar()`, `mask()`

#### STATUS: SUCCESS

---

### [2026-04-22 — Headless JWT OAuth Validation]

#### ACTION TYPE: CLI
#### PURPOSE: Validate headless JWT OAuth flow works in Codespaces (no browser)

```bash
cd "gen ai project/starburst-mcp2" && python3 run_query_jwt.py
```

```
Connecting to datateam-free-cluster.trino.galaxy.starburst.io (catalog=mcp2ohio, auth=jwt)
Executing: SELECT * FROM "sample"."burstbank"."account" LIMIT 1
1 row(s) returned.
custkey=1000001 | acctkey=1217470 | products=credit_card,auto_loan | cc_status=open | cc_balance=9209.9
```

#### STATUS: SUCCESS
#### OBSERVATIONS: Headless OAuth completed without manual browser click. JWT auth works in Codespaces.

---

### [2026-04-22 — app_jwt.py FastAPI Server Started]

#### ACTION TYPE: CLI
#### PURPOSE: Start StarQuery chatbot server on port 8000

```bash
nohup python3 -m uvicorn app_jwt:app --host 0.0.0.0 --port 8000 > /tmp/app_jwt.log 2>&1 &
```

Server started. Schema pre-warm runs in background thread on startup (5-min TTL cache).

Endpoints:
- `GET /` — serves index.html (frontend)
- `GET /api/schema` — returns cached schema
- `POST /api/query` — runs raw SQL
- `POST /api/chat` — NL→SQL translation + execution
- `POST /api/export/{fmt}` — CSV/JSON/Excel export

#### STATUS: SUCCESS

---

### [2026-04-22 — Fix "Failed to connect to server" on Public Codespaces Port]

#### ACTION TYPE: CODE
#### PURPOSE: Fix frontend error when accessing via public Codespaces URL (not localhost)

**Root cause:** `gen ai project/starburst-mcp2/index.html` line 275 had:
```js
const API = 'http://localhost:8000';
```
This doesn't resolve from external browser when using public Codespaces port.

**Fix applied:**
```js
const API = '';  // relative URL — works from any hostname
```

#### STATUS: SUCCESS
#### OBSERVATIONS: After fix, frontend loads correctly on public Codespaces port URL.

---

### [2026-04-22 — Push Changes to dev3]

#### ACTION TYPE: CLI
#### PURPOSE: Push all new code to remote dev3 branch

```bash
git pull --rebase origin dev3  # resolved "fetch first" rejection
git push origin dev3
```

#### STATUS: SUCCESS

---

### [2026-04-22 — Commit .github/agents Folder]

#### ACTION TYPE: CLI
#### PURPOSE: Commit previously untracked .github/agents/ folder

```bash
git add .github/agents/
git commit -m "feat: add GitHub agents configuration"
git push origin dev3
```

Note: User explicitly requested **no Claude co-author** in commit messages.

#### STATUS: SUCCESS

---

### [2026-04-22 — Claude Marketplace Plugin Auto-Sync System]

#### ACTION TYPE: CODE / CONFIG
#### PURPOSE: Auto-register Claude agents/commands/skills from claude-marketplace/ into .claude/ on every container start

**Files created/modified:**

1. `.devcontainer/sync-marketplace.sh` (new) — idempotent sync script
   - Originally used relative symlinks (`ln -sf` + `realpath --relative-to`)
   - **LATER CHANGED** to use `cp -f` + `diff` check (see fix below)
   - Scans: `claude-marketplace/plugins/*/agents/*.md` → `.claude/agents/`
   - Scans: `claude-marketplace/plugins/*/commands/*.md` → `.claude/commands/`
   - Scans: `claude-marketplace/plugins/*/skills/*/SKILL.md` → `.claude/skills/<name>/SKILL.md`

2. `.devcontainer/setup.sh` — added steps:
   - Step 7: `bash sync-marketplace.sh`
   - Step 8: launch `keepalive.py` via `nohup` if not already running

3. `.devcontainer/start.sh` — added same steps 7 & 8

Commit: `8a37010` — `feat: auto-sync Claude marketplace plugins on container start/create`

#### STATUS: SUCCESS

---

### [2026-04-22 — Fix: Symlinks Don't Work for Claude Code Slash Commands]

#### ACTION TYPE: CODE
#### PURPOSE: Fix /generate-system-prompt not appearing in Claude Code slash command menu

**Problem:** Claude Code does NOT follow symlinks when scanning `.claude/commands/` for slash commands.
Original sync script used `ln -sf` (symlinks) — looked correct in shell but invisible to Claude Code.

**Fix:**
1. Replaced symlinks with real file copies immediately:
   ```bash
   cp --remove-destination "$(realpath .claude/commands/generate-system-prompt.md)" .claude/commands/generate-system-prompt.md
   cp --remove-destination "$(realpath .claude/agents/sys-prompt-agent.md)" .claude/agents/sys-prompt-agent.md
   cp --remove-destination "$(realpath .claude/skills/system-prompt-generator/SKILL.md)" .claude/skills/system-prompt-generator/SKILL.md
   ```

2. Rewrote `sync-marketplace.sh` to use `cp -f` with `diff` idempotency check:
   ```bash
   sync_file() {
       local src="$1" dst="$2"
       if [ -f "$dst" ] && diff -q "$src" "$dst" >/dev/null 2>&1; then
           skipped=$((skipped + 1))
       else
           cp -f "$src" "$dst" && installed=$((installed + 1)) || errors=$((errors + 1))
       fi
   }
   ```

After fix: reload VSCode window (`Ctrl+Shift+P` → "Developer: Reload Window"), then `/` shows the command.

#### STATUS: SUCCESS
#### RULE LEARNED: Claude Code slash commands need REAL files in `.claude/commands/`, not symlinks.

---

### [2026-04-22 — Session Documentation]

#### ACTION TYPE: CODE
#### PURPOSE: Create persistent session summary at repo root

Created `compact_session_summary.md` — full summary of all features built, bugs fixed, commits, and how to run everything. No sensitive info (no keys/credentials).

#### STATUS: SUCCESS

---

## CURRENTLY REGISTERED ASSETS IN `.claude/`

| Type    | File                                              | Source Plugin            |
|---------|---------------------------------------------------|--------------------------|
| Command | `.claude/commands/generate-system-prompt.md`      | sys-prompt-generator     |
| Agent   | `.claude/agents/sys-prompt-agent.md`              | sys-prompt-generator     |
| Skill   | `.claude/skills/system-prompt-generator/SKILL.md` | sys-prompt-generator     |

To use: press `/` in Claude Code → type `generate-system-prompt`

---

## HOW TO RUN SERVERS

```bash
# Navigate to project folder
cd "/workspaces/starburst-demo/gen ai project/starburst-mcp2"

# Start chatbot server (headless JWT, port 8000) — PRIMARY
nohup python3 -m uvicorn app_jwt:app --host 0.0.0.0 --port 8000 > /tmp/app_jwt.log 2>&1 &

# Start original server (browser OAuth, port 8001) — SECONDARY
nohup python3 -m uvicorn app:app --host 0.0.0.0 --port 8001 > /tmp/app.log 2>&1 &

# Start keepalive (prevent free-cluster idle suspension)
nohup python3 keepalive.py >> keepalive.log 2>&1 &

# Check server logs
tail -f /tmp/app_jwt.log
tail -f keepalive.log

# Kill a server
pkill -f "uvicorn app_jwt"
pkill -f "uvicorn app:"
```

---

## KNOWN PATTERNS / DECISIONS

- Development protocol: log-before-execute, mandatory chain of thought
- **Symlink rule:** Claude Code doesn't follow symlinks in `.claude/` — always use real files
- **Relative API URL:** `const API = ''` in index.html — never hardcode localhost
- **keepalive.py:** Always run as background process; devcontainer auto-starts it
- **No Claude co-author:** User requested all commits exclude `Co-Authored-By: Claude`
- **Branch:** All work goes to `dev3`, PRs merge to `main`

---

## SECURITY NOTES

- No API keys stored in this file
- `.env` files never committed
- Credentials masked wherever logged (`sk-****`, `GXY$****`)
- `token_cache.json` is gitignored (OAuth token cache)

---

## RECOVERY INSTRUCTIONS

**To resume this project from any point:**

1. Read `CLAUDE.md` in project root (auto-loaded by Claude Code)
2. Read this file (`starburst-mcp2-session.md`) for full context
3. Check **CURRENT STATE** section above
4. Start servers if needed (see HOW TO RUN SERVERS above)
5. The slash command `/generate-system-prompt` should be available after VSCode reload

**If slash command is missing after container restart:**
```bash
bash .devcontainer/sync-marketplace.sh
# Then reload VSCode window: Ctrl+Shift+P → "Developer: Reload Window"
```

**If Starburst connection fails (cold start):**
- Wait 20-60 seconds and retry — free-cluster needs warm-up time
- Check keepalive is running: `pgrep -f keepalive.py`

**If `app_jwt.py` fails with `ModuleNotFoundError: fastapi`:**
- Install the StarQuery web extras into the project environment:
   `pip install fastapi "uvicorn[standard]" openpyxl python-multipart`
- Then start the server with:
   `/workspaces/starburst-demo/.venv/bin/python -m uvicorn app_jwt:app --host 0.0.0.0 --port 8000`

---

### [2026-05-09 00:00]

#### ACTION TYPE: DESIGN
#### PURPOSE: Read runtime/authentication docs and identify the correct clean-start procedure for `app_jwt.py`
#### PRE-EXECUTION
- Review, in order:
   1. `/workspaces/starburst-demo/.devcontainer/devcontainer.json`
   2. `/workspaces/starburst-demo/.devcontainer/setup.sh`
   3. `/workspaces/starburst-demo/.devcontainer/start.sh`
   4. `/workspaces/starburst-demo/README.md`
   5. `/workspaces/starburst-demo/docs/FLOW.md`
   6. `/workspaces/starburst-demo/gen ai project/starburst-mcp2/STARBURST-AUTH.md`
   7. `/workspaces/starburst-demo/gen ai project/starburst-mcp2/docs/superpowers/End_User_Documentation.md`
   8. `/workspaces/starburst-demo/gen ai project/starburst-mcp2/docs/superpowers/Enterprise_Documentation.md`
   9. `/workspaces/starburst-demo/gen ai project/starburst-mcp2/app_jwt.py`
- Then inspect the current process state for port 8000, stop any stale server, and start `app_jwt.py` cleanly from `/workspaces/starburst-demo/gen ai project/starburst-mcp2`.

#### EXECUTION RESULT
Reviewed the requested runtime and authentication sources in order:

1. `.devcontainer/devcontainer.json`
2. `.devcontainer/setup.sh`
3. `.devcontainer/start.sh`
4. `README.md`
5. `docs/FLOW.md`
6. `gen ai project/starburst-mcp2/STARBURST-AUTH.md`
7. `gen ai project/starburst-mcp2/docs/superpowers/End_User_Documentation.md`
8. `gen ai project/starburst-mcp2/docs/superpowers/Enterprise_Documentation.md`
9. `gen ai project/starburst-mcp2/app_jwt.py`

Key findings from those files:
- Devcontainer lifecycle installs only `requirements.txt` plus validation checks; it does not auto-start `app_jwt.py`
- `keepalive.py` is auto-started, which reduces cold starts but does not make the web UI available by itself
- `app_jwt.py` is intended to run as a FastAPI/Uvicorn app on port `8000` from `gen ai project/starburst-mcp2`
- Headless auth depends on a local `.env` with Starburst host/catalog/schema plus `STARBURST_USER` and `STARBURST_PASSWORD`; `StarburstClientJWT` is instantiated at import time
- `app_jwt.py` serves `index.html` from its own directory, so the project file layout and launch path matter
- `app_jwt.py`'s `__main__` block points at `uvicorn.run("app:app", ...)`, so the reliable start command is `python -m uvicorn app_jwt:app --host 0.0.0.0 --port 8000`
- README docs list extra StarQuery web dependencies beyond `requirements.txt`, which explains the initial import failure in a fresh environment

#### STATUS: SUCCESS
#### OBSERVATIONS: External session log path from `CLAUDE.md` was not present in the container; the checked-in workspace log was used instead. The clean-start path and the likely failure points were identifiable directly from the requested files.
#### NEXT STEP: None for this analysis step.

---

### [2026-05-09 00:05]

#### ACTION TYPE: CONFIG
#### PURPOSE: Resolve the active Python environment for `gen ai project/starburst-mcp2` before running any Python-based server commands
#### PRE-EXECUTION
- Configure the Python environment for `/workspaces/starburst-demo/gen ai project/starburst-mcp2`
- Retrieve the Python executable details for that project so the server start command uses the active environment correctly

#### EXECUTION RESULT
Configured the Python environment for `/workspaces/starburst-demo/gen ai project/starburst-mcp2` successfully.

- Environment type: `VirtualEnvironment`
- Python version: `3.13.13`
- Terminal command prefix: `/workspaces/starburst-demo/.venv/bin/python`
- Verified the active environment and package inventory for the restart path; later startup validation showed `uvicorn`, `trino`, `python-dotenv`, and `requests` were present while `fastapi` was still missing at that point

#### STATUS: SUCCESS
#### OBSERVATIONS: `app_jwt.py` imports and instantiates `StarburstClientJWT` at module import time, so using the project virtualenv avoids path drift and missing-package startup failures.
#### NEXT STEP: Execute the clean port-8000 restart sequence with `/workspaces/starburst-demo/.venv/bin/python -m uvicorn app_jwt:app --host 0.0.0.0 --port 8000`.

---

### [2026-05-09 00:06]

#### ACTION TYPE: CLI
#### PURPOSE: Stop any stale process on port 8000 and start `app_jwt.py` cleanly from the project directory
#### PRE-EXECUTION
```bash
cd "/workspaces/starburst-demo/gen ai project/starburst-mcp2"
lsof -iTCP:8000 -sTCP:LISTEN -Pn || true
pgrep -af "uvicorn .*8000|app_jwt|app:app" || true
pkill -f "uvicorn app_jwt:app --host 0.0.0.0 --port 8000" || true
pkill -f "python3 app_jwt.py" || true
pkill -f "python app_jwt.py" || true
nohup python3 -m uvicorn app_jwt:app --host 0.0.0.0 --port 8000 > /tmp/app_jwt.log 2>&1 &
```

After start, verify with:
```bash
cd "/workspaces/starburst-demo/gen ai project/starburst-mcp2"
lsof -iTCP:8000 -sTCP:LISTEN -Pn || true
curl -I http://127.0.0.1:8000/
tail -n 80 /tmp/app_jwt.log
```

#### EXECUTION RESULT
Attempted clean restart with the project virtualenv and verified the captured server log.

Observed outcome:
- Background server process exited immediately with status `1`
- `/tmp/app_jwt.log` captured the exact startup failure:

```text
Traceback (most recent call last):
   File "/workspaces/starburst-demo/gen ai project/starburst-mcp2/app_jwt.py", line 11, in <module>
      from fastapi import FastAPI, HTTPException, Response
ModuleNotFoundError: No module named 'fastapi'
```

#### STATUS: FAILURE
#### OBSERVATIONS: Port 8000 was not the blocking issue. The active virtualenv is missing StarQuery web runtime dependencies, so `uvicorn app_jwt:app` cannot import the module. `if __name__ == "__main__"` in `app_jwt.py` also points at `app:app`, which is another reason to avoid starting it via `python app_jwt.py`.
#### NEXT STEP: Install the missing web app dependencies in the active virtualenv, then retry the clean port-8000 start and verification sequence.

---

### [2026-05-09 00:08]

#### ACTION TYPE: CONFIG
#### PURPOSE: Install missing StarQuery web runtime dependencies required by `app_jwt.py`
#### PRE-EXECUTION
- Install these Python packages into the active project environment:
   - `fastapi`
   - `uvicorn[standard]`
   - `openpyxl`
   - `python-multipart`

#### EXECUTION RESULT
Installed the missing StarQuery web runtime packages into the active project virtualenv successfully:

- `fastapi`
- `uvicorn[standard]`
- `openpyxl`
- `python-multipart`

#### STATUS: SUCCESS
#### OBSERVATIONS: The failure was environment-specific, not a syntax or import path problem inside `app_jwt.py`. The active virtualenv now has the packages the README calls out for the web UI path.
#### NEXT STEP: Retry the clean port-8000 start and verification sequence for `app_jwt.py`.

---

### [2026-05-09 00:10]

#### ACTION TYPE: CLI
#### PURPOSE: Retry the clean `app_jwt.py` startup after installing missing web dependencies
#### PRE-EXECUTION
```bash
cd "/workspaces/starburst-demo/gen ai project/starburst-mcp2"
lsof -iTCP:8000 -sTCP:LISTEN -Pn || true
pgrep -af "uvicorn .*8000|app_jwt|app:app" || true
pids=$(lsof -t -iTCP:8000 -sTCP:LISTEN -Pn || true)
if [[ -n "$pids" ]]; then kill $pids; fi
nohup /workspaces/starburst-demo/.venv/bin/python -m uvicorn app_jwt:app --host 0.0.0.0 --port 8000 > /tmp/app_jwt.log 2>&1 &
```

After start, verify with:
```bash
cd "/workspaces/starburst-demo/gen ai project/starburst-mcp2"
lsof -iTCP:8000 -sTCP:LISTEN -Pn || true
curl -I http://127.0.0.1:8000/
tail -n 80 /tmp/app_jwt.log
```

#### EXECUTION RESULT
Retried the clean startup after installing the missing web dependencies.

Verification results:
- Port 8000 listener present:
   - `python` PID `4717` listening on `*:8000`
- UI entrypoint check:
   - `GET /` returned `HTTP/1.1 200 OK`
   - Response body begins with `<!DOCTYPE html>` from `index.html`
- Backend API check:
   - `POST /api/query` with `{"sql":"SELECT 1"}` returned `{"columns":["_col0"],"rows":[[1]],"row_count":1}`
- UI bootstrap check:
   - `GET /api/schema` returned schema JSON successfully
- Uvicorn log summary:
   - Server started successfully
   - Application startup completed
   - Running at `http://0.0.0.0:8000`
   - An informational OAuth URL was printed by the auth stack, but headless query execution still succeeded without manual browser interaction

#### STATUS: SUCCESS
#### OBSERVATIONS: The earlier failure was fully explained by missing web dependencies in the fresh environment. After installing them, the app served both the UI and live backend data on port 8000.
#### NEXT STEP: None — clean restart and verification complete.

---

## SESSION 2026-05-09 — NL-driven DDL/DML feature

### BEFORE state (logged 2026-05-09T15:18Z)

**Goal:** Extend the FastAPI chatbot at `/api/chat` to handle natural-language DDL (CREATE/ALTER/DROP/TRUNCATE) and DML (INSERT/UPDATE/DELETE/MERGE), in addition to the existing SELECT/SHOW/DESCRIBE patterns.

**Discovery (parallel Explore agent + direct reads):**

| Component | Location | Notes |
|---|---|---|
| NL→SQL flow | `gen-ai-project/starburst-mcp2/app_jwt.py:193-256` (`_nl_to_sql`) | SELECT/SHOW/DESCRIBE only. Raw SQL passes through if it contains a dot. |
| Context hints parser | `app_jwt.py:152-182` (`_extract_context`) | Recognizes "is part of X schema and part of Y catalog". |
| SQL execution | `app_jwt.py:90-98` (`_exec`) | Calls `client.execute()` directly — bypasses permissions and validation. |
| Trino client | `starburst_client_jwt.py:126-149` (`StarburstClientJWT.execute`) | **Already supports DDL/DML** — returns `{rows_affected, status}` for non-SELECT. |
| Identifier validation | `starburst_client_jwt.py:151-156` (`validate_identifier`) | Static method, regex `^[a-zA-Z][a-zA-Z0-9_]*$` + reserved-word block. |
| Permission engine | `permission_manager.py` (`PermissionManager.check_with_message`) | YAML-driven, hot-reloaded. **NOT used by app_jwt.py currently.** |
| Permission keys | `permissions.yaml` | read, insert, update, delete, create_schema, create_table, drop_table, drop_schema, truncate, merge, execute_raw |
| Existing developer | `STARBURST_DEVELOPER=prakashrajr666` (admin profile) | All permissions granted in current `.env`. |
| MCP write tools | `tools/write_tools.py` | DDL/DML tools already implemented for MCP server, gated by perms + `confirm=true` for destructive ops. **app_jwt.py does NOT call them.** |
| Tests | `tests/test_permission_manager.py`, `tests/test_starburst_client.py`, `tests/test_integration.py` | Unit + integration. |

**Architectural finding:** `app_jwt.py` is fully independent of the permission/validation layer that exists for the MCP side. Extending NL coverage requires (a) new patterns in `_nl_to_sql`, (b) a strict FQ validator on the generated SQL, (c) a permission check via `PermissionManager`, (d) a destructive-op confirm guard.

**Plan (minimal/focused):**
1. Backup `app_jwt.py` → `gen-ai-project/starburst-mcp2/backup/app_jwt.20260509_204843.bak.py` with header comment.
2. Edit `app_jwt.py`:
   - Import `os`, `PermissionManager`. Init `_perms` and `_developer` once.
   - Add `_classify_sql(sql)` → (op_label, perm_key).
   - Add `_extract_target(sql, op_label)` and `_validate_fq(sql, op_label)` — rejects if not fully qualified.
   - Add NL patterns to `_nl_to_sql` for: insert/update/delete/truncate/drop table/drop schema/create schema/merge. CREATE TABLE & ALTER deferred to raw-SQL passthrough.
   - In `/api/chat`: after NL→SQL, classify → validate FQ → check perm → require `context.confirm=true` for destructive ops → execute.
3. Add `tests/test_app_jwt_nl.py` for unit coverage of the helpers.
4. Restart uvicorn and smoke-test.
5. Log AFTER state with results.

**Constraints honored:**
- All DDL/DML SQL must reference fully qualified `catalog.schema.table` (or `catalog.schema` for schema-level ops). Validator rejects bare names.
- Destructive ops (drop_table, drop_schema, truncate, delete) require explicit confirm.
- Permissions enforced via existing `PermissionManager` against `STARBURST_DEVELOPER` from `.env`.
- No edits to existing read paths; SELECT flow unchanged.

### AFTER state (logged 2026-05-09T15:35Z — completion)

**Files changed:**
- `gen-ai-project/starburst-mcp2/app_jwt.py` — extended (backup at `gen-ai-project/starburst-mcp2/backup/app_jwt.20260509_204843.bak.py`)
- `gen-ai-project/starburst-mcp2/tests/test_app_jwt_nl.py` — new (48 unit tests)

**Code additions in `app_jwt.py`:**

1. **Imports:** `os`, `PermissionManager`. Module init: `_perms = PermissionManager()`, `_developer = os.getenv("STARBURST_DEVELOPER", "unknown")`.
2. **Exceptions:** `FQValidationError`, `PermissionDenied`, `ConfirmRequired`.
3. **Classification:** `_classify_sql(sql) -> (op_label, perm_key)` covering all 14 SQL prefixes.
4. **FQ validator:** `_validate_fq(sql, op_label) -> dict` — extracts target via per-op regex, requires 3-part `catalog.schema.table` (or 2-part for schema-level ops), validates each identifier via `StarburstClient.validate_identifier`. Read ops are exempt.
5. **Permission check:** `_check_permission(perm_key)` — wraps `PermissionManager.check_with_message` with the developer ID from `.env`.
6. **Destructive guard:** `_enforce_destructive_confirm(perm_key, op_label, target, confirm)` — raises `ConfirmRequired` for `drop_table` / `drop_schema` / `truncate` / `delete` unless `context.confirm=true`.
7. **NL patterns** (added to `_nl_to_sql`, hoisted above the dot-passthrough so numeric literals like `1.0` don't trigger raw-SQL passthrough on writes):
   - `delete (from)? <tbl> [where ...]`
   - `truncate [table] <tbl>`
   - `drop table <tbl>` / `drop schema <sch>`
   - `create schema <sch>`
   - `update <tbl> set <cols> [where ...]`
   - `insert (into)? <tbl> values (...)`
   - Bare table names auto-qualify to `{catalog}.{schema}.{table}` from defaults / context hints.
   - Complex CREATE TABLE column DDL and full MERGE statements still flow through raw-SQL passthrough, then the FQ validator + perm + confirm layer.
8. **`/api/chat` wiring:** after `_nl_to_sql`, classify → validate FQ → check perm → enforce destructive confirm → execute. Errors map to:
   - 400 with `{"error":"fq_validation",...}` for bad FQ
   - 403 with `{"error":"permission_denied",...}` for perm denial
   - 200 with `{"requires_confirm":true, "operation":..., "target":..., "message":...}` for destructive ops awaiting confirm
   - 200 with `{"rows_affected":..., "status":...}` on successful DML/DDL
9. **`_exec` enhancement:** normalizes `{rows_affected, status}` results into the response shape so the chart pipeline doesn't break for write ops.

**Safety rules added:**

| Rule | Where | Effect |
|---|---|---|
| FQ name required for all DDL/DML | `_validate_fq` | 400 if target is < 3 parts (or < 2 for schema-level ops) |
| Identifier syntax check on every part | `StarburstClient.validate_identifier` | 400 on reserved words or non-identifier chars |
| Permission gate per op | `PermissionManager.check_with_message` | 403 if developer profile lacks the required permission |
| Destructive confirm | `_enforce_destructive_confirm` | 200 + `requires_confirm:true` until client resends with `context.confirm=true` |
| Read path unchanged | (no edit) | Existing SELECT/SHOW/DESCRIBE behavior fully preserved |

**Tests executed and results:**

```
pytest tests/test_app_jwt_nl.py -v          → 48 passed
pytest tests/ -v -m "not integration"        → 62 passed, 6 deselected
pytest tests/test_integration.py -v          → 6 passed (51 s, hits live cluster)
```

**Live smoke tests against http://127.0.0.1:8000/api/chat:**

| # | Input | Expected | Actual |
|---|---|---|---|
| 1 | `delete from demo where id=99999` (no confirm) | requires_confirm=true | ✅ requires_confirm=true, sql qualified to mcp2ohio.test_writes.demo |
| 2 | same + `context.confirm=true` | rows_affected=N | ✅ rows_affected=0, executed |
| 3 | `DROP TABLE bare_table` | requires_confirm OR fq_validation | ✅ requires_confirm=true (auto-qualified) |
| 4 | `insert into demo values (777, 'nl_test', 7.7)` | rows_affected=1 | ✅ rows_affected=1 |
| 5 | `DELETE FROM test_writes.demo WHERE 1=0` (2 parts) | 400 fq_validation | ✅ HTTP 400, "got 'test_writes.demo'" |
| 6 | `show all tables` (regression) | 200 with tables | ✅ row_count=5, op=SHOW |
| 7 | `DROP TABLE mcp2ohio.test_writes.SELECT` | 400 (reserved word) | ✅ HTTP 400, "is a SQL reserved word" |
| 8 | `update demo set name='updated_via_nl' where id=2` | rows_affected=1 | ✅ rows_affected=1 |

**Remaining risks / limitations:**

1. **Single-developer permission model.** The chat UI runs as one `STARBURST_DEVELOPER` from `.env`. There is no per-session identity. For multi-tenant deployment, a JWT/session resolution layer is required.
2. **Auto-qualification of bare names** uses `STARBURST_CATALOG`/`STARBURST_SCHEMA` defaults. A user typing "drop table demo" will hit `mcp2ohio.test_writes.demo`. Acceptable per spec ("explicitly OR reliably resolve") but worth noting.
3. **CREATE TABLE column DDL** is not pattern-matched in NL — must be entered as raw SQL with FQ name. Same for full MERGE statements.
4. **`ALTER` is mapped to `execute_raw` permission** (not in any standard profile). Expect 403 unless the developer has `execute_raw=true`.
5. **Latent bug at `app_jwt.py:706`:** `uvicorn.run("app:app", ...)` still references the wrong module — running `python app_jwt.py` directly loads `app.py`. Out of scope; launch via `python -m uvicorn app_jwt:app` works fine.
6. **CORS open to `*`** — restrict before any non-local deployment.

**Recommended next steps:**

1. Surface NL DDL/DML in the frontend (`index.html`) — current chips are SELECT-only. Add a confirmation dialog tied to `requires_confirm: true` responses.
2. Add NL patterns for `ALTER TABLE ... ADD/DROP COLUMN` and `RENAME TABLE` — common ops with simple grammars.
3. Replace single-developer mode with per-session identity (JWT claim → developer name).
4. Fix the line-706 self-launch bug.
5. Move `_developer` resolution into a request-time context so future per-session perms can plug in cleanly.
6. Audit the destructive list — consider gating `update` without `WHERE` clauses (currently a missing-WHERE update silently affects all rows — Trino allows it).

**Status:** ✅ Feature complete, all 62 unit tests + 6 integration tests + 8 live smoke tests pass. uvicorn is running at http://127.0.0.1:8000/.

---

## SESSION 2026-05-09 (continued) — Business-user NL INSERT grammar

### BEFORE state (logged 2026-05-09T15:55Z)

**Goal:** Support a business-user-friendly NL phrasing for INSERT, on top of the existing developer-SQL forms. Three example inputs to recognize:
1. `Add a new row into catalog mcp2ohio, schema test_writes, table demo with id 777, name nl_test, and amount 7.7`
2. `Insert a record into mcp2ohio.test_writes.demo where id = 888, name = cols_form, and amount = 1.5`
3. `In catalog mcp2ohio, schema test_writes, add a row to table demo with id 901, name fq_form, and amount 9.99`

**Constraint:** "Do not guess missing database object context" — so the new NL parser MUST require explicit catalog/schema/table (no default fallback). Existing developer SQL forms (which DO use defaults) keep working unchanged.

**Plan:**
1. Backup app_jwt.py with timestamp + comment header.
2. Add `_NL_INSERT_TRIGGER` regex (matches: `^add (a)? (new)? row|record`, `^insert (a)? (new)? row|record`, `^in catalog`).
3. Add `_render_value(raw)` — quote/cast helper for values (string/int/float/null/bool, strips surrounding `"` `'` ` ` ).
4. Add `_nl_insert_to_sql(msg, default_catalog, default_schema)` — extracts target via dotted-form OR verbose phrases (`catalog X / schema Y / table Z`), parses col-value pairs from the segment after `with|where|having`, validates each identifier, renders SQL.
5. Insert the trigger check at the top of `_nl_to_sql` so it runs before the dot-passthrough that would mis-classify "Insert a record into …" as raw SQL.
6. Add tests for: all three sample prompts; missing catalog/schema/table; missing values; quoted values; numeric/null/bool values; existing dev-SQL forms unchanged.
7. Restart uvicorn and smoke-test live.

### AFTER state (logged 2026-05-09T16:25Z — completion)

**Files changed:**
- `gen-ai-project/starburst-mcp2/app_jwt.py` — added `_NL_INSERT_TRIGGER`, `_render_value`, `_nl_insert_to_sql`; trigger check at top of `_nl_to_sql`; `try/except FQValidationError` around `_nl_to_sql` in `/api/chat`. Backup: `gen-ai-project/starburst-mcp2/backup/app_jwt.20260509_232040.bak.py`.
- `gen-ai-project/starburst-mcp2/tests/test_app_jwt_nl.py` — added 10 new tests covering happy paths, rejection cases, dev-SQL preservation.

**Tests:** 72 unit tests + 6 integration = 78 passing, 0 failing.

**Live smoke tests (8 cases, all green):**

| # | Input | Expected | Actual |
|---|---|---|---|
| 1 | `Add a new row into catalog mcp2ohio, schema test_writes, table demo with id 7777, name nl_smoke_v, and amount 7.77` | rows_affected=1 | ✅ INSERT INTO mcp2ohio.test_writes.demo (id, name, amount) VALUES (7777, 'nl_smoke_v', 7.77), rows_affected=1 |
| 2 | `Insert a record into mcp2ohio.test_writes.demo where id = 8888, name = nl_smoke_d, and amount = 1.5` | rows_affected=1 | ✅ rows_affected=1 |
| 3 | `In catalog mcp2ohio, schema test_writes, add a row to table demo with id 9999, name nl_smoke_s, and amount 9.99` | rows_affected=1 | ✅ rows_affected=1 |
| 4 | `Add a new row into catalog mcp2ohio, table demo with id 1, name a` (missing schema) | 400 fq_validation | ✅ HTTP 400, "Could not resolve schema..." |
| 5 | `Add a new row into catalog mcp2ohio, schema test_writes, table demo` (no values) | 400 fq_validation | ✅ HTTP 400, "Could not find column values..." |
| 6 | `INSERT INTO mcp2ohio.test_writes.demo VALUES (10101, 'dev_sql_fq', 1.01)` | rows_affected=1 | ✅ existing dev SQL still works |
| 7 | `insert into demo (id, name, amount) values (20202, 'dev_sql_bare', 2.02)` | rows_affected=1 | ✅ bare-name auto-qualify still works |
| 8 | `show all tables` | row_count=5 | ✅ SELECT regression clean |

All 5 smoke rows cleaned up (single NL DELETE with confirm: `delete from demo where id in (7777,8888,9999,10101,20202)` → 5 rows).

**Status:** ✅ Feature complete. uvicorn at http://127.0.0.1:8000/.

---

## SESSION 2026-05-09 (continued) — Clarification: placeholder vs real cluster objects

### Issue logged

User tested the prompt:
```
Add a record into catalog c, schema s, table t with a 1, b null, c true
```

**Observed:**
- Generated SQL: `INSERT INTO c.s.t (a, b, c) VALUES (1, NULL, TRUE)` — correct
- HTTP 400, Trino error: `TABLE_NOT_FOUND ... Table 'c.s.t' does not exist`

**Root cause:** the prompt was a syntactic/unit-test demo using placeholder identifiers `c`/`s`/`t`. Those objects don't exist on the live `mcp2ohio` cluster — the cluster correctly rejected the insert.

**Resolution:** to actually execute the prompt, replace placeholders with real cluster objects:
```
Add a record into catalog mcp2ohio, schema test_writes, table demo with id 1, name null, amount 7.7
→ INSERT INTO mcp2ohio.test_writes.demo (id, name, amount) VALUES (1, NULL, 7.7)  → rows_affected=1
```

The `demo` table has no boolean column. To exercise `true`/`false` value rendering, create a table with a BOOLEAN column first:
```
CREATE TABLE mcp2ohio.test_writes.bool_demo (a INTEGER, b VARCHAR, c BOOLEAN)
Add a record into catalog mcp2ohio, schema test_writes, table bool_demo with a 1, b null, c true
→ INSERT INTO mcp2ohio.test_writes.bool_demo (a, b, c) VALUES (1, NULL, TRUE)
```

**Diagnosis pattern documented:**
1. Inspect the `sql` field in any response — that's what was sent to Trino.
2. Read the `detail` field for Trino's error category (TABLE_NOT_FOUND / COLUMN_NOT_FOUND / TYPE_MISMATCH / ACCESS_DENIED).
3. Use `/api/schema` or `describe <table>` to confirm what objects/columns exist.

---

## SESSION 2026-05-09 (continued) — Business-user NL UPDATE grammar

### BEFORE state

**Goal:** Add a business-user-friendly NL UPDATE grammar parallel to the NL INSERT one. Three target prompts:
1. `In catalog mcp2ohio, schema test_writes, table demo, update the row where id = 2 and set name to updated_via_nl`
2. `Change amount to 1500.5 in catalog mcp2ohio, schema test_writes, table demo for the row where name = 'hello'`
3. `Update mcp2ohio.test_writes.demo and set amount = 999 where id = 888`

**Existing UPDATE coverage:**
- Raw SQL passthrough: works (e.g. `UPDATE mcp2ohio.test_writes.demo SET amount=999 WHERE id=888`)
- Simple NL pattern at `_nl_to_sql`: `update\s+([\w.]+)\s+set\s+(.+?)(?:\s+where\s+(.+))?$` — handles `update demo set name='x' where id=1` but **fails** on the verbose business forms because of words like "the row", "and set", or "change ... to ...".
- Existing pattern also allows missing WHERE (would update all rows silently).

**Plan:**
1. Backup `app_jwt.py` with timestamp + comment header.
2. Refine `_NL_INSERT_TRIGGER` so the `^in catalog ...` branch requires an `add|insert` verb later (avoids overlap with UPDATE's `^in catalog ...` branch).
3. Add `_NL_UPDATE_TRIGGER` (matches `change <col> to`, `update the row|record`, `update X.Y.Z and set`, and `^in catalog ... update|change`).
4. Add `_nl_update_to_sql(message)` parser:
   - Resolve target via inline dotted form OR verbose `catalog/schema/table` phrases.
   - Extract one or more SET pairs via `set <col> to|= <val>`, `and set <col> to|= <val>`, or `change <col> to <val>`.
   - Extract WHERE clause (mandatory; reject if missing).
   - Validate identifiers; render values via existing `_render_value`.
5. Wire into `_nl_to_sql` after the INSERT trigger check.
6. Add tests for happy paths (3 spec examples + multi-set), and rejections (missing WHERE / missing schema / reserved-word column / no SET).
7. Restart uvicorn and smoke-test live.

**Constraint:** mandatory WHERE for the new business-NL form (per spec: "missing or unsafe filter conditions" → reject). Existing simple SQL pattern left alone for technical-user passthrough.

### AFTER state (UPDATE feature complete)

**Files changed:**
- `gen-ai-project/starburst-mcp2/app_jwt.py` — added `_NL_UPDATE_TRIGGER`, `_SET_PAIR_RE`, `_CHANGE_PAIR_RE`, `_WHERE_RE`, `_nl_update_to_sql()`. Refined `_NL_INSERT_TRIGGER` so its `^in catalog ...` branch requires `add|insert ... row|record` later (prevents collision with UPDATE's `^in catalog ...` branch). Backup: `gen-ai-project/starburst-mcp2/backup/app_jwt.20260509_235603.bak.py`.
- `gen-ai-project/starburst-mcp2/tests/test_app_jwt_nl.py` — added 11 UPDATE-specific tests.

**Tests:** 83 unit tests pass (11 new + 72 prior). 0 failures.

**Live smoke tests on `/api/chat`:**

| # | Input | Expected | Actual |
|---|---|---|---|
| 0 | seed: `Add a record into catalog mcp2ohio, schema test_writes, table demo with id 4242, name initial_value, amount 1.00` | rows_affected=1 | ✅ |
| 1 | `In catalog mcp2ohio, schema test_writes, table demo, update the row where id = 4242 and set name to updated_via_nl` | rows_affected=1, FQ UPDATE generated | ✅ `UPDATE mcp2ohio.test_writes.demo SET name = 'updated_via_nl' WHERE id = 4242` |
| 2 | `Change amount to 1500.5 in catalog mcp2ohio, schema test_writes, table demo for the row where name = 'updated_via_nl'` | rows_affected ≥1 | ✅ `UPDATE ... SET amount = 1500.5 WHERE name = 'updated_via_nl'` (2 rows hit; pre-existing row from earlier session) |
| 3 | `Update mcp2ohio.test_writes.demo and set amount = 999 where id = 4242` | rows_affected=1 | ✅ `UPDATE ... SET amount = 999 WHERE id = 4242` |
| 4 | missing WHERE: `Update mcp2ohio.test_writes.demo and set amount = 999` | HTTP 400 | ✅ "UPDATE requires a WHERE clause..." |
| 5 | missing schema: `In catalog mcp2ohio, table demo, update the row where id=1 and set name to a` | HTTP 400 | ✅ "Could not resolve schema..." |
| 6 | missing SET: `In catalog mcp2ohio, schema test_writes, table demo, update the row where id = 1` | HTTP 400 | ✅ "UPDATE requires a SET clause..." |
| 7 | dev SQL: `UPDATE mcp2ohio.test_writes.demo SET amount=11.11 WHERE id=4242` | rows_affected=1 | ✅ unchanged behavior |
| 8 | simple NL: `update demo set name='nl_simple' where id=4242` | rows_affected=1 | ✅ unchanged behavior |
| 9 | cleanup: `delete from demo where id=4242 (confirm=true)` | rows_affected=1 | ✅ |

**Status:** ✅ Feature complete. uvicorn at http://127.0.0.1:8000/.
