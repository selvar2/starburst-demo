# Manual To Run StarQuery AI In GitHub Codespaces

This manual is written for humans, non-technical users, and AI assistants. Follow it top to bottom to run the application in a Linux GitHub Codespaces VM.

The application is a FastAPI web app backed by Starburst/Trino. It supports:

- Direct SQL
- Natural-language prompts
- Optional LLM-powered NL2SQL
- Schema browser
- Query results
- Charts and executive insights

---

## 1. What You Need Before Starting

You need:

- A GitHub Codespace opened for this repository
- Starburst connection details
- Starburst OAuth client credentials or username/password credentials
- Optional LLM API key if you want schema-aware AI/NL2SQL

Do not commit secrets. The local `.env` file is ignored by Git.

---

## 2. Repository Structure

The main app lives here:

```text
gen-ai-project/starburst-mcp2
```

Important files:

```text
gen-ai-project/starburst-mcp2/app_jwt.py          # FastAPI backend
gen-ai-project/starburst-mcp2/index.html          # Browser UI
gen-ai-project/starburst-mcp2/requirements.txt    # Python dependencies
gen-ai-project/starburst-mcp2/.env.example        # Environment template
gen-ai-project/starburst-mcp2/permissions.yaml    # Permission profile config
```

---

## 3. Open A Terminal In Codespaces

In GitHub Codespaces:

1. Open the repository.
2. Open Terminal.
3. Confirm you are at the repository root.

```bash
pwd
ls
```

You should see:

```text
README.md
gen-ai-project
```

---

## 4. Go To The App Folder

```bash
cd gen-ai-project/starburst-mcp2
```

Confirm files:

```bash
ls
```

Expected:

```text
app_jwt.py
index.html
requirements.txt
.env.example
```

---

## 5. Set Up Python

Check Python:

```bash
python3 --version
```

Recommended: Python 3.11 or newer.

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

After activation, the terminal prompt usually shows `.venv`.

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

---

## 6. Install Dependencies

If dependencies are already installed, the check below will pass and you can skip installation.

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
print("All required packages are installed.")
PY
```

If the command fails, install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the check again:

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
print("All required packages are installed.")
PY
```

---

## 7. Create The Environment File

Create `.env` from the example:

```bash
cp .env.example .env
```

Open it:

```bash
nano .env
```

Fill in Starburst values. Example with masked secrets:

```dotenv
# OAuth Authentication
STARBURST_CLIENT_ID=example_client@datateam.galaxy.starburst.io
STARBURST_CLIENT_SECRET=replace_with_real_secret
STARBURST_TOKEN_URL=https://datateam.galaxy.starburst.io/oauth2/token

# Connection
STARBURST_HOST=datateam-free-cluster.trino.galaxy.starburst.io
STARBURST_PORT=443
STARBURST_CATALOG=mcp2ohio
STARBURST_SCHEMA=test_writes

# Developer ID for permissions.yaml
STARBURST_DEVELOPER=prakashrajr666
```

If using username/password fallback instead of OAuth, fill these:

```dotenv
STARBURST_USER=user@example.com/accountadmin
STARBURST_PASSWORD=replace_with_real_password
```

Keep secrets private.

---

## 8. Configure LLM

The app runs without an LLM. In that mode:

- SQL works.
- Known deterministic natural-language prompts work.
- Advanced business-language prompts may need LLM enabled.

### Option A: Run Without LLM

Use this when you only want direct SQL and deterministic fallback prompts.

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

### Option B: Enable DeepSeek

Use this when you want LLM-powered natural-language analytics.

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

### Option C: Enable OpenAI

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

### Option D: Enable Anthropic / Claude

```dotenv
LLM_ENABLED=true
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-latest
LLM_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_BASE_URL=https://api.anthropic.com/v1/messages
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
LLM_DEFAULT_LIMIT=100
```

---

## 9. Validate Configuration

Run this after saving `.env`:

```bash
python - <<'PY'
from dotenv import load_dotenv
import os

load_dotenv()

required = [
    "STARBURST_HOST",
    "STARBURST_PORT",
    "STARBURST_CATALOG",
    "STARBURST_SCHEMA",
    "STARBURST_DEVELOPER",
]

missing = [name for name in required if not os.getenv(name)]
if missing:
    raise SystemExit(f"Missing required variables: {missing}")

print("Environment looks valid.")
print("Host:", os.getenv("STARBURST_HOST"))
print("Catalog:", os.getenv("STARBURST_CATALOG"))
print("Schema:", os.getenv("STARBURST_SCHEMA"))
print("LLM enabled:", os.getenv("LLM_ENABLED", "false"))
print("LLM provider:", os.getenv("LLM_PROVIDER", "not set"))
PY
```

