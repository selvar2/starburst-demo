#!/usr/bin/env bash
# start.sh — runs every time the container starts (postStartCommand)
# Validates environment, deps, .env, and server readiness.
set -euo pipefail

PROJECT_DIR="gen ai project/starburst-mcp2"
ERRORS=0

echo "============================================"
echo "  Starburst MCP: postStartCommand (start)"
echo "============================================"

# ── 1. Detect environment ──────────────────────
if [ "${CODESPACES:-}" = "true" ]; then
    echo "[ENV] GitHub Codespaces"
elif [ "${REMOTE_CONTAINERS:-}" = "true" ]; then
    echo "[ENV] VS Code Remote Container"
else
    echo "[ENV] Local / other"
fi

# ── 2. Detect Python ───────────────────────────
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "[FAIL] No python found!"
    ERRORS=$((ERRORS + 1))
    PYTHON=""
fi

if [ -n "$PYTHON" ]; then
    echo "[OK] $($PYTHON --version) at $(which $PYTHON)"
fi

# ── 3. Verify deps are installed ───────────────
if [ -n "$PYTHON" ]; then
    if $PYTHON -c "import trino; import mcp; import dotenv; import yaml" 2>/dev/null; then
        echo "[OK] Core dependencies available"
    else
        echo "[WARN] Missing dependencies — reinstalling..."
        $PYTHON -m pip install -r "$PROJECT_DIR/requirements.txt" -q
        if $PYTHON -c "import trino; import mcp; import dotenv; import yaml" 2>/dev/null; then
            echo "[OK] Dependencies recovered after reinstall"
        else
            echo "[FAIL] Dependencies still missing after reinstall"
            ERRORS=$((ERRORS + 1))
        fi
    fi
fi

# ── 4. Check .env ──────────────────────────────
if [ -f "$PROJECT_DIR/.env" ]; then
    echo "[OK] .env file found"

    # Validate key variables (parse .env safely without shell expansion)
    get_env_val() { grep "^$1=" "$PROJECT_DIR/.env" 2>/dev/null | head -1 | cut -d'=' -f2-; }

    for var in STARBURST_HOST STARBURST_PORT STARBURST_CATALOG; do
        val=$(get_env_val "$var")
        if [ -n "$val" ]; then
            echo "  $var = $val"
        else
            echo "  [WARN] $var is not set in .env"
        fi
    done

    # Show auth mode
    CID=$(get_env_val "STARBURST_CLIENT_ID")
    BUSER=$(get_env_val "STARBURST_USER")
    if [ -n "$CID" ]; then
        echo "  Auth: OAuth (client_id=$CID)"
    elif [ -n "$BUSER" ]; then
        echo "  Auth: BasicAuth (user=$BUSER)"
    else
        echo "  [WARN] No auth credentials found in .env"
    fi
else
    echo "[WARN] No .env file — server will start but cannot connect"
    ERRORS=$((ERRORS + 1))
fi

# ── 5. Verify server.py ────────────────────────
if [ -f "$PROJECT_DIR/server.py" ]; then
    echo "[OK] server.py found"
else
    echo "[FAIL] server.py not found at $PROJECT_DIR/server.py"
    ERRORS=$((ERRORS + 1))
fi

# ── 6. Quick MCP handshake test ─────────────────
if [ -n "$PYTHON" ] && [ -f "$PROJECT_DIR/server.py" ]; then
    INIT='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"healthcheck","version":"0.1"}}}'
    RESPONSE=$(echo "$INIT" | timeout 10 $PYTHON "./$PROJECT_DIR/server.py" 2>/dev/null || true)
    if echo "$RESPONSE" | grep -q '"serverInfo"'; then
        SERVER_NAME=$(echo "$RESPONSE" | $PYTHON -c "import sys,json; print(json.loads(sys.stdin.read())['result']['serverInfo']['name'])" 2>/dev/null || echo "unknown")
        SERVER_VER=$(echo "$RESPONSE" | $PYTHON -c "import sys,json; print(json.loads(sys.stdin.read())['result']['serverInfo']['version'])" 2>/dev/null || echo "unknown")
        echo "[OK] MCP server responds: $SERVER_NAME v$SERVER_VER"
    else
        echo "[WARN] MCP server did not respond to handshake"
    fi
fi

# ── Summary ─────────────────────────────────────
echo "============================================"
if [ $ERRORS -eq 0 ]; then
    echo "  All checks passed — MCP server ready"
else
    echo "  Completed with $ERRORS warning(s)"
fi
echo "============================================"
