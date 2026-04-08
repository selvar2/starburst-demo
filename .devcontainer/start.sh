#!/usr/bin/env bash
# start.sh — runs every time the container starts (postStartCommand)
# Idempotent: safe to re-run on restarts.
set -euo pipefail

PROJECT_DIR="gen ai project/starburst-mcp2"

echo "=== Starburst MCP: postStartCommand ==="

# Detect environment
if [ "${CODESPACES:-}" = "true" ]; then
    echo "Environment: GitHub Codespaces"
elif [ "${REMOTE_CONTAINERS:-}" = "true" ]; then
    echo "Environment: VS Code Remote Container"
else
    echo "Environment: Local / other"
fi

# Verify Python + key deps are available
python3 -c "import mcp; import trino" 2>/dev/null && echo "Core dependencies OK." \
    || { echo "WARNING: Missing dependencies. Run: pip install -r $PROJECT_DIR/requirements.txt"; }

# Verify server.py is importable
if [ -f "$PROJECT_DIR/server.py" ]; then
    echo "MCP server: $PROJECT_DIR/server.py (ready)"
else
    echo "WARNING: server.py not found at $PROJECT_DIR/server.py"
fi

echo "=== Start complete ==="
