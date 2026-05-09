# Starburst Galaxy Auth Guide

How to connect to Starburst Galaxy without browser popups.
Read this file once. You will know everything needed.

## The Problem

Starburst Galaxy uses OAuth2 login. By default, it opens a browser window.
This is bad for servers, scripts, and AI agents.

## The Solution

We bypass the browser. We login using Galaxy's API. No popup. No user action.

There are 3 files that do this:

| File | What It Does |
|------|-------------|
| `starburst_client.py` | Original client. Opens browser for OAuth. |
| `starburst_client_jwt.py` | No browser. Logs in using API. Drop-in replacement. |
| `token_cache.py` | No browser. Saves token to disk. Reuses on restart. |

## .env File (Required)

All auth files read from `.env` in the same folder. Here are the fields:

```env
# Connection
STARBURST_HOST=datateam-free-cluster.trino.galaxy.starburst.io
STARBURST_PORT=443
STARBURST_CATALOG=mcp2ohio
STARBURST_SCHEMA=test_writes

# User login (email + password for Galaxy portal)
STARBURST_USER=your_email@company.com/accountadmin
STARBURST_PASSWORD=your_password

# Service account (optional, used by original client for OAuth)
STARBURST_CLIENT_ID=service_name@domain.galaxy.starburst.io
STARBURST_CLIENT_SECRET=GXY$your_secret_here
STARBURST_TOKEN_URL=https://domain.galaxy.starburst.io/oauth2/token
```

### Which fields matter for each client:

| Field | starburst_client.py | starburst_client_jwt.py | token_cache.py |
|-------|:---:|:---:|:---:|
| STARBURST_HOST | Yes | Yes | Yes |
| STARBURST_PORT | Yes | Yes | Yes |
| STARBURST_CATALOG | Yes | Yes | Yes |
| STARBURST_SCHEMA | Yes | Yes | Yes |
| STARBURST_USER | Fallback | Yes | Yes |
| STARBURST_PASSWORD | Fallback | Yes | Yes |
| STARBURST_CLIENT_ID | Yes | No | No |
| STARBURST_CLIENT_SECRET | Yes | No | No |

## How Each Client Works

### 1. starburst_client.py (Original - Browser Popup)

```
User runs query -> Trino says "login needed" -> Opens browser ->
User clicks approve -> Token saved in memory -> Query runs
```

**Problem:** Needs browser. Bad for servers.

### 2. starburst_client_jwt.py (No Browser)

```
User runs query -> Trino says "login needed" -> Instead of browser:
  1. POST /api/v1/login with email + password
  2. GET /oauth/v2/redirect to complete callback
-> Token saved in memory -> Query runs
```

**How:** Monkey-patches `webbrowser.open`. When Trino tries to open browser,
our code runs the login API instead.

**Use this when:** Running a server (app_jwt.py), background scripts, CI/CD.

### 3. token_cache.py (No Browser + Disk Cache)

```
First run: Same as #2, but also saves token info to token_cache.json
Next run:  Checks token_cache.json. If valid, skips login. Fast startup.
Expired:   Logs in again, saves new token.
```

**Use this when:** You want fastest startup. Good for keepalive scripts.

## Quick Start

### Test original client (will open browser):
```bash
cd "gen-ai-project/starburst-mcp2"
python -c "from starburst_client import StarburstClient; c = StarburstClient(); print(c.execute('SELECT 1'))"
```

### Test JWT client (no browser):
```bash
cd "gen-ai-project/starburst-mcp2"
python -c "from starburst_client_jwt import StarburstClientJWT; c = StarburstClientJWT(); print(c.execute('SELECT 1'))"
```

Expected output:
```
{'columns': ['_col0'], 'rows': [[1]]}
```

### Test token cache (no browser + saves to disk):
```bash
cd "gen-ai-project/starburst-mcp2"
python token_cache.py
```

Expected output:
```
Testing token cache...

No cached token found. Will login fresh.

Connected!
  Auth mode: jwt-cached
  Host:      datateam-free-cluster.trino.galaxy.starburst.io
  Catalog:   mcp2ohio

Query result (3 rows):
  Columns: ['id', 'name', 'amount']
  [3, 'test3', 300.0]
  [2, 'test2', 200.0]
  [1, 'hello', 150.0]

Token saved to: .../token_cache.json
Token content: { "host": "...", "expires_at": ..., "status": "active" }
```

Second run will show:
```
Found cached token:
  Host:    datateam-free-cluster.trino.galaxy.starburst.io
  Email:   your_email@company.com
  Created: Tue Apr 15 ...
  Expires: Tue Apr 15 ...
```

## How to Use in Your Code

### Option A: Use StarburstClientJWT (recommended for servers)

```python
from starburst_client_jwt import StarburstClientJWT as StarburstClient

client = StarburstClient()
result = client.execute("SELECT * FROM mcp2ohio.test_writes.demo LIMIT 10")
print(result["columns"])  # ['id', 'name', 'amount']
print(result["rows"])     # [[1, 'hello', 150.0], ...]
```

### Option B: Use token_cache (recommended for scripts)

```python
from token_cache import get_cached_client

client = get_cached_client()
result = client.execute("SELECT * FROM mcp2ohio.test_writes.demo LIMIT 10")
print(result["columns"])  # ['id', 'name', 'amount']
print(result["rows"])     # [[1, 'hello', 150.0], ...]
```

### Option C: Use in FastAPI app

```python
# In app_jwt.py, line 16 is:
from starburst_client_jwt import StarburstClientJWT as StarburstClient

# Everything else stays the same as app.py
```

Run it:
```bash
python -m uvicorn app_jwt:app --host 0.0.0.0 --port 8000
```

## File List

```
starburst-mcp2/
  .env                      # Credentials (never commit this)
  starburst_client.py       # Original client (browser popup)
  starburst_client_jwt.py   # JWT client (no browser)
  token_cache.py            # Token cache (no browser + disk save)
  token_cache.json          # Saved token (auto-created, never commit)
  app.py                    # FastAPI server (uses original client)
  app_jwt.py                # FastAPI server (uses JWT client)
  keepalive.py              # Keeps cluster awake every 4 minutes
```

## Troubleshooting

### "Browser still opens"
You are using `starburst_client.py`. Switch to `starburst_client_jwt.py`.

### "Login failed" or "401 error"
Check your `.env` file:
- `STARBURST_USER` must be an email (the part before `/`)
- `STARBURST_PASSWORD` must be your Galaxy portal password
- Make sure no extra spaces in the values

### "Connection timeout"
The free cluster may be asleep. Run `keepalive.py` to keep it awake:
```bash
nohup python keepalive.py > /dev/null 2>&1 &
```

### "Token expired"
Delete `token_cache.json` and run again. A new token will be created.
```bash
rm token_cache.json
python token_cache.py
```

## For AI Agents

If you are an AI agent reading this file, here is what you need to know:

1. **Never use `starburst_client.py` for headless work.** It opens a browser.
2. **Use `starburst_client_jwt.py` instead.** Same API, no browser.
3. **Import:** `from starburst_client_jwt import StarburstClientJWT as StarburstClient`
4. **The .env file must exist** in the same folder with STARBURST_USER and STARBURST_PASSWORD.
5. **The Galaxy host is auto-detected** from STARBURST_HOST. No extra config needed.
6. **Token is cached in memory** by the Trino client. One login per session.
7. **To run the web app without browser:** `python -m uvicorn app_jwt:app --port 8000`
