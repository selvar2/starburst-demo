# ============================================================================
# BACKUP: app_jwt.py
# Timestamp:  2026-05-09T15:19:37Z (TS=20260509_204843)
# Source:     gen-ai-project/starburst-mcp2/app_jwt.py
# Branch:     dev3 @ commit db6bb19
# Why:        Adding NL-driven DDL/DML support to /api/chat. Original file
#             only handled SELECT/SHOW/DESCRIBE. Backing up before adding
#             permission checks, FQ-name validation, destructive-op confirm
#             guard, and INSERT/UPDATE/DELETE/TRUNCATE/DROP/CREATE-SCHEMA
#             NL patterns.
# Before:     ~/api/chat~ executes SQL via client.execute with no guardrails.
# After:      Same endpoint validates fully-qualified target, checks
#             permissions via PermissionManager, requires context.confirm
#             for destructive ops.
# Restore:    cp 'gen-ai-project/starburst-mcp2/backup/app_jwt.20260509_204843.bak.py' gen-ai-project/starburst-mcp2/app_jwt.py
# ============================================================================

# Additional dependencies: fastapi, uvicorn[standard], openpyxl, python-multipart

import io
import csv
import re
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from starburst_client_jwt import StarburstClientJWT as StarburstClient

# ---------------------------------------------------------------------------
# App & client
# ---------------------------------------------------------------------------

