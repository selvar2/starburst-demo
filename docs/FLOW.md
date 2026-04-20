# `app_jwt.py` — Flow Documentation

## 1. Executive Summary

`app_jwt.py` is the **FastAPI backend** for StarQuery AI — a browser-based chatbot that converts natural-language prompts into Trino/SQL against **Starburst Galaxy** and renders results as tables, charts, and exports. The "JWT" suffix denotes the **headless-OAuth2** variant: no interactive browser popup, because `webbrowser.open` is monkey-patched to complete the Galaxy OAuth flow programmatically (see [`starburst_client_jwt.py`](../gen%20ai%20project/starburst-mcp2/starburst_client_jwt.py)).

Audience: backend engineers extending the chatbot, adding tools, swapping the NL engine, or hardening for production.

Related docs: [`README.md`](../README.md), [`STARBURST-AUTH.md`](../gen%20ai%20project/starburst-mcp2/STARBURST-AUTH.md).

---

## 2. Technology Stack

| Layer | Technology | Version / Spec | Purpose | Why chosen |
|---|---|---|---|---|
| Frontend markup | HTML5 single file (`index.html`) | — | UI, schema browser, chat, chart panel | Zero build step; ships with backend |
| Frontend CSS | Inline CSS (dark/light) | — | Themed single-page UI | Keeps the app portable — one file, no bundler |
| Frontend JS | Vanilla JS (no framework) | ES2020+ | Fetch calls, DOM updates, exports | Avoids React/Vue toolchain for a demo-scale UI |
| Charting | Chart.js | CDN-loaded | Bar / pie / line / area | De-facto lightweight chart lib, no build |
| Frontend export | `html2canvas` + `jsPDF` | CDN | PDF/JPEG screenshot export | Client-side rendering — no server load |
| Web framework | FastAPI | latest | ASGI app, routing, DI, Pydantic models | Async-first, typed, auto OpenAPI |
| ASGI server | Uvicorn | `uvicorn[standard]` | Hosts FastAPI on `:8000` | Canonical pair with FastAPI |
| Validation | Pydantic v2 | bundled with FastAPI | `QueryRequest`, `ChatRequest`, `ExportRequest` at [`app_jwt.py:47-57`](../gen%20ai%20project/starburst-mcp2/app_jwt.py#L47-L57) | Declarative request validation |
| Concurrency | `threading`, `concurrent.futures.ThreadPoolExecutor` | stdlib | Parallel `SHOW TABLES` + `DESCRIBE` fan-out in `_fetch_schema` [`app_jwt.py:325-367`](../gen%20ai%20project/starburst-mcp2/app_jwt.py#L325-L367) | Trino calls are I/O-bound; threads avoid GIL pain |
| DB client | `trino` DBAPI | `>=0.328.0` | Cursor-based query execution | Official client |
| Database | Starburst Galaxy (Trino) | managed | Query federation + storage | Project target |
| Auth | OAuth2 (interactive flow, headless-patched) | `trino.auth.OAuth2Authentication` + monkeypatch | Bearer auth to Trino; login via Galaxy portal API | Avoids browser popup for servers/agents |
| Token cache | `token_cache.py` (standalone, **not imported by `app_jwt.py`**) | JSON on disk | Persist token across restarts | Cold-start latency reduction |
| Excel export | `openpyxl` | `>=3.1` | `.xlsx` writer | Pure-Python, no native deps |
| HTML export | stdlib string templating | — | Printable table | No deps |
| Config | `python-dotenv` | `>=1.0` | `.env` loader | 12-factor config |
| Permissions (MCP side) | PyYAML via `permission_manager.py` | — | Per-developer RBAC | Not used by `app_jwt.py` itself (MCP-only) |
| Tests | `pytest` | `>=8.0` | 14 unit + 6 integration | Standard |
| Ops | `keepalive.py` daemon, Codespaces `.devcontainer/` | — | Prevent Galaxy free-cluster cold start | Free tier idle-sleeps after ~5 min |

---

## 3. High-Level Architecture

```mermaid
graph TB
    subgraph Browser
        UI[index.html<br/>Vanilla JS + Chart.js]
    end

    subgraph Backend["FastAPI app_jwt.py :8000"]
        RT[Routes:<br/>/ /api/schema<br/>/api/query /api/chat<br/>/api/export/fmt]
        NL[_nl_to_sql<br/>regex engine<br/>app_jwt.py:193]
        FB[_try_other_schemas<br/>cross-schema fallback<br/>app_jwt.py:260]
        EXECF[_exec + _add_agg_aliases<br/>app_jwt.py:78-98]
        SC[Schema Cache<br/>_schema_cache dict<br/>TTL 300s]
    end

    subgraph Client["starburst_client_jwt.py"]
        SBC[StarburstClientJWT]
        HO[_HeadlessOAuth<br/>patches webbrowser.open]
    end

    subgraph Galaxy["Starburst Galaxy"]
        TRINO[(Trino cluster<br/>HTTPS :443)]
        PORTAL[[Galaxy portal<br/>api/v1/login + oauth/v2/redirect]]
    end

    UI -->|fetch JSON| RT
    RT --> NL
    NL --> EXECF
    RT --> EXECF
    EXECF --> SBC
    SBC -.OAuth flow.-> HO
    HO --> PORTAL
    SBC -->|SQL + Bearer| TRINO
    RT --> SC
    SC -. miss .-> SBC
    EXECF -. TABLE_NOT_FOUND .-> FB
    FB --> SC
    FB --> SBC
```

---

## 4. Request Lifecycle — `POST /api/chat`

```mermaid
sequenceDiagram
    autonumber
    participant U as User (Browser)
    participant JS as index.html JS
    participant API as FastAPI /api/chat
    participant NL as _nl_to_sql
    participant CTX as _extract_context / _clean_nl
    participant EX as _exec
    participant AGG as _add_agg_aliases
    participant C as StarburstClientJWT
    participant T as Trino (Starburst)

    U->>JS: type "show all data from demo" + Enter
    JS->>API: POST /api/chat {message, context}
    API->>API: _catalog(ctx), _schema(ctx)
    API->>NL: _nl_to_sql(message, catalog, schema)
    NL->>CTX: _extract_context(low, ...)
    CTX-->>NL: (catalog, schema) possibly overridden
    NL->>CTX: _clean_nl(low)
    CTX-->>NL: cleaned text
    NL-->>API: "SELECT * FROM cat.sch.demo LIMIT 100"
    API->>EX: _exec(sql)
    EX->>AGG: _add_agg_aliases(sql)
    AGG-->>EX: sql (aliases injected if any)
    EX->>C: client.execute(sql)
    C->>C: get_connection() reuse or reconnect
    C->>T: cur.execute(sql) over HTTPS+bearer
    T-->>C: rows, columns
    C-->>EX: {columns, rows}
    EX-->>API: {columns, rows, row_count}
    API->>API: _suggest_chart(columns, rows)
    API-->>JS: {sql, columns, rows, row_count, chart_suggestion, message}
    JS->>JS: render table + Chart.js
    JS-->>U: table + chart + suggestion chips
```

---

## 5. Authentication Flow (headless OAuth2)

`app_jwt.py` imports `StarburstClientJWT` ([`starburst_client_jwt.py:60`](../gen%20ai%20project/starburst-mcp2/starburst_client_jwt.py#L60)). The trick: `trino.auth.OAuth2Authentication` calls `webbrowser.open(url)` when it needs user consent; `StarburstClientJWT.get_connection()` uses `unittest.mock.patch` to redirect that call into `_HeadlessOAuth.handle_redirect`, which replays the Galaxy login via HTTP.

```mermaid
sequenceDiagram
    autonumber
    participant APP as app_jwt.py
    participant SBC as StarburstClientJWT
    participant MP as patch webbrowser.open
    participant HO as _HeadlessOAuth
    participant TA as trino OAuth2Authentication
    participant GP as Galaxy Portal
    participant TR as Trino cluster

    APP->>SBC: client.execute(sql)
    SBC->>SBC: get_connection()
    alt connection cached and alive
        SBC->>TR: SELECT 1 (liveness)
        TR-->>SBC: ok, reuse conn
    else new connection
        SBC->>MP: with patch(webbrowser.open to HO.handle_redirect)
        SBC->>TA: connect(auth=OAuth2Authentication())
        TA->>MP: webbrowser.open(initiate_url)
        MP->>HO: handle_redirect(url)
        HO->>GP: POST /api/v1/login {email, password}
        GP-->>HO: session cookies
        HO->>GP: GET initiate_url (no-follow)
        GP-->>HO: 302 + authorize cookies
        HO->>GP: GET /oauth/v2/redirect (follow)
        GP-->>HO: 200 (OAuth callback completed)
        TA->>GP: poll token endpoint
        GP-->>TA: access_token
        TA->>TR: attach Bearer, open JDBC
        TR-->>SBC: connection established
        SBC->>TR: SELECT 1 (force auth now)
    end
    SBC->>TR: run the real sql
    TR-->>SBC: result rows
    SBC-->>APP: {columns, rows}
```

**Note on `token_cache.py`.** It is a **separate** entry point that persists the token metadata to `token_cache.json` for restart reuse. It is **not** imported by `app_jwt.py`; it exists for standalone scripts and future consolidation.

---

## 6. NL to SQL Decision Flow (`_nl_to_sql`)

```mermaid
flowchart TD
    A[message: str] --> B[lowercase low = msg.lower]
    B --> C["_extract_context(low) parses<br/>'part of X schema', 'in Y catalog'"]
    C --> D[_clean_nl: strip context hints]
    D --> E{clean in exact list?<br/>show tables / list tables /<br/>tables / show all tables}
    E -->|yes| E1[SHOW TABLES FROM cat.sch] --> Z[return sql]
    E -->|no| F{clean in<br/>show schemas / list schemas}
    F -->|yes| F1[SHOW SCHEMAS FROM cat] --> Z
    F -->|no| G{raw SQL start AND '.' in msg}
    G -->|yes| G1[return msg as-is] --> Z
    G -->|no| H{describe / show columns of X}
    H -->|match| H1[DESCRIBE cat.sch.X] --> Z
    H -->|no| I{show all data from X / show me X}
    I -->|match| I1[SELECT * FROM cat.sch.X LIMIT 100] --> Z
    I -->|no| J{count rows in X}
    J -->|match| J1[SELECT COUNT star FROM cat.sch.X] --> Z
    J -->|no| K{top N col from X}
    K -->|match| K1[SELECT star ORDER BY col DESC LIMIT N] --> Z
    K -->|no| L{sum/avg/min/max of col from X}
    L -->|match| L1[SELECT AGG of col FROM cat.sch.X] --> Z
    L -->|no| M{group by col from X}
    M -->|match| M1[SELECT col, COUNT star GROUP BY col] --> Z
    M -->|no| N{raw SQL start without dots?}
    N -->|yes| N1[return msg as-is] --> Z
    N -->|no| O[return None<br/>API replies with help text]
```

Source: [`app_jwt.py:193-256`](../gen%20ai%20project/starburst-mcp2/app_jwt.py#L193-L256).

---

## 7. Error and Fallback Flow

When the default schema does not contain the requested table, `_try_other_schemas` searches the **in-memory schema cache** first, then falls back to `information_schema.tables`. This avoids repeated slow Trino round-trips.

```mermaid
flowchart TD
    A["_exec(sql)"] --> B{exception?}
    B -->|no| Z[return result]
    B -->|yes QueryError| C{err contains<br/>TABLE_NOT_FOUND or<br/>'does not exist'?}
    C -->|no| X[HTTP 400 raise]
    C -->|yes| D[_try_other_schemas]
    D --> E[regex extract<br/>schema+table from<br/>FROM cat.schema.table]
    E --> F{_schema_cache<br/>has data?}
    F -->|yes| G[iterate cached schemas<br/>skip default + information_schema]
    G --> H{table_name match?}
    H -->|yes| H1[rewrite sql to alt_sql] --> R[_exec alt_sql] --> Z
    H -->|no| I[continue]
    F -->|no or no match| J[query information_schema.tables<br/>WHERE table_name = X<br/>AND table_schema != default]
    J --> K{rows returned?}
    K -->|yes| K1[rewrite sql to alt_sql] --> R
    K -->|no| L[return None] --> X
```

Source: [`app_jwt.py:260-295`](../gen%20ai%20project/starburst-mcp2/app_jwt.py#L260-L295) and the `/api/chat` error branch at [`app_jwt.py:417-429`](../gen%20ai%20project/starburst-mcp2/app_jwt.py#L417-L429).

---

## 8. Module Dependency Graph

```mermaid
graph LR
    IDX[index.html<br/>served by GET /]
    APP[app_jwt.py]
    SBCJ[starburst_client_jwt.py]
    HO[_HeadlessOAuth]
    TC[token_cache.py<br/>NOT imported by app_jwt]
    DOTENV[.env]
    TRINOLIB[trino.dbapi + trino.auth]
    REQS[requests]
    OPX[openpyxl]
    FAPI[fastapi + pydantic]
    OAUTH[OAuth2Authentication]

    APP -->|static file| IDX
    APP -->|import StarburstClientJWT| SBCJ
    APP -->|FastAPI, HTTPException,<br/>CORS, StaticFiles| FAPI
    APP -->|Workbook| OPX
    SBCJ --> HO
    SBCJ -->|connect| TRINOLIB
    SBCJ -->|OAuth2Authentication| OAUTH
    HO -->|HTTP login + redirect| REQS
    SBCJ -->|load_dotenv| DOTENV
    TC -. standalone .-> TRINOLIB
    TC -. standalone .-> REQS
```

---

## 9. Data / State Inventory

| Name | Location | Lifetime | Thread safety | Invalidation |
|---|---|---|---|---|
| `_schema_cache` | module-global dict in `app_jwt.py:310` | Process lifetime | Not locked; read/write are atomic dict ops; pre-warmed on startup in a daemon thread ([`app_jwt.py:513-520`](../gen%20ai%20project/starburst-mcp2/app_jwt.py#L513-L520)) | TTL 300 s or `/api/schema?refresh=1` |
| Trino connection | `StarburstClientJWT._conn` instance attr | Process lifetime, reused | **Not thread-safe.** FastAPI routes are async but the Trino cursor is sync; under concurrent requests a single shared cursor can corrupt results. See [Extension Points](#10-extension-points) | Reset to `None` on any `execute()` exception or `SELECT 1` liveness failure |
| OAuth token | Inside Trino `OAuth2Authentication` object | Matches connection lifetime | Managed by Trino client | Auto-refresh by Trino client when token nears expiry |
| Disk token cache | `token_cache.json` (only via `token_cache.py`, not `app_jwt.py`) | Cross-restart | Single writer | Checks `expires_at` with 60 s buffer; `save_token` rewrites |
| FastAPI `app` state | Module global | Process lifetime | Managed by FastAPI/Uvicorn workers | N/A |
| Static file mount `/static` | Conditional on `static/` folder existing at import ([`app_jwt.py:37-40`](../gen%20ai%20project/starburst-mcp2/app_jwt.py#L37-L40)) | Process lifetime | Read-only | N/A |
| Startup banner + cache warm | `@app.on_event("startup")` ([`app_jwt.py:503`](../gen%20ai%20project/starburst-mcp2/app_jwt.py#L503)) | Once per process | `threading.Thread(daemon=True)` | N/A |

---

## 10. Extension Points

- **LLM-backed NL to SQL.** Current engine is pure regex ([`_nl_to_sql`](../gen%20ai%20project/starburst-mcp2/app_jwt.py#L193)). Swap by injecting a function with signature `(message, catalog, schema) -> str | None` that calls an LLM with the schema cache as grounding context. Keep the regex path as a fast fallback.
- **Connection pooling / thread safety.** Replace the single shared `_conn` with a per-request connection or a bounded pool (`queue.Queue` of `StarburstClientJWT` instances) to avoid cursor contention under load.
- **New auth providers.** `StarburstClientJWT._get_auth` returns `OAuth2Authentication()`; parameterize to accept `BasicAuthentication`, true JWT bearer, or SAML, selected via `.env`.
- **New export formats.** Extend `/api/export/{fmt}` ([`app_jwt.py:442`](../gen%20ai%20project/starburst-mcp2/app_jwt.py#L442)) — add `parquet` via pyarrow, `json` trivially, or `markdown` for LLM hand-off.
- **Multi-tenant permissions.** Port `permission_manager.py` (currently MCP-only) into `app_jwt.py`: resolve developer from a header/JWT claim, gate `_exec` by permission flag.
- **Observability.** Add a FastAPI middleware to emit structured logs + Prometheus metrics (query count, latency, NL-match rate, TABLE_NOT_FOUND fallback rate).
- **Streaming results.** For large result sets, switch `/api/chat` to a WebSocket or SSE stream that yields rows as Trino delivers them.

---

## Deliverables Summary

1. **File written:** `docs/FLOW.md`
2. **Mermaid diagrams produced: 6** — architecture (`graph TB`), request lifecycle (`sequenceDiagram`), auth flow (`sequenceDiagram`), NL-to-SQL decision (`flowchart TD`), error fallback (`flowchart TD`), module dependency (`graph LR`).
3. **Deviations between optimized spec and actual code:**
   - **Auth is not OAuth2 client-credentials.** It is the standard **OAuth2 authorization-code flow** with `webbrowser.open` monkey-patched so `_HeadlessOAuth` replays the Galaxy portal login + redirect endpoint instead of opening a browser. Documented accurately in §5.
   - **`token_cache.py` is NOT wired into `app_jwt.py`.** The spec implied it was a direct collaborator; in reality it is a standalone script / CLI. Noted in §5 and §8.
   - **Latent bug at [`app_jwt.py:525`](../gen%20ai%20project/starburst-mcp2/app_jwt.py#L525):** `uvicorn.run("app:app", ...)` references module `app`, not `app_jwt`. Running `python app_jwt.py` directly loads the wrong module. Recommended fix: `uvicorn.run("app_jwt:app", ...)`, or launch via `python -m uvicorn app_jwt:app --port 8000` (as the README instructs).
   - **Schema cache is pre-warmed** on startup in a background daemon thread — worth calling out for operators (§9).
4. **Sensitive values masked:**
   - Galaxy tenant host (category: `<TENANT>.galaxy.starburst.io`) — abstracted in all diagrams/examples; real value only lives in `.env` (gitignored).
   - Email / password credentials — referenced as `email`, `password` parameters; never shown.
   - Catalog / schema names — shown as `cat.sch` / `<CAT>.<SCH>` placeholders in examples.
   - No real identifiers from `permissions.yaml` appear in this document.
