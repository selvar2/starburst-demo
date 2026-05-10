"""Schema metadata context for LLM prompting and validation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SchemaContext:
    text: str
    tables: dict[tuple[str, str, str], set[str]]


def build_schema_context(
    schema_data: dict | None,
    catalog: str,
    default_schema: str,
    max_tables: int = 80,
) -> SchemaContext:
    schema_data = schema_data or {}
    tables: dict[tuple[str, str, str], set[str]] = {}
    lines = [
        f"Default catalog: {catalog}",
        f"Default schema: {default_schema}",
        "Available tables:",
    ]

    count = 0
    for schema in schema_data.get("schemas", []):
        schema_name = schema.get("name")
        if not schema_name:
            continue
        for table in schema.get("tables", []):
            table_name = table.get("name")
            if not table_name:
                continue
            columns = table.get("columns", [])
            col_parts = []
            col_names: set[str] = set()
            for col in columns:
                name = str(col.get("name", "")).strip()
                if not name:
                    continue
                typ = str(col.get("type", "unknown")).strip() or "unknown"
                col_names.add(name.lower())
                col_parts.append(f"{name} {typ}")
            key = (catalog.lower(), schema_name.lower(), table_name.lower())
            tables[key] = col_names
            lines.append(f"- {catalog}.{schema_name}.{table_name}: {', '.join(col_parts) if col_parts else 'columns unknown'}")
            count += 1
            if count >= max_tables:
                lines.append(f"- Metadata truncated after {max_tables} tables.")
                return SchemaContext(text="\n".join(lines), tables=tables)

    if count == 0:
        lines.append("- No schema metadata loaded yet.")
    return SchemaContext(text="\n".join(lines), tables=tables)
