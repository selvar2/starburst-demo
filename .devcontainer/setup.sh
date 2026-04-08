#!/usr/bin/env bash
# setup.sh — runs once after container creation (postCreateCommand)
# Idempotent: safe to re-run on rebuilds.
set -euo pipefail

PROJECT_DIR="gen ai project/starburst-mcp2"

echo "=== Starburst MCP: postCreateCommand ==="

# Ensure python3 is available
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Aborting."
    exit 1
fi

echo "Python: $(python3 --version)"

# Install dependencies
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip install --upgrade pip -q
    pip install -r "$PROJECT_DIR/requirements.txt" -q
    echo "Dependencies installed."
else
    echo "WARNING: $PROJECT_DIR/requirements.txt not found. Skipping pip install."
fi

# Copy .env.example if .env is missing (secrets stay out of git)
if [ -f "$PROJECT_DIR/.env.example" ] && [ ! -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo "Created .env from .env.example — fill in your credentials."
fi

echo "=== Setup complete ==="
