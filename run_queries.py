"""Run two queries against the starburst-rw MCP server via stdio JSON-RPC."""
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\Lenovo\gen ai project\starburst-mcp3")
MCP_DIR = PROJECT_ROOT / "gen ai project" / "starburst-mcp2"
ENV_FILE = MCP_DIR / ".env"
SERVER = MCP_DIR / "server.py"

# Load .env into process environment (grep/cut-style parsing to avoid $ expansion)
env = os.environ.copy()
for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, _, value = line.partition("=")
    env[key.strip()] = value.strip()

# Force BasicAuth path: strip OAuth vars so client uses STARBURST_USER/PASSWORD
for k in ("STARBURST_CLIENT_ID", "STARBURST_CLIENT_SECRET", "STARBURST_TOKEN_URL"):
    env.pop(k, None)

QUERIES = [
    'SELECT custkey FROM "sample"."burstbank"."account" LIMIT 1',
    'SELECT * FROM "mcp2ohio"."test_writes"."demo" LIMIT 10',
]

def build_requests():
    yield {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "ad-hoc-runner", "version": "1.0"},
        },
    }
    yield {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
    for i, q in enumerate(QUERIES, start=2):
        yield {
            "jsonrpc": "2.0", "id": i, "method": "tools/call",
            "params": {"name": "execute_query", "arguments": {"query": q}},
        }

payload = "\n".join(json.dumps(r) for r in build_requests()) + "\n"

proc = subprocess.run(
    [sys.executable, str(SERVER)],
    input=payload, capture_output=True, text=True,
    env=env, cwd=str(MCP_DIR), timeout=120,
)

print("===== STDOUT =====")
for line in proc.stdout.splitlines():
    try:
        obj = json.loads(line)
        print(json.dumps(obj, indent=2))
        print("---")
    except json.JSONDecodeError:
        print(line)

print("===== STDERR =====")
print(proc.stderr)
print(f"\nreturncode={proc.returncode}")
