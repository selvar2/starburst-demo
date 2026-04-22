#!/usr/bin/env bash
# setup.sh — runs once after container creation (postCreateCommand)
# Always does a FRESH install — no caching, no skipping.
set -euo pipefail

PROJECT_DIR="gen ai project/starburst-mcp2"

echo "============================================"
echo "  Starburst MCP: postCreateCommand (setup)"
echo "============================================"

# ── 1. Detect environment ──────────────────────
if [ "${CODESPACES:-}" = "true" ]; then
    echo "[ENV] GitHub Codespaces detected"
elif [ "${REMOTE_CONTAINERS:-}" = "true" ]; then
    echo "[ENV] VS Code Remote Container detected"
else
    echo "[ENV] Local / other environment"
fi

# ── 2. Verify Python ───────────────────────────
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "[ERROR] No python found. Aborting."
    exit 1
fi
echo "[OK] Python found: $($PYTHON --version) at $(which $PYTHON)"

# ── 3. Fresh install — wipe cached packages ────
echo "[INSTALL] Upgrading pip..."
$PYTHON -m pip install --upgrade pip --force-reinstall -q

echo "[INSTALL] Installing ALL dependencies from scratch..."
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    $PYTHON -m pip install --force-reinstall -r "$PROJECT_DIR/requirements.txt" -q
    echo "[OK] All dependencies installed (fresh)."
else
    echo "[ERROR] $PROJECT_DIR/requirements.txt not found!"
    exit 1
fi

# ── 4. Verify critical packages ────────────────
echo "[VERIFY] Checking core imports..."
$PYTHON -c "
import trino
import mcp
import dotenv
import yaml
print(f'  trino={trino.__version__ if hasattr(trino, \"__version__\") else \"ok\"}')
print(f'  mcp={mcp.__version__ if hasattr(mcp, \"__version__\") else \"ok\"}')
print('  dotenv=ok')
print('  yaml=ok')
"
echo "[OK] All core packages verified."

# ── 5. Check .env exists ───────────────────────
if [ -f "$PROJECT_DIR/.env" ]; then
    echo "[OK] .env file found at $PROJECT_DIR/.env"
else
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        echo "[WARN] Created .env from .env.example — fill in your credentials."
    else
        echo "[WARN] No .env file found. MCP server will start but cannot connect to Starburst."
        echo "       Create: $PROJECT_DIR/.env with your credentials."
    fi
fi

# ── 6. Validate server.py is loadable ──────────
echo "[VERIFY] Checking server.py imports..."
$PYTHON -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
from starburst_client import StarburstClient
from permission_manager import PermissionManager
from tools import register_read_tools, register_write_tools
from mcp.server.fastmcp import FastMCP
print('  All server modules loadable.')
"
echo "[OK] Server validated."

echo "============================================"
echo "  Setup complete — MCP server ready"
echo "============================================"

# ── 7. Launch keepalive in background ────────────
if [ -f "$PROJECT_DIR/keepalive.py" ]; then
    if pgrep -f "keepalive.py" >/dev/null 2>&1; then
        echo "[OK] keepalive.py already running (PID $(pgrep -f keepalive.py))"
    else
        nohup $PYTHON "$PROJECT_DIR/keepalive.py" >> "$PROJECT_DIR/keepalive.log" 2>&1 &
        echo "[OK] keepalive.py started in background (PID $!)"
    fi
fi
