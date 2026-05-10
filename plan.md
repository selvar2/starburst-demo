# StarQuery AI LLM Modernization Plan

## Current Architecture Analysis

The repository contains a Starburst Galaxy MCP server and a browser app named StarQuery AI. The active web app lives in `gen-ai-project/starburst-mcp2/app_jwt.py` and serves `index.html` directly from FastAPI. The current request flow is:

1. Browser sends `/api/chat` with `{message, context}`.
2. `app_jwt.py` resolves catalog/schema defaults from Starburst config.
3. `_nl_to_sql` translates natural language through fixed regex patterns or passes raw SQL through.
4. SQL is classified, fully-qualified validation is applied to DDL/DML, permissions are checked, and destructive operations require confirmation.
5. `StarburstClientJWT` executes SQL against Starburst Galaxy with headless OAuth.
6. Results are returned with columns, rows, row count, chart suggestion, and SQL text.
7. `index.html` renders table, Chart.js visualization, exports, and follow-up chips.

Authentication is currently handled by `starburst_client_jwt.py`, which monkey-patches browser OAuth redirects and performs the Galaxy portal flow in-process. The devcontainer installs Python 3.13, dependencies from `requirements.txt`, validates MCP imports, and starts a keepalive daemon. Schema metadata is loaded through `/api/schema`, cached for five minutes, and pre-warmed in a daemon thread.

## Problem Statement

The current natural-language layer is rule-based. It works for a narrow set of phrasings but fails when a business user asks semantically equivalent questions such as "sales for the us-east region in 2026" or "which products drove revenue last quarter". It also couples NL parsing, SQL execution, chart selection, export concerns, permissions, and API routing inside one large FastAPI file.

The modernization goal is to introduce a provider-agnostic LLM layer that owns natural-language understanding, schema-aware SQL generation, result summarization, insight generation, dashboard suggestions, and chart recommendation while preserving existing SQL passthrough, authentication, permissions, exports, charts, and UI theme.

## Target Architecture

The target architecture keeps StarQuery AI as a FastAPI + vanilla HTML app, but extracts AI responsibilities into focused services:

- `llm_provider.py`: provider abstraction, retries, streaming shape, provider factory.
- `prompts.py`: centralized prompt templates for NL2SQL, summaries, dashboards, and SQL repair.
- `metadata_service.py`: schema context loader and business glossary builder from cached Starburst metadata.
- `sql_validator.py`: read-query safety, dangerous statement blocking, table/column validation, scan limiting.
- `nl2sql_service.py`: orchestration for SQL passthrough, LLM generation, fallback regex generation, validation, and repair.
- `analytics_service.py`: summaries, KPI detection, and chart/dashboard recommendation.

`app_jwt.py` remains the API entry point and Starburst auth remains unchanged. Existing raw SQL support remains first-class for technical users. Natural language uses LLM generation when `LLM_ENABLED=true` and a provider API key exists; otherwise the current deterministic regex path remains the fallback so demos do not break.

## Implementation Phases

### Phase 1: Planning and Documentation

- Create `plan.md`, `claude.md`, and `instructions.md`.
- Document current flow, limitations, target architecture, security rules, rollout, and rollback.

### Phase 2: Backend Service Extraction

- Add typed LLM provider abstractions with adapters for OpenAI, Anthropic/Claude, and Kimi-compatible chat APIs.
- Add prompt templates with JSON-only response contracts.
- Add metadata context building from `/api/schema` cache.
- Add SQL validator for generated SQL before execution.
- Add NL2SQL service that falls back to existing `_nl_to_sql` when no LLM is configured.

### Phase 3: API Integration

- Update `/api/chat` to call the NL2SQL service.
- Preserve classification, permission checks, destructive confirmation, cross-schema fallback, execution, export, and chart behavior.
- Add summary, insights, dashboard cards, and chart recommendation fields to the response payload.

### Phase 4: UI Enhancement

- Keep the existing theme, layout, typography, and Chart.js flow.
- Add compact insight/summary rendering inside bot responses only when the backend provides those fields.
- Avoid a redesign or new framework.

### Phase 5: Validation

- Unit-test provider config, SQL validation, metadata context, NL2SQL fallback, and response payload behavior.
- Run existing unit tests to verify current SQL and regex flows remain intact.
- If credentials are available, run integration tests against Starburst.

## Database Strategy

Starburst/Trino remains the first dialect. The metadata layer should represent catalog, schema, table, and columns generically so Redshift, Snowflake, Postgres, and future engines can be added behind the same interface. SQL prompts must include dialect rules and should default to read-only `SELECT` for business-user NL requests unless the user explicitly asks for write operations and permissions allow them.

## LLM Strategy

Providers are selected by config:

- `LLM_PROVIDER=kimi|openai|anthropic|mock`
- `LLM_MODEL=<model-name>`
- `LLM_API_KEY=<secret>`
- Optional provider-specific base URLs and timeout/retry settings.

The LLM must return structured JSON. NL2SQL responses include intent, SQL, assumptions, chart recommendation, confidence, and optional follow-up questions. Summary responses include executive summary, insights, anomalies, and dashboard card definitions. Provider adapters must not leak provider-specific request formats into API routes.

## Security Plan

- Never hard-code API keys or database credentials.
- Preserve Starburst authentication and permission checks.
- Raw SQL remains supported for technical users but still goes through classification and permission checks.
- LLM-generated SQL must be validated before execution.
- Block multi-statement SQL, comments used for injection, dangerous statements for business-user read flows, unsupported catalogs/schemas/tables, and excessive result scans.
- Add a default `LIMIT` to generated SELECT queries when absent.
- Keep destructive operations behind explicit confirmation.

## Rollback Strategy

The LLM path is feature-flagged. Set `LLM_ENABLED=false` or remove `LLM_API_KEY` to return to the existing regex/passthrough behavior. New modules are additive. `app_jwt.py` integration should preserve the original `_nl_to_sql` function as fallback during this migration.

## Risks

- LLM hallucinated tables or columns: mitigated by schema context and validation.
- SQL dialect mismatch: mitigated by Trino-specific prompt rules and validator.
- Provider latency or outage: mitigated by timeouts, retries, fallback provider, and regex fallback.
- Large scans: mitigated by limit injection and future cost estimation.
- Shared Starburst connection thread safety: existing risk remains; future work should add connection pooling.

## Testing Strategy

- Unit tests for LLM provider factory and mock provider.
- Unit tests for SQL validator blocking destructive or multi-statement generated SQL.
- Unit tests for metadata context creation from cached schema data.
- Unit tests for NL2SQL service fallback with no API key.
- Existing `test_app_jwt_nl.py` must continue to pass.
- Optional integration test: `/api/chat` raw SQL and NL query with live Starburst credentials.

## Future Improvements

- Add vector search over table descriptions, sample queries, and glossary terms.
- Add connection pooling for concurrent FastAPI requests.
- Add SSE streaming for LLM summaries and long-running query status.
- Add per-user auth claims and tenant-aware metadata filtering.
- Add cost estimation with Trino `EXPLAIN`.
- Add saved dashboards and conversation memory.
