# Session Summary — Starburst MCP2 Dev

**Date:** 2026-04-22  
**Branch:** `dev3`  
**Repo:** `selvar2/starburst-demo`

---

## What Was Built

### 1. Keepalive Process
- **File:** `gen ai project/starburst-mcp2/keepalive.py`
- Pings Starburst with `SELECT 1` every 60 seconds to prevent free-cluster idle suspension
- Logs to `keepalive.log`, auto-trims to last 10 entries every 5 minutes
- Launched via `nohup` on container start/create

### 2. Headless JWT OAuth Client
- **File:** `gen ai project/starburst-mcp2/starburst_client_jwt.py`
- `StarburstClientJWT` class — drop-in replacement for `StarburstClient`
- Completes OAuth flow without browser popup by monkey-patching `webbrowser.open`
- Used for CI/headless environments where browser is unavailable

### 3. FastAPI Chatbot Servers
- **`app_jwt.py`** — port 8000, uses headless JWT auth
- **`app.py`** — port 8001, uses browser OAuth
- Endpoints: `GET /`, `GET /api/schema`, `POST /api/query`, `POST /api/chat`, `POST /api/export/{fmt}`
- Schema pre-warmed in background thread on startup (5-min TTL cache)

### 4. Frontend Fix — Relative API URL
- **File:** `gen ai project/starburst-mcp2/index.html` (line 275)
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
- **File:** `gen ai project/starburst-mcp2/index.html`
- **Root cause:** `.data-table th` had `position:sticky;top:0` but no `z-index`, causing headers to render behind `<td>` data rows on scroll. Semi-transparent background `rgba(0,0,0,.15)` let row content bleed through.
- **Fix:** Added `z-index:2` to sticky `<th>`, changed background to `var(--surface3)` (solid color for both dark and light themes).

#### Fix 2 — App Renamed to "Data Analytics AI"
- **File:** `gen ai project/starburst-mcp2/index.html`
- Changed `<title>`, sidebar logo text, and welcome screen heading from "StarQuery AI" → "Data Analytics AI" in three locations.

#### Fix 3 — Enterprise-Grade PDF Export
- **File:** `gen ai project/starburst-mcp2/index.html`
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
- **File:** `gen ai project/starburst-mcp2/index.html`
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
