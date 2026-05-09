"""Starburst Read-Write MCP Server.

A custom MCP server providing full read+write access to Starburst Galaxy
via Trino DBAPI. Supports OAuth2 authentication and per-developer permissions.

Usage (stdio):
    python server.py

Register in ~/.claude/settings.json:
    "starburst-rw": {
        "type": "stdio",
        "command": "python",
        "args": ["c:/Users/Lenovo/gen-ai-project/starburst-mcp2/server.py"]
    }
"""

import os
import sys
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from starburst_client import StarburstClient
from permission_manager import PermissionManager
from tools import register_read_tools, register_write_tools

# Initialize
client = StarburstClient()
perms = PermissionManager()
developer = os.getenv("STARBURST_DEVELOPER", "unknown")

mcp = FastMCP(
    name="starburst-rw",
    instructions=(
        "Starburst Galaxy Read-Write MCP Server. "
        "Provides full SQL access including SELECT, INSERT, UPDATE, DELETE, "
        "CREATE, DROP, TRUNCATE, and MERGE operations. "
        f"Connected to: {client.host} | Catalog: {client.catalog} | "
        f"Developer: {developer} | Auth: {client.auth_mode}"
    ),
)

# Register all tools
register_read_tools(mcp, client, perms, developer)
register_write_tools(mcp, client, perms, developer)

if __name__ == "__main__":
    mcp.run(transport="stdio")
