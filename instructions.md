# StarQuery AI Setup and Operations Instructions

## Setup

From the repository root:

```bash
cd gen-ai-project/starburst-mcp2
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install fastapi "uvicorn[standard]" openpyxl python-multipart
```

On Windows PowerShell:

```powershell
cd gen-ai-project/starburst-mcp2
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install fastapi "uvicorn[standard]" openpyxl python-multipart
```

## Environment Variables

Starburst variables:

```env
STARBURST_HOST=<tenant-free-cluster.trino.galaxy.starburst.io>
STARBURST_PORT=443
STARBURST_CATALOG=<catalog>
STARBURST_SCHEMA=<schema>
STARBURST_USER=<email>/<role>
STARBURST_PASSWORD=<password>
STARBURST_DEVELOPER=<developer-id>
```

LLM variables:

```env
LLM_ENABLED=true
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1-mini
LLM_API_KEY=<api-key>
LLM_BASE_URL=
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
LLM_DEFAULT_LIMIT=100
```

Provider examples:

```env
# OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1-mini
LLM_API_KEY=<openai-key>

# Claude / Anthropic
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-latest
LLM_API_KEY=<anthropic-key>

# Kimi-compatible OpenAI-style endpoint
LLM_PROVIDER=kimi
LLM_MODEL=kimi-k2.6
LLM_API_KEY=<kimi-key>
LLM_BASE_URL=<kimi-chat-completions-base-url>
```

Never commit `.env`, token files, or API keys.

## Running the App

```bash
cd gen-ai-project/starburst-mcp2
python -m uvicorn app_jwt:app --host 0.0.0.0 --port 8000
```

Open:

```text
http://localhost:8000
```

## Development Workflow

1. Update or add tests for new service behavior.
2. Implement the focused service/module change.
3. Run focused tests.
4. Run existing app tests.
5. Start the FastAPI app and manually test `/api/chat`.

Recommended local tests:

```bash
cd gen-ai-project/starburst-mcp2
pytest tests/test_app_jwt_nl.py -q
pytest -m "not integration" -q
```

Integration tests require a valid `.env` and network access to Starburst:

```bash
pytest -m integration -q
```

## Deployment Steps

1. Set Starburst and LLM environment variables in the runtime environment.
2. Restrict CORS origins for non-local deployments.
3. Run the app with Uvicorn or a production ASGI server.
4. Run `keepalive.py` only where Starburst free-cluster cold start prevention is needed.
5. Monitor query errors, LLM provider errors, and validation failures.

## Rollback

Set:

```env
LLM_ENABLED=false
```

or remove `LLM_API_KEY`. The app should continue to use direct SQL and the existing deterministic regex fallback.
