"""Run a query against the starburst-rw MCP server via stdio JSON-RPC."""
import json
import subprocess
import sys
import os
from pathlib import Path

# Load .env manually to avoid shell expansion of $ in passwords
env = os.environ.copy()
env_file = Path(__file__).parent / ".env"
for raw in env_file.read_text().splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, _, value = line.partition("=")
    env[key.strip()] = value.strip()

# Force BasicAuth: remove OAuth vars so client falls back to user/password
for k in ("STARBURST_CLIENT_ID", "STARBURST_CLIENT_SECRET", "STARBURST_TOKEN_URL"):
    env.pop(k, None)

# Build JSON-RPC requests
requests_list = [
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "query-runner", "version": "1.0"},
        },
    },
    {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
    {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "execute_query",
            "arguments": {
                "query": 'SELECT * FROM "mcp2ohio"."test_writes"."demo" LIMIT 10'
            },
        },
    },
]

payload = "\n".join(json.dumps(r) for r in requests_list) + "\n"

server_py = Path(__file__).parent / "server.py"

proc = subprocess.run(
    [sys.executable, str(server_py)],
    input=payload,
    capture_output=True,
    text=True,
    env=env,
    cwd=str(Path(__file__).parent),
    timeout=120,
)

print("===== STDOUT =====")
for line in proc.stdout.splitlines():
    try:
        obj = json.loads(line)
        print(json.dumps(obj, indent=2))
        print("---")
    except json.JSONDecodeError:
        print(line)

if proc.stderr:
    print("===== STDERR =====")
    print(proc.stderr[-2000:])  # last 2000 chars only

print(f"returncode={proc.returncode}")