Do not print secret values.

---

## 10. Validate Starburst Connection

Run:

```bash
python - <<'PY'
from dotenv import load_dotenv
load_dotenv()

from starburst_client_jwt import StarburstClientJWT

client = StarburstClientJWT()
rows = client.execute("SELECT 1")
print(rows)
PY
```

Expected output:

```text
[[1]]
```

If this fails, check:

- `STARBURST_HOST`
- `STARBURST_CLIENT_ID`
- `STARBURST_CLIENT_SECRET`
- `STARBURST_TOKEN_URL`
- Starburst role permissions
- Network access from Codespaces

---

## 11. Start The Web Application

Run:

```bash
python -m uvicorn app_jwt:app --host 0.0.0.0 --port 8001
```

Expected output:

```text
INFO:     Uvicorn running on http://0.0.0.0:8001
```

In Codespaces, open the forwarded port `8001`.

Local browser URL:

```text
http://127.0.0.1:8001/
```

---

## 12. Test The App In Browser

Try these prompts:

```text
Show all tables
```

```text
Describe demo table
```

```text
Show all data from demo
```

```text
Count rows in demo
```

Try direct SQL:

```sql
SELECT "id", "name", "amount"
FROM "mcp2ohio"."test_writes"."demo"
ORDER BY "amount" DESC
LIMIT 20;
```

---

## 13. Test With curl

If the browser does not load, test the backend from terminal.

```bash
curl -i http://127.0.0.1:8001/
```

Expected:

```text
HTTP/1.1 200 OK
```

Test API:

```bash
curl -s -X POST http://127.0.0.1:8001/api/query \
  -H "Content-Type: application/json" \
  -d '{"message":"Show all tables"}'
```

Expected:

```text
JSON response with SQL, rows, columns, or a clear error.
```

---

## 14. Optional Keepalive

Use this if the Starburst free cluster sleeps during demos.

Open a second terminal:

```bash
cd gen-ai-project/starburst-mcp2
source .venv/bin/activate
python keepalive.py
```

Stop it with:

```text
Ctrl+C
```

---

## 15. Troubleshooting

### Problem: `ModuleNotFoundError`

Fix:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Problem: `Address already in use`

Check:

```bash
lsof -i :8001
```

Use another port:

```bash
python -m uvicorn app_jwt:app --host 0.0.0.0 --port 8002
```

Then open forwarded port `8002`.

### Problem: Browser says the site cannot be reached

Fix:

- Confirm Uvicorn is still running.
- Confirm it used `--host 0.0.0.0`.
- Confirm Codespaces forwarded port `8001`.

### Problem: Starburst authentication fails

Check non-secret config:

```bash
grep -E '^(STARBURST_HOST|STARBURST_PORT|STARBURST_CATALOG|STARBURST_SCHEMA|STARBURST_CLIENT_ID|STARBURST_USER)=' .env
```

Do not print:

```text
STARBURST_CLIENT_SECRET
STARBURST_PASSWORD
LLM_API_KEY
```

### Problem: LLM is not being used

Check:

```bash
grep -E '^(LLM_ENABLED|LLM_PROVIDER|LLM_MODEL|LLM_BASE_URL|LLM_TIMEOUT_SECONDS|LLM_MAX_RETRIES|LLM_DEFAULT_LIMIT)=' .env
```

Expected:

```dotenv
LLM_ENABLED=true
```

Also confirm `LLM_API_KEY` exists in `.env`, but do not print it.

### Problem: Natural language prompt fails

Use one of the known working prompts first:

```text
Show all tables
```

```text
Describe demo table
```

```text
Show all data from demo
```

Then use table/column names from the schema browser.

---

## 16. Safe Shutdown

In the terminal where Uvicorn is running:

```text
Ctrl+C
```

---

## 17. Files That Must Stay Local

Do not commit:

```text
gen-ai-project/starburst-mcp2/.env
gen-ai-project/starburst-mcp2/token_cache.json
gen-ai-project/starburst-mcp2/*.log
gen-ai-project/starburst-mcp2/.venv/
gen-ai-project/starburst-mcp2/.deps/
gen-ai-project/starburst-mcp2/.tmp/
gen-ai-project/starburst-mcp2/backup/
```

---

## 18. One-Command Run After Setup

After dependencies and `.env` are ready:

```bash
cd gen-ai-project/starburst-mcp2
source .venv/bin/activate
python -m uvicorn app_jwt:app --host 0.0.0.0 --port 8001
```
