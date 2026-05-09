"""Read-only MCP tools for Starburst Galaxy.

Tools: execute_query, list_catalogs, show_schemas, show_tables, describe_table
"""

from mcp.server.fastmcp import FastMCP
from starburst_client import StarburstClient
from permission_manager import PermissionManager


def register_read_tools(mcp: FastMCP, client: StarburstClient, perms: PermissionManager, developer: str):

    @mcp.tool()
    def execute_query(query: str, read_only: bool = False) -> str:
        """Execute any SQL query on Starburst Galaxy.

        Args:
            query: SQL query to execute (Trino/ANSI SQL)
            read_only: If true, only SELECT/SHOW/DESCRIBE/EXPLAIN are allowed
        """
        upper = query.strip().upper()
        is_read = upper.startswith(("SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "WITH"))

        if read_only and not is_read:
            return "Error: read_only=true but query is not a read operation."

        if not is_read:
            allowed, msg = perms.check_with_message(developer, "execute_raw")
            if not allowed:
                return f"Error: {msg}"

        try:
            result = client.execute(query)
            return _format_result(result)
        except Exception as e:
            return f"Error executing query: {e}"

    @mcp.tool()
    def list_catalogs() -> str:
        """List all available catalogs in Starburst Galaxy."""
        try:
            result = client.execute("SHOW CATALOGS")
            return _format_result(result)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def show_schemas(catalog: str) -> str:
        """Show all schemas in a catalog.

        Args:
            catalog: Catalog name (e.g., 'mcp2ohio', 'sample')
        """
        try:
            StarburstClient.validate_identifier(catalog)
            result = client.execute(f'SHOW SCHEMAS FROM "{catalog}"')
            return _format_result(result)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def show_tables(catalog: str, schema: str) -> str:
        """Show all tables in a schema.

        Args:
            catalog: Catalog name
            schema: Schema name
        """
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            fqn = StarburstClient.qualified_name(catalog, schema)
            result = client.execute(f"SHOW TABLES FROM {fqn}")
            return _format_result(result)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def describe_table(catalog: str, schema: str, table: str) -> str:
        """Describe a table's columns and types.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
        """
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            StarburstClient.validate_identifier(table)
            fqn = StarburstClient.qualified_name(catalog, schema, table)
            result = client.execute(f"DESCRIBE {fqn}")
            return _format_result(result)
        except Exception as e:
            return f"Error: {e}"


def _format_result(result: dict) -> str:
    """Format query result as a readable string."""
    if "columns" in result:
        columns = result["columns"]
        rows = result["rows"]
        if not rows:
            return "No rows returned."
        str_rows = [[str(v) if v is not None else "NULL" for v in row] for row in rows]
        widths = [
            max(len(c), max((len(r[i]) for r in str_rows), default=0))
            for i, c in enumerate(columns)
        ]
        header = " | ".join(c.ljust(w) for c, w in zip(columns, widths))
        sep = "-+-".join("-" * w for w in widths)
        lines = [header, sep]
        for row in str_rows:
            lines.append(" | ".join(v.ljust(w) for v, w in zip(row, widths)))
        return f"{len(rows)} row(s) returned.\n\n" + "\n".join(lines)
    if "rows_affected" in result:
        return f"OK. Rows affected: {result['rows_affected']}"
    return str(result)