app = FastAPI(title="Starburst Galaxy Chatbot (JWT)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = StarburstClient()

HERE = Path(__file__).parent

# Static files (best-effort; directory may not exist yet)
static_dir = HERE / "static"
if static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    sql: str

class ChatRequest(BaseModel):
    message: str
    context: dict | None = None

class ExportRequest(BaseModel):
    columns: list[str]
    rows: list[list]
    title: str = "export"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _catalog(ctx: dict | None) -> str:
    return (ctx or {}).get("catalog") or client.catalog or "mcp2ohio"

def _schema(ctx: dict | None) -> str:
    return (ctx or {}).get("schema") or client.schema or "test_writes"

class QueryError(Exception):
    pass

_AGG_ALIAS_RE = re.compile(
    r'\b(COUNT|SUM|AVG|MIN|MAX)\s*\(\s*(\*|\w+)\s*\)(?!\s+AS\b)',
    re.IGNORECASE,
)

def _add_agg_aliases(sql: str) -> str:
    """Add aliases to aggregate functions that don't have one."""
    def _repl(m):
        func = m.group(1).lower()
        col = m.group(2)
        if col == '*':
            alias = f"{func}"
        else:
            alias = f"{func}_{col}"
        return f'{m.group(0)} AS {alias}'
    return _AGG_ALIAS_RE.sub(_repl, sql)

def _exec(sql: str) -> dict:
    """Execute and normalise result."""
    try:
        result = client.execute(_add_agg_aliases(sql))
    except Exception as exc:
        raise QueryError(str(exc))
    columns = result.get("columns", [])
    rows = result.get("rows", [])
    return {"columns": columns, "rows": rows, "row_count": len(rows)}


# ---------------------------------------------------------------------------
# Chart suggestion
# ---------------------------------------------------------------------------

_DATE_KEYWORDS = {"date", "time", "timestamp", "day", "month", "year", "created", "updated"}

def _suggest_chart(columns: list[str], rows: list[list]) -> str:
    if not columns or not rows:
        return "table"

    ncols = len(columns)

    # Single scalar value
    if ncols == 1 and len(rows) == 1:
        return "metric"

    # Check for date column
    lower_cols = [c.lower() for c in columns]
    has_date = any(any(kw in c for kw in _DATE_KEYWORDS) for c in lower_cols)
    if has_date and ncols >= 2:
        return "line"

    # 2 columns: any type + number (group by results)
    if ncols == 2 and rows:
        second_num = isinstance(rows[0][1], (int, float)) if rows[0] else False
        if second_num:
            return "pie" if len(rows) < 8 else "bar"

    # Aggregation (single row, multiple numeric cols)
    if len(rows) == 1 and ncols >= 1:
        if all(isinstance(v, (int, float)) for v in rows[0]):
            return "bar"

    # Multiple rows with at least one numeric column
    if ncols >= 2 and len(rows) > 1:
        has_num = any(isinstance(rows[0][i], (int, float)) for i in range(ncols))
        if has_num:
            return "bar"

    return "table"


# ---------------------------------------------------------------------------
# NL -> SQL
# ---------------------------------------------------------------------------

_SQL_START = re.compile(
    r"^\s*(SELECT|SHOW|DESCRIBE|WITH|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\b",
    re.IGNORECASE,
)

def _extract_context(text: str, default_catalog: str, default_schema: str):
    """Extract catalog, schema, table from NL text with context hints."""
    low = text.lower()
    cat = default_catalog
    sch = default_schema

    # Match: "X is part of Y schema and part of Z catalog"
    m = re.search(r'part of\s+(\w+)\s+schema', low)
    if m:
        sch = m.group(1)
    m = re.search(r'part of\s+(\w+)\s+catalog', low)
    if m:
        cat = m.group(1)

    # Match: "from/in Y schema in/of Z catalog"
    m = re.search(r'(?:from|in)\s+(\w+)\s+schema\s+(?:in|of)\s+(\w+)\s+catalog', low)
    if m:
        sch = m.group(1)
        cat = m.group(2)

    # Match: "in Y schema" alone
    m = re.search(r'in\s+(\w+)\s+schema', low)
    if m:
        sch = m.group(1)

    # Match: "in Z catalog" alone
    m = re.search(r'in\s+(\w+)\s+catalog', low)
    if m:
        cat = m.group(1)

    return cat, sch


def _clean_nl(text: str) -> str:
    """Remove context hints from NL text to get core query."""
    cleaned = re.sub(r',?\s*\w+\s+is\s+part\s+of\s+\w+\s+schema\s+and\s+part\s+of\s+\w+\s+catalog\s*', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r',?\s*(?:from|in)\s+\w+\s+schema\s+(?:in|of)\s+\w+\s+catalog\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r',?\s*in\s+\w+\s+(?:schema|catalog)\s*', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _nl_to_sql(message: str, catalog: str, schema: str) -> str | None:
    """Return SQL string or None if no pattern matched and not raw SQL."""
    msg = message.strip()
    low = msg.lower()

    # Extract catalog/schema from NL context hints
    catalog, schema = _extract_context(low, catalog, schema)
    fq = f"{catalog}.{schema}"

    # Clean context hints from message for pattern matching
    clean = _clean_nl(low)

    # Exact NL matches first (before raw SQL check)
    if clean in ("show tables", "list tables", "tables", "show all tables", "list all tables"):
        return f"SHOW TABLES FROM {fq}"

    if clean in ("show schemas", "list schemas", "schemas", "show all schemas"):
        return f"SHOW SCHEMAS FROM {catalog}"

    # Raw SQL passthrough — if it contains dots (qualified names), treat as SQL
    if _SQL_START.match(msg) and '.' in msg:
        return msg

    # describe / show columns
    m = re.match(r"(?:describe|show columns of|columns of)\s+(\w+)", clean)
    if m:
        return f"DESCRIBE {fq}.{m.group(1)}"

    # show all data / select from
    m = re.match(r"(?:show all data from|show data from|select from|show me data from|show me)\s+(\w+)", clean)
    if m:
        return f"SELECT * FROM {fq}.{m.group(1)} LIMIT 100"

    # count rows
    m = re.match(r"count (?:rows in|rows from|from|of)\s+(\w+)", clean)
    if m:
        return f"SELECT COUNT(*) FROM {fq}.{m.group(1)}"

    # top N column from table
    m = re.match(r"top\s+(\d+)\s+(\w+)\s+from\s+(\w+)", clean)
    if m:
        n, col, tbl = m.group(1), m.group(2), m.group(3)
        return f"SELECT * FROM {fq}.{tbl} ORDER BY {col} DESC LIMIT {n}"

    # aggregation: sum/avg/min/max of column from table
    m = re.match(r"(sum|avg|min|max|average)\s+(?:of\s+)?(\w+)\s+from\s+(\w+)", clean)
    if m:
        agg = m.group(1).upper()
        if agg == "AVERAGE":
            agg = "AVG"
        col, tbl = m.group(2), m.group(3)
        return f"SELECT {agg}({col}) FROM {fq}.{tbl}"

    # group by column from table
    m = re.match(r"group\s+by\s+(\w+)\s+(?:from|in)\s+(\w+)", clean)
    if m:
        col, tbl = m.group(1), m.group(2)
        return f"SELECT {col}, COUNT(*) FROM {fq}.{tbl} GROUP BY {col}"

    # Fallback: raw SQL without dots
    if _SQL_START.match(msg):
        return msg

    return None


# ---------------------------------------------------------------------------
def _try_other_schemas(message: str, failed_sql: str, catalog: str, default_schema: str):
    """When a table isn't found in the default schema, search cached schema data."""
    m = re.search(r'FROM\s+\S+\.(\w+)\.(\w+)', failed_sql, re.IGNORECASE)
    if not m:
        return None
    table_name = m.group(2).lower()

    # Use cached schema to avoid slow Starburst round-trips
    cached = _schema_cache.get("data")
    if cached and cached.get("schemas"):
        for s in cached["schemas"]:
            if s["name"] == default_schema or s["name"] == "information_schema":
                continue
            for t in s.get("tables", []):
                if t["name"].lower() == table_name:
                    return failed_sql.replace(
                        f"{catalog}.{default_schema}.{m.group(2)}",
                        f"{catalog}.{s['name']}.{t['name']}"
                    )

    # Fallback: single direct query if cache is empty
    try:
        result = client.execute(
            f"SELECT table_schema, table_name FROM {catalog}.information_schema.tables "
            f"WHERE table_name = '{table_name}' AND table_schema != '{default_schema}' LIMIT 1"
        )
        if result.get("rows"):
            found_schema = result["rows"][0][0]
            found_table = result["rows"][0][1]
            return failed_sql.replace(
                f"{catalog}.{default_schema}.{m.group(2)}",
                f"{catalog}.{found_schema}.{found_table}"
            )
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
async def index():
    index_file = HERE / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(str(index_file))


_schema_cache: dict = {"data": None, "ts": 0}
_SCHEMA_TTL = 300  # 5 minutes

def _describe_table(catalog: str, schema_name: str, table_name: str) -> dict:
    """Fetch columns for one table. Runs in a thread."""
    columns = []
    try:
        col_result = client.execute(f"DESCRIBE {catalog}.{schema_name}.{table_name}")
        for crow in col_result.get("rows", []):
            columns.append({"name": crow[0], "type": crow[1] if len(crow) > 1 else "unknown"})
    except Exception:
        pass
    return {"name": table_name, "columns": columns}


def _fetch_schema():
    catalog = client.catalog or "mcp2ohio"

    # Step 1: Get all schemas
    schema_result = client.execute(f"SHOW SCHEMAS FROM {catalog}")
    schema_names = [row[0] for row in schema_result.get("rows", [])]

    # Step 2: Get all tables for all schemas in parallel
    schema_tables = {}
    with ThreadPoolExecutor(max_workers=len(schema_names)) as pool:
        def get_tables(s):
            try:
                r = client.execute(f"SHOW TABLES FROM {catalog}.{s}")
                return s, [row[0] for row in r.get("rows", [])]
            except Exception:
                return s, []
        futures = [pool.submit(get_tables, s) for s in schema_names]
        for f in as_completed(futures):
            name, tables = f.result()
            schema_tables[name] = tables

    # Step 3: Describe ALL tables across ALL schemas in parallel
    all_tasks = []
    for schema_name, table_names in schema_tables.items():
        for table_name in table_names:
            all_tasks.append((schema_name, table_name))

    table_data = {}  # (schema, table) -> {name, columns}
    with ThreadPoolExecutor(max_workers=min(len(all_tasks), 10)) as pool:
        futures = {
            pool.submit(_describe_table, catalog, s, t): (s, t)
            for s, t in all_tasks
        }
        for f in as_completed(futures):
            s, t = futures[f]
            table_data[(s, t)] = f.result()

    # Step 4: Assemble result
    schemas = []
    for schema_name in sorted(schema_tables.keys()):
        tables = [table_data[(schema_name, t)] for t in schema_tables[schema_name]]
        schemas.append({"name": schema_name, "tables": tables})
    return {"schemas": schemas}

@app.get("/api/schema")
async def get_schema(refresh: int = 0):
    try:
        now = time.time()
        if not refresh and _schema_cache["data"] and (now - _schema_cache["ts"]) < _SCHEMA_TTL:
            return _schema_cache["data"]
        result = _fetch_schema()
        _schema_cache["data"] = result
        _schema_cache["ts"] = now
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/query")
async def run_query(req: QueryRequest):
    try:
        return _exec(req.sql)
    except QueryError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/chat")
async def chat(req: ChatRequest):
    catalog = _catalog(req.context)
    schema = _schema(req.context)

    sql = _nl_to_sql(req.message, catalog, schema)
    if sql is None:
        return {
            "sql": None,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "chart_suggestion": "table",
            "message": (
                "I couldn't understand that query. Try phrases like:\n"
                "- show tables\n"
                "- describe <table>\n"
                "- show all data from <table>\n"
                "- count rows in <table>\n"
                "- top 10 <column> from <table>\n"
                "- sum/avg/min/max of <column> from <table>\n"
                "- group by <column> from <table>\n"
                "- Or enter raw SQL directly."
            ),
        }

    try:
        result = _exec(sql)
    except QueryError as exc:
        err_str = str(exc)
        if "TABLE_NOT_FOUND" in err_str or "does not exist" in err_str:
            alt_sql = _try_other_schemas(req.message, sql, catalog, schema)
            if alt_sql:
                sql = alt_sql
                result = _exec(sql)
            else:
                raise HTTPException(status_code=400, detail=err_str)
        else:
            raise HTTPException(status_code=400, detail=err_str)

    chart = _suggest_chart(result["columns"], result["rows"])
    return {
        "sql": sql,
        "columns": result["columns"],
        "rows": result["rows"],
        "row_count": result["row_count"],
        "chart_suggestion": chart,
        "message": f"Executed: {sql}",
    }


@app.post("/api/export/{fmt}")
async def export_data(fmt: str, req: ExportRequest):
    if fmt not in ("csv", "xlsx", "html"):
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")

    safe_title = re.sub(r"[^\w\-]", "_", req.title)

    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(req.columns)
        writer.writerows(req.rows)
        return Response(
            content=buf.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.csv"'},
        )

    if fmt == "xlsx":
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = req.title[:31]
        ws.append(req.columns)
        for row in req.rows:
            ws.append(row)
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.xlsx"'},
        )

    # html
    rows_html = "".join(
        "<tr>" + "".join(f"<td>{v}</td>" for v in row) + "</tr>" for row in req.rows
    )
    header_html = "".join(f"<th>{c}</th>" for c in req.columns)
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<title>{req.title}</title>"
        "<style>table{border-collapse:collapse;width:100%}"
        "th,td{border:1px solid #ccc;padding:8px;text-align:left}"
        "th{background:#f5f5f5}</style></head><body>"
        f"<h2>{req.title}</h2>"
        f"<table><thead><tr>{header_html}</tr></thead>"
        f"<tbody>{rows_html}</tbody></table></body></html>"
    )
    return Response(
        content=html,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{safe_title}.html"'},
    )


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_banner():
    print("=" * 60)
    print("  Starburst Galaxy Chatbot")
    print(f"  Host:    {client.host}")
    print(f"  Catalog: {client.catalog}")
    print(f"  Schema:  {client.schema}")
    print(f"  Auth:    {client.auth_mode}")
    print("=" * 60)
    # Pre-warm schema cache in background thread (non-blocking)
    def _warm():
        try:
            _schema_cache["data"] = _fetch_schema()
            _schema_cache["ts"] = time.time()
            print("  Schema cache warmed ✓")
        except Exception as e:
            print(f"  Schema cache warm failed: {e}")
    threading.Thread(target=_warm, daemon=True).start()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
