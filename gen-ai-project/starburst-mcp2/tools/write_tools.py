"""Write MCP tools for Starburst Galaxy.

DDL: create_schema, create_table, drop_table, drop_schema, truncate_table
DML: insert_data, update_data, delete_data, merge_data

All tools check permissions before execution.
Dangerous operations (drop, truncate) require confirm=true.
"""

import json
from mcp.server.fastmcp import FastMCP
from starburst_client import StarburstClient
from permission_manager import PermissionManager


def register_write_tools(mcp: FastMCP, client: StarburstClient, perms: PermissionManager, developer: str):

    def _check(operation: str) -> str | None:
        allowed, msg = perms.check_with_message(developer, operation)
        if not allowed:
            return f"Error: {msg}"
        return None

    def _confirm_guard(operation: str, target: str, confirm: bool) -> str | None:
        if not confirm:
            return (
                f"WARNING: This will {operation} '{target}'. "
                f"This action cannot be undone. "
                f"Pass confirm=true to proceed."
            )
        return None

    @mcp.tool()
    def create_schema(catalog: str, schema: str) -> str:
        """Create a new schema in a catalog.

        Args:
            catalog: Catalog name (e.g., 'mcp2ohio')
            schema: New schema name
        """
        if err := _check("create_schema"):
            return err
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            fqn = StarburstClient.qualified_name(catalog, schema)
            client.execute(f"CREATE SCHEMA {fqn}")
            return f"Schema {fqn} created successfully."
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def create_table(catalog: str, schema: str, table: str, columns: str) -> str:
        """Create a new table.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: New table name
            columns: JSON array of columns, e.g. [{"name": "id", "type": "INTEGER"}, {"name": "val", "type": "VARCHAR"}]
        """
        if err := _check("create_table"):
            return err
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            StarburstClient.validate_identifier(table)
            col_list = json.loads(columns) if isinstance(columns, str) else columns
            col_defs = ", ".join(f'"{c["name"]}" {c["type"]}' for c in col_list)
            fqn = StarburstClient.qualified_name(catalog, schema, table)
            client.execute(f"CREATE TABLE {fqn} ({col_defs})")
            return f"Table {fqn} created successfully with {len(col_list)} column(s)."
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def drop_table(catalog: str, schema: str, table: str, confirm: bool = False) -> str:
        """Drop (delete) a table permanently.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table to drop
            confirm: Must be true to execute. Safety guard for destructive operation.
        """
        if err := _check("drop_table"):
            return err
        fqn = StarburstClient.qualified_name(catalog, schema, table)
        if warn := _confirm_guard("DROP TABLE", fqn, confirm):
            return warn
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            StarburstClient.validate_identifier(table)
            client.execute(f"DROP TABLE {fqn}")
            return f"Table {fqn} dropped successfully."
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def drop_schema(catalog: str, schema: str, confirm: bool = False) -> str:
        """Drop (delete) a schema permanently.

        Args:
            catalog: Catalog name
            schema: Schema to drop
            confirm: Must be true to execute. Safety guard for destructive operation.
        """
        if err := _check("drop_schema"):
            return err
        fqn = StarburstClient.qualified_name(catalog, schema)
        if warn := _confirm_guard("DROP SCHEMA", fqn, confirm):
            return warn
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            client.execute(f"DROP SCHEMA {fqn}")
            return f"Schema {fqn} dropped successfully."
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def truncate_table(catalog: str, schema: str, table: str, confirm: bool = False) -> str:
        """Truncate (remove all rows from) a table. Table structure is preserved.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table to truncate
            confirm: Must be true to execute. Safety guard for destructive operation.
        """
        if err := _check("truncate"):
            return err
        fqn = StarburstClient.qualified_name(catalog, schema, table)
        if warn := _confirm_guard("TRUNCATE TABLE", fqn, confirm):
            return warn
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            StarburstClient.validate_identifier(table)
            client.execute(f"TRUNCATE TABLE {fqn}")
            return f"Table {fqn} truncated successfully."
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def insert_data(catalog: str, schema: str, table: str, rows: str) -> str:
        """Insert rows into a table.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
            rows: JSON array of row objects, e.g. [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        """
        if err := _check("insert"):
            return err
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            StarburstClient.validate_identifier(table)
            row_list = json.loads(rows) if isinstance(rows, str) else rows
            if not row_list:
                return "Error: No rows provided."
            columns = list(row_list[0].keys())
            col_str = ", ".join(f'"{c}"' for c in columns)
            value_rows = []
            for row in row_list:
                vals = []
                for c in columns:
                    v = row.get(c)
                    if v is None:
                        vals.append("NULL")
                    elif isinstance(v, str):
                        vals.append(f"'{v}'")
                    else:
                        vals.append(str(v))
                value_rows.append(f"({', '.join(vals)})")
            values_str = ", ".join(value_rows)
            fqn = StarburstClient.qualified_name(catalog, schema, table)
            sql = f"INSERT INTO {fqn} ({col_str}) VALUES {values_str}"
            result = client.execute(sql)
            affected = result.get("rows_affected", len(row_list))
            return f"Inserted {affected} row(s) into {fqn}."
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def update_data(catalog: str, schema: str, table: str, set_values: str, where: str) -> str:
        """Update rows in a table.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
            set_values: JSON object of column=value pairs, e.g. {"amount": 100, "status": "active"}
            where: WHERE clause (without the WHERE keyword), e.g. "id = 1"
        """
        if err := _check("update"):
            return err
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            StarburstClient.validate_identifier(table)
            vals = json.loads(set_values) if isinstance(set_values, str) else set_values
            set_parts = []
            for col, val in vals.items():
                if val is None:
                    set_parts.append(f'"{col}" = NULL')
                elif isinstance(val, str):
                    set_parts.append(f'"{col}" = \'{val}\'')
                else:
                    set_parts.append(f'"{col}" = {val}')
            set_str = ", ".join(set_parts)
            fqn = StarburstClient.qualified_name(catalog, schema, table)
            sql = f"UPDATE {fqn} SET {set_str} WHERE {where}"
            result = client.execute(sql)
            affected = result.get("rows_affected", 0)
            return f"Updated {affected} row(s) in {fqn}."
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def delete_data(catalog: str, schema: str, table: str, where: str) -> str:
        """Delete rows from a table.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
            where: WHERE clause (without the WHERE keyword), e.g. "id = 1"
        """
        if err := _check("delete"):
            return err
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            StarburstClient.validate_identifier(table)
            fqn = StarburstClient.qualified_name(catalog, schema, table)
            sql = f"DELETE FROM {fqn} WHERE {where}"
            result = client.execute(sql)
            affected = result.get("rows_affected", 0)
            return f"Deleted {affected} row(s) from {fqn}."
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def merge_data(catalog: str, schema: str, table: str, source_query: str, on_condition: str, when_matched: str, when_not_matched: str) -> str:
        """Merge (upsert) data into a table from a source query.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Target table name
            source_query: SELECT query providing source rows
            on_condition: Join condition, e.g. "target.id = source.id"
            when_matched: Action when matched, e.g. "UPDATE SET target.val = source.val"
            when_not_matched: Action when not matched, e.g. "INSERT (id, val) VALUES (source.id, source.val)"
        """
        if err := _check("merge"):
            return err
        try:
            StarburstClient.validate_identifier(catalog)
            StarburstClient.validate_identifier(schema)
            StarburstClient.validate_identifier(table)
            fqn = StarburstClient.qualified_name(catalog, schema, table)
            sql = (
                f"MERGE INTO {fqn} AS target "
                f"USING ({source_query}) AS source "
                f"ON {on_condition} "
                f"WHEN MATCHED THEN {when_matched} "
                f"WHEN NOT MATCHED THEN {when_not_matched}"
            )
            result = client.execute(sql)
            affected = result.get("rows_affected", 0)
            return f"Merge completed on {fqn}. Rows affected: {affected}"
        except Exception as e:
            return f"Error: {e}"
