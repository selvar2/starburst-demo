"""Safety validation for LLM-generated SQL."""

from __future__ import annotations

import re
from dataclasses import dataclass

from metadata_service import SchemaContext


class SQLValidationError(ValueError):
    pass


@dataclass(frozen=True)
class SQLValidationResult:
    sql: str
    warnings: list[str]


_READ_START = re.compile(r"^\s*(SELECT|WITH|SHOW|DESCRIBE)\b", re.IGNORECASE)
_BLOCKED_START = re.compile(
    r"^\s*(INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TRUNCATE|MERGE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)
_LIMIT_RE = re.compile(r"\bLIMIT\s+\d+\b", re.IGNORECASE)
_TABLE_REF_RE = re.compile(r"\b(?:FROM|JOIN)\s+([a-zA-Z_]\w*)\.([a-zA-Z_]\w*)\.([a-zA-Z_]\w*)", re.IGNORECASE)
_FROM_RE = re.compile(r"\bFROM\b", re.IGNORECASE)
_SIMPLE_SELECT_RE = re.compile(
    r"^\s*SELECT\s+(.+?)\s+FROM\s+([a-zA-Z_]\w*)\.([a-zA-Z_]\w*)\.([a-zA-Z_]\w*)\b",
    re.IGNORECASE | re.DOTALL,
)


def validate_generated_sql(
    sql: str,
    schema_context: SchemaContext | None,
    default_limit: int = 100,
    allow_write: bool = False,
) -> SQLValidationResult:
    cleaned = sql.strip().rstrip(";")
    if not cleaned:
        raise SQLValidationError("Generated SQL is empty.")
    if ";" in cleaned:
        raise SQLValidationError("Generated SQL must be a single statement.")
    if "--" in cleaned or "/*" in cleaned or "*/" in cleaned:
        raise SQLValidationError("Generated SQL must not contain comments.")
    if _BLOCKED_START.match(cleaned) and not allow_write:
        raise SQLValidationError("Generated business-user SQL is restricted to read-only statements.")
    if not _READ_START.match(cleaned) and not allow_write:
        raise SQLValidationError("Generated SQL must start with SELECT, WITH, SHOW, or DESCRIBE.")
    if cleaned.upper().startswith(("SELECT", "WITH")) and not _FROM_RE.search(cleaned):
        raise SQLValidationError("Generated SQL must query approved enterprise tables, not return literal answers.")

    warnings: list[str] = []
    if schema_context and schema_context.tables:
        for cat, sch, tbl in _TABLE_REF_RE.findall(cleaned):
            key = (cat.lower(), sch.lower(), tbl.lower())
            if key not in schema_context.tables:
                raise SQLValidationError(f"Generated SQL references unknown table: {cat}.{sch}.{tbl}")
        _validate_simple_selected_columns(cleaned, schema_context)

    if cleaned.upper().startswith(("SELECT", "WITH")) and not _LIMIT_RE.search(cleaned):
        cleaned = f"{cleaned} LIMIT {default_limit}"
        warnings.append(f"Added LIMIT {default_limit} to generated SQL.")

    return SQLValidationResult(sql=cleaned, warnings=warnings)


def _validate_simple_selected_columns(sql: str, schema_context: SchemaContext) -> None:
    match = _SIMPLE_SELECT_RE.match(sql)
    if not match:
        return
    select_part, cat, sch, tbl = match.groups()
    key = (cat.lower(), sch.lower(), tbl.lower())
    known = schema_context.tables.get(key)
    if not known:
        return
    for expr in _split_select_expressions(select_part):
        col = _extract_column_name(expr)
        if col and col.lower() not in known:
            raise SQLValidationError(f"Generated SQL references unknown column: {col}")


def _split_select_expressions(select_part: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    for ch in select_part:
        if ch == "(":
            depth += 1
        elif ch == ")" and depth:
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    return parts


def _extract_column_name(expr: str) -> str | None:
    cleaned = re.sub(r"\s+AS\s+\w+\s*$", "", expr.strip(), flags=re.IGNORECASE)
    if cleaned == "*":
        return None
    func = re.match(r"\w+\s*\(\s*([a-zA-Z_]\w*|\*)\s*\)", cleaned)
    if func:
        inner = func.group(1)
        return None if inner == "*" else inner
    if re.match(r"^[a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)?$", cleaned):
        return cleaned.split(".")[-1]
    return None
