# Starburst Galaxy Read-Write MCP + StarQuery AI

> Enterprise-grade toolkit for accessing Starburst Galaxy from AI agents and humans — a full CRUD **Model Context Protocol (MCP)** server plus **StarQuery AI**, a natural-language-to-SQL web chatbot.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![MCP](https://img.shields.io/badge/MCP-1.0%2B-green)]()
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)]()
[![License](https://img.shields.io/badge/license-Proprietary-lightgrey)]()

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Tech Stack](#tech-stack)
4. [Architecture](#architecture)
5. [Prerequisites](#prerequisites)
6. [Installation](#installation)
7. [Configuration](#configuration)
8. [Usage](#usage)
   - [A. MCP Server (Claude Code / IDE integration)](#a-mcp-server-claude-code--ide-integration)
   - [B. StarQuery AI Chatbot (Web UI)](#b-starquery-ai-chatbot-web-ui)
   - [C. Keepalive Daemon](#c-keepalive-daemon)
9. [API Reference](#api-reference)
10. [Permissions Model](#permissions-model)
11. [Development](#development)
12. [Deployment](#deployment)
13. [Troubleshooting / FAQ](#troubleshooting--faq)
14. [Security](#security)
15. [Roadmap](#roadmap)
16. [License & Maintainers](#license--maintainers)

---

## Overview

**Problem.** Starburst Galaxy is a managed Trino platform. Out of the box, access requires interactive OAuth browser flows, per-query role juggling, and manual SQL — none of which works for AI agents, headless servers, or non-technical business users.

**Solution.** This repo ships two complementary surfaces over the same Starburst client:

| Surface | Audience | Interface |
|---|---|---|
| **`starburst-rw` MCP server** | AI agents (Claude Code, Claude Desktop, other MCP clients) | stdio / JSON-RPC |
| **StarQuery AI** | Business users, analysts | Browser chat UI at `http://localhost:8001` |

Both share a JWT-based headless auth path, a per-developer permission layer, and a hardened SQL execution engine.

## Features

- **14 MCP tools** — 5 read (`execute_query`, `list_catalogs`, `show_schemas`, `show_tables`, `describe_table`) + 9 write (CRUD, DDL, MERGE) with confirm guards on destructive ops.
- **Natural-language SQL with optional LLM** — direct SQL always works, deterministic fallback covers common enterprise prompts, and the provider-agnostic LLM layer supports schema-aware NL2SQL through OpenAI-compatible providers such as DeepSeek, OpenAI, Kimi, plus Anthropic/Claude.
- **Headless OAuth2** — logs in via the Galaxy token endpoint; no browser popup; cached token auto-refreshes.
- **Per-developer permissions** — YAML config with profiles (`read_only`, `analyst`, `engineer`, `admin`) and per-user overrides, hot-reloaded.
- **Rich chatbot UX** — schema browser, Chart.js visualizations, CSV / Excel / HTML / PDF / JPEG export, dark/light mode.
- **Keepalive daemon** — pings the free cluster every 60 s to prevent cold starts.
- **Full test suite** — 14 unit + 6 integration tests, all green.

## Tech Stack

- **Language:** Python 3.11+
- **Database:** Starburst Galaxy (Trino) via `trino` DBAPI
- **MCP:** `mcp>=1.0.0` (FastMCP, stdio transport)
- **Web:** FastAPI + Uvicorn, vanilla HTML/JS frontend, Chart.js
- **AI:** Provider-agnostic LLM adapter, grounded schema context, SQL validation, deterministic fallback
- **Config:** PyYAML, python-dotenv
- **Tests:** pytest

## Architecture

```
                      ┌─────────────────────────────┐
                      │      Starburst Galaxy       │
                      │   (Trino, catalog=mcp2ohio) │
                      └──────────────┬──────────────┘
                                     │  HTTPS + OAuth2 bearer
                                     │
                     ┌───────────────┴───────────────┐
                     │   starburst_client_jwt.py     │
                     │   (headless auth + caching)   │
                     │   + permission_manager.py     │
                     └───────┬───────────────┬───────┘
                             │               │
           ┌─────────────────┴─────┐   ┌─────┴─────────────────┐
           │  server.py (MCP)      │   │  app_jwt.py (FastAPI) │
           │  stdio / JSON-RPC     │   │  /api/query, /api/... │
           │  14 tools             │   │  NL→SQL translator    │
           └──────────┬────────────┘   └──────────┬────────────┘
                      │                           │
               Claude Code / MCP clients     Browser (index.html)
```

**Data flow:** `user input → NL→SQL or tool call → permission check → SQL validation → Trino execute → result formatting → client`.

## Prerequisites

- Python **3.11+** (3.12 recommended)
- A Starburst Galaxy account with at least one catalog you can read from
- OAuth2 client credentials (Client ID + Client Secret) issued from Galaxy console, **or** a username/password fallback
- Optional: Claude Code, Claude Desktop, or any MCP-compatible client for the MCP surface

## Installation

```bash
# 1. Clone
git clone https://github.com/<ORG>/starburst-demo.git
cd starburst-demo/"gen-ai-project/starburst-mcp2"

# 2. Create virtualenv
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
.venv\Scripts\activate             # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# edit .env and fill in your credentials (see Configuration)

# 5. Verify
python -c "from starburst_client_jwt import StarburstClient; print(StarburstClient().execute('SELECT 1'))"
```

## GitHub Codespaces / Linux Quick Start

Use this when running inside a GitHub Codespaces VM or any fresh Linux environment.

```bash
# From the repository root
cd gen-ai-project/starburst-mcp2

# Optional but recommended: create an isolated virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies. If imports already work, this step can be skipped.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Create the local environment file. Never commit this file.
cp .env.example .env
nano .env

# Start the web app on the project demo port
python -m uvicorn app_jwt:app --host 0.0.0.0 --port 8001
```

Open the forwarded Codespaces port `8001` in the browser. The app should load at:

```text
http://127.0.0.1:8001/
```

For detailed step-by-step instructions for humans and AI agents, see:

- [`instruction-for-running-application-codespaces.md`](instruction-for-running-application-codespaces.md)
- [`manual-to-run-application-codespaces.md`](manual-to-run-application-codespaces.md)

## Configuration

Copy `.env.example` to `.env` and populate. **Never commit `.env`.**

| Variable | Required | Default | Description | Example (masked) |
|---|---|---|---|---|
| `STARBURST_HOST` | yes | — | Trino host | `<TENANT>-free-cluster.trino.galaxy.starburst.io` |
| `STARBURST_PORT` | no | `443` | Trino port | `443` |
| `STARBURST_CATALOG` | yes | — | Default catalog | `<YOUR_CATALOG>` |
| `STARBURST_SCHEMA` | yes | — | Default schema | `<YOUR_SCHEMA>` |
| `STARBURST_CLIENT_ID` | OAuth | — | Galaxy OAuth client ID | `<CLIENT_ID>@<TENANT>.galaxy.starburst.io` |
| `STARBURST_CLIENT_SECRET` | OAuth | — | Galaxy OAuth secret | `<CLIENT_SECRET>` |
| `STARBURST_TOKEN_URL` | OAuth | — | OAuth2 token endpoint | `https://<TENANT>.galaxy.starburst.io/oauth2/token` |
| `STARBURST_USER` | BasicAuth fallback | — | Galaxy username/role | `<USER>@<DOMAIN>/<ROLE>` |
| `STARBURST_PASSWORD` | BasicAuth fallback | — | Galaxy password | `<YOUR_PASSWORD>` |
| `STARBURST_DEVELOPER` | yes | `unknown` | Key into `permissions.yaml` | `<DEVELOPER_ID>` |

**Auth mode is auto-selected:** if `STARBURST_CLIENT_ID` is set → OAuth2; else BasicAuth.

## Usage

### A. MCP Server (Claude Code / IDE integration)

Register in `.mcp.json` at your repo root (or `~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "starburst-rw": {
      "type": "stdio",
      "command": "python",
      "args": ["./gen-ai-project/starburst-mcp2/server.py"]
    }
  }
}
```

Restart Claude Code. The `starburst-rw` server exposes 14 tools.

**Example tool invocation (from the agent side):**

```json
// Input
{
  "tool": "execute_query",
  "arguments": { "query": "SELECT region, SUM(revenue) FROM <CAT>.<SCH>.sales_by_region GROUP BY region" }
}
```

```
// Output (formatted text)
region     | _col1
-----------+--------
North      | 1240000
South      |  980500
East       | 1102300
West       |  875900
Central    |  756100
(5 rows)
```

**Destructive op guard:**

```json
// Input
{ "tool": "drop_table", "arguments": { "catalog": "<CAT>", "schema": "<SCH>", "table": "demo", "confirm": false } }

// Output
"WARNING: This will drop_table '<CAT>.<SCH>.demo'. This action cannot be undone. Pass confirm=true to proceed."
```

### B. StarQuery AI Chatbot (Web UI)

Start the server:

```bash
cd "gen-ai-project/starburst-mcp2"
python -m uvicorn app_jwt:app --host 0.0.0.0 --port 8001
# open http://localhost:8001 or the forwarded Codespaces port 8001
```

**Example — natural language:**

```
Input:   show all data from demo
```

```json
// POST /api/query → response
{
  "sql": "SELECT * FROM <CAT>.<SCH>.demo LIMIT 100",
  "columns": ["id", "name", "amount"],
  "rows": [[1, "Alice", 100.0], [2, "Bob", 200.0]],
  "row_count": 2,
  "chart_suggestion": "table",
  "message": "Executed: SELECT * FROM <CAT>.<SCH>.demo LIMIT 100"
}
```

**Example — cross-schema hint:**

```
Input:   show all data from iceberg_tables, iceberg_tables is part of system schema and part of <CAT> catalog
→ SQL:   SELECT * FROM <CAT>.system.iceberg_tables LIMIT 100
```

**Example — unrecognized prompt:**

```
Input:   tell me a joke
Output:  "I couldn't understand that query. Try phrases like:
          - show tables
          - describe <table>
          - show all data from <table>
          - count rows in <table>
          - top 10 <column> from <table>
          - sum/avg/min/max of <column> from <table>
          - group by <column> from <table>
          - Or enter raw SQL directly."
```

**Supported input patterns:** raw SQL pass-through; deterministic natural-language fallback for `show tables`, `describe <table>`, `show all data from <table>`, `count rows in <table>`, `top <N> <column> from <table>`, `sum/avg/min/max of <column> from <table>`, `group by <column> from <table>`; governed CREATE/INSERT/UPDATE/DELETE patterns; and optional schema-aware LLM NL2SQL when `LLM_ENABLED=true`.

### C. Keepalive Daemon

The Galaxy free-tier cluster sleeps after ~5 min idle. Run the pinger in the background:

```bash
python keepalive.py   # pings every 60s, trims log every 5 min
```

Output (`keepalive.log`):

```
[2026-04-20 10:15:00] OK - [[1]]
[2026-04-20 10:16:00] OK - [[1]]
```

## API Reference

**StarQuery FastAPI endpoints** (see `app_jwt.py`):

| Method | Path | Body | Returns |
|---|---|---|---|
| `GET`  | `/` | — | `index.html` |
| `GET`  | `/api/schema` | — | `{ catalogs: [...], schemas: {...}, tables: {...} }` |
| `POST` | `/api/query` | `{ message, context? }` | `{ sql, columns, rows, row_count, chart_suggestion, message }` |
| `POST` | `/api/exec` | `{ sql }` | Same as `/api/query` |
| `POST` | `/api/export/{csv\|xlsx\|html}` | `{ columns, rows, title }` | File stream |

**MCP tools** (see `tools/read_tools.py`, `tools/write_tools.py`):

| Category | Tool | Required permission |
|---|---|---|
| Read | `execute_query` (read_only=true) | `read` |
| Read | `list_catalogs`, `show_schemas`, `show_tables`, `describe_table` | `read` |
| Write | `insert_data` | `insert` |
| Write | `update_data` | `update` |
| Write | `delete_data` | `delete` |
| Write | `merge_data` | `merge` |
| DDL  | `create_schema` / `create_table` | `create_schema` / `create_table` |
| DDL  | `drop_table` / `drop_schema` / `truncate_table` | matching flag + `confirm=true` |
| Raw  | `execute_query` (write mode) | `execute_raw` |

## Permissions Model

Configured in `permissions.yaml`. Resolution order: **defaults → profile → per-user overrides**.

```yaml
profiles:
  read_only: { read: true }
  analyst:   { insert: true, update: true, delete: true, create_table: true }
  engineer:  { ..., create_schema: true, drop_table: true, truncate: true, merge: true }
  admin:     { ..., drop_schema: true, execute_raw: true }

developers:
  <DEVELOPER_ID>:
    profile: admin
  <ANALYST_USER>:
    profile: analyst
  <INTERN_USER>:
    profile: read_only
  <CUSTOM_USER>:
    profile: analyst
    overrides: { drop_table: true, truncate: true }
```

Hot-reload: edit YAML, next tool call sees the new config.

## Development

```bash
# Unit tests (no network)
pytest -m "not integration"

# Integration tests (hits live Galaxy — needs valid .env)
pytest -m integration

# All
pytest
```

Current suite: **14 unit + 6 integration = 20 tests, all pass**.

**Project layout:**

```
.
├── gen-ai-project/starburst-mcp2/
│   ├── server.py                 # MCP entry point
│   ├── app.py / app_jwt.py       # FastAPI (browser OAuth / headless JWT)
│   ├── index.html                # StarQuery UI
│   ├── starburst_client*.py      # Trino client (OAuth & JWT variants)
│   ├── token_cache.py            # disk-backed OAuth token cache
│   ├── permission_manager.py     # YAML permission engine
│   ├── permissions.yaml          # auth config
│   ├── tools/                    # MCP tool registrations
│   ├── tests/                    # unit + integration
│   ├── keepalive.py              # cluster pinger
│   └── docs/superpowers/         # design specs & plans
├── run_queries.py                # ad-hoc script runner
├── CLAUDE.md                     # agent development protocol
└── .devcontainer/                # Codespaces config
```

## Deployment

**Local / single dev.** Follow [Installation](#installation). Run `uvicorn app_jwt:app` and `keepalive.py` as background processes.

**GitHub Codespaces.** `.devcontainer/` installs dependencies from `gen-ai-project/starburst-mcp2/requirements.txt` and forwards port `8001`. After the Codespace boots, configure `.env`, then run:

```bash
cd gen-ai-project/starburst-mcp2
python -m uvicorn app_jwt:app --host 0.0.0.0 --port 8001
```

**Server / container** (not yet provided as image — build your own):

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r "gen-ai-project/starburst-mcp2/requirements.txt"
CMD ["python", "-m", "uvicorn", "app_jwt:app", "--host", "0.0.0.0", "--port", "8001", \
     "--app-dir", "gen-ai-project/starburst-mcp2"]
```

Mount `.env` as a secret; never bake credentials into the image.

## Troubleshooting / FAQ

| Symptom | Cause | Fix |
|---|---|---|
| `Table 'X.Y.Z' does not exist` | Wrong schema/catalog context | Use cross-schema hint: `... is part of <schema> schema and part of <catalog> catalog`, or click the table in the sidebar |
| Browser popup on login | Using `starburst_client.py` (OAuth browser mode) | Switch to `app_jwt.py` / `starburst_client_jwt.py` (headless JWT) |
| `Schema Browser` stuck on "Loading..." | Free cluster cold start | Wait 30 s, refresh; run `keepalive.py` to prevent |
| `Role <ROLE> does not have the privilege CREATE_SCHEMA` | Galaxy role lacks grant | Use a writable catalog (e.g., `mcp2ohio`) or grant role in Galaxy console |
| MCP tools not visible in Claude Code | Global stdio servers don't load in VS Code extension | Use project-level `.mcp.json` instead of global `settings.json` |

## Security

- **Secrets** live in `.env` (gitignored) and `token_cache.json` (gitignored going forward). Never commit either.
- **Identifier validation.** `starburst_client.py` rejects SQL identifiers that don't match `^[a-zA-Z][a-zA-Z0-9_]*$` and blocks SQL reserved words as names.
- **Permission enforcement.** Every write tool calls `PermissionManager.check()` before execution. Destructive ops additionally require `confirm=true`.
- **CORS.** StarQuery currently allows `*` for local dev — **restrict `allow_origins` before any non-local deployment.**
- **Token handling.** OAuth tokens cached on disk with filesystem perms; auto-refresh on expiry.
- **Audit logging.** All actions are journaled to the session memory file (per `CLAUDE.md` protocol) for full replay/recovery.

## Roadmap

- LLM-backed NL→SQL (current engine is regex-only)
- Role-aware query rewriting
- Multi-tenant permission isolation
- Prometheus metrics + Grafana dashboard
- Official Docker image + Helm chart

## License & Maintainers

**License.** Proprietary — internal use only until relicensed.

**Maintainer.** `<MAINTAINER_NAME>` (`<MAINTAINER_EMAIL>`)

**Repository.** `https://github.com/<ORG>/starburst-demo`

---

_Documentation generated 2026-04-20. For design rationale and historical decisions, see [`docs/superpowers/Enterprise_Documentation.md`](gen-ai-project/starburst-mcp2/docs/superpowers/Enterprise_Documentation.md) and [`docs/superpowers/End_User_Documentation.md`](gen-ai-project/starburst-mcp2/docs/superpowers/End_User_Documentation.md)._
