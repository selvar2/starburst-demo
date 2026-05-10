# Instruction For Running The Application In GitHub Codespaces

Audience: AI agents, LLM coding assistants, and automation runners.

Goal: start the StarQuery AI FastAPI web application inside a Linux GitHub Codespaces VM with the fewest assumptions.

Application path:

```text
gen-ai-project/starburst-mcp2
```

Default app URL:

```text
http://127.0.0.1:8001/
```

Codespaces exposes this through the forwarded port `8001`.

---

## 1. Start From Repository Root

Run all commands from the repository root unless a command explicitly changes directory.

```bash
pwd
ls
```

Expected files/folders include:

```text
README.md
.devcontainer/
gen-ai-project/
```

---

## 2. Enter The Application Folder

```bash
cd gen-ai-project/starburst-mcp2
pwd
ls
```

Expected files include:

```text
app_jwt.py
index.html
requirements.txt
.env.example
permissions.yaml
starburst_client_jwt.py
```

---

## 3. Detect Python

Use `python3` first on Linux. If `python3` is missing, try `python`.

```bash
python3 --version || python --version
```

Python 3.11 or newer is recommended.

---

## 4. Create A Virtual Environment

If `.venv` already exists, reuse it.

```bash
python3 -m venv .venv
source .venv/bin/activate
python --version
```

If `python3 -m venv` fails because `venv` is missing:

```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip
python3 -m venv .venv
source .venv/bin/activate
```

---

## 5. Check Whether Dependencies Already Exist

If this command succeeds, the main dependencies are already installed and the install step can be skipped.

```bash
python - <<'PY'
import fastapi
import uvicorn
import trino
import mcp
import dotenv
import yaml
import requests
import openpyxl
import pydantic
print("Dependencies OK")
PY
```

If it fails, install dependencies.

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Verify again:

```bash
python - <<'PY'
import fastapi
import uvicorn
import trino
import mcp
import dotenv
import yaml
import requests
import openpyxl
import pydantic
print("Dependencies OK")
PY
```

---

## 6. Create `.env`

Never commit `.env`. It contains secrets.

```bash
cp .env.example .env
```

Edit `.env`:

```bash
nano .env
```

Minimum required Starburst values:

```dotenv
STARBURST_HOST=datateam-free-cluster.trino.galaxy.starburst.io
STARBURST_PORT=443
STARBURST_CATALOG=mcp2ohio
STARBURST_SCHEMA=test_writes
STARBURST_DEVELOPER=prakashrajr666

STARBURST_CLIENT_ID=example_client@datateam.galaxy.starburst.io
STARBURST_CLIENT_SECRET=replace_with_real_secret
STARBURST_TOKEN_URL=https://datateam.galaxy.starburst.io/oauth2/token
```

Do not paste real secrets into documentation, chat messages, commits, or screenshots.

---

## 7. Enable Or Disable LLM

The application can run without an LLM. Direct SQL and deterministic fallback prompts still work.

Disable LLM:

```dotenv
LLM_ENABLED=false
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_API_KEY=
LLM_BASE_URL=https://api.deepseek.com/chat/completions
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
LLM_DEFAULT_LIMIT=100
```

Enable DeepSeek LLM:

```dotenv
LLM_ENABLED=true
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_BASE_URL=https://api.deepseek.com/chat/completions
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
LLM_DEFAULT_LIMIT=100
```

Enable OpenAI-compatible LLM:

```dotenv
LLM_ENABLED=true
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1-mini
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_BASE_URL=https://api.openai.com/v1/chat/completions
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
LLM_DEFAULT_LIMIT=100
```

---

## 8. Validate Environment Loading

```bash
python - <<'PY'
from dotenv import load_dotenv
import os
load_dotenv()
required = ["STARBURST_HOST", "STARBURST_PORT", "STARBURST_CATALOG", "STARBURST_SCHEMA", "STARBURST_DEVELOPER"]
missing = [name for name in required if not os.getenv(name)]
if missing:
    raise SystemExit(f"Missing required env vars: {missing}")
print("Environment OK")
print("Catalog:", os.getenv("STARBURST_CATALOG"))
print("Schema:", os.getenv("STARBURST_SCHEMA"))
print("LLM enabled:", os.getenv("LLM_ENABLED", "false"))
PY
```

---

## 9. Validate App Imports

```bash
python - <<'PY'
import app_jwt
print("app_jwt import OK")
print(app_jwt.app.title)
PY
```

If this fails, read the Python traceback and fix the missing package or missing environment variable.

---

## 10. Start The Application

Use host `0.0.0.0` in Codespaces so the forwarded port works.

```bash
python -m uvicorn app_jwt:app --host 0.0.0.0 --port 8001
```

Expected output:

```text
Uvicorn running on http://0.0.0.0:8001
```

Open forwarded port `8001` from Codespaces.

---

## 11. Health Checks

In a second terminal:

```bash
curl -i http://127.0.0.1:8001/
```

Expected result:

```text
HTTP/1.1 200 OK
```

Test schema endpoint:

```bash
curl -s http://127.0.0.1:8001/api/schema | head -c 500
```

Expected result: JSON containing catalog/schema/table metadata, or a clear Starburst auth/connection error if credentials are wrong.

Test query endpoint:

```bash
curl -s -X POST http://127.0.0.1:8001/api/query \
  -H "Content-Type: application/json" \
  -d '{"message":"Show all tables"}'
```

Expected result: JSON response with generated SQL, result rows, or a clear error message.

---

## 12. Common Failures And Fixes

### Port Already In Use

```bash
lsof -i :8001
```

Stop the old process or use another port:

```bash
python -m uvicorn app_jwt:app --host 0.0.0.0 --port 8002
```

### Missing Python Package

```bash
python -m pip install -r requirements.txt
```

### App Loads But Schema Fails

Check `.env`:

```bash
grep -E '^(STARBURST_HOST|STARBURST_PORT|STARBURST_CATALOG|STARBURST_SCHEMA|STARBURST_CLIENT_ID|STARBURST_USER|LLM_ENABLED)=' .env
```

Never print secrets such as `STARBURST_CLIENT_SECRET`, `STARBURST_PASSWORD`, or `LLM_API_KEY`.

### LLM Does Not Work

Check non-secret LLM config:

```bash
grep -E '^(LLM_ENABLED|LLM_PROVIDER|LLM_MODEL|LLM_BASE_URL|LLM_TIMEOUT_SECONDS|LLM_MAX_RETRIES|LLM_DEFAULT_LIMIT)=' .env
```

Confirm `LLM_ENABLED=true` and that `LLM_API_KEY` is set in `.env`.

### Direct SQL Works But Natural Language Fails

Try a known deterministic prompt:

```text
Show all tables
```

Then try a fully qualified natural-language prompt:

```text
show all data from demo
```

For business-language prompts, enable LLM and use table names/columns that exist in `mcp2ohio.test_writes`.

---

## 13. Stop The Application

In the terminal running Uvicorn:

```text
Ctrl+C
```

---

## 14. Do Not Commit These Files

Never commit:

```text
.env
token_cache.json
*.log
.venv/
.deps/
.tmp/
backup/
```

