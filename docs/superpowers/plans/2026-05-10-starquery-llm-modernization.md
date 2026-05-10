# StarQuery AI LLM Modernization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a provider-agnostic LLM layer for schema-aware NL2SQL, summaries, insights, and dashboard recommendations while preserving existing SQL, auth, UI, charts, and exports.

**Architecture:** Keep `app_jwt.py` as the FastAPI entry point and move AI concerns into focused modules. Use a feature flag so the current regex translator remains the fallback when no LLM provider is configured.

**Tech Stack:** Python 3.11+, FastAPI, Starburst/Trino DBAPI, requests, pytest, vanilla HTML/JS, Chart.js.

---

## File Structure

- Create `gen-ai-project/starburst-mcp2/llm_provider.py`: provider config, provider interface, OpenAI/Kimi/Anthropic adapters, mock provider.
- Create `gen-ai-project/starburst-mcp2/prompts.py`: prompt builders for NL2SQL and insight generation.
- Create `gen-ai-project/starburst-mcp2/metadata_service.py`: schema-to-context conversion.
- Create `gen-ai-project/starburst-mcp2/sql_validator.py`: generated SQL safety and metadata validation.
- Create `gen-ai-project/starburst-mcp2/nl2sql_service.py`: orchestration and fallback to legacy translator.
- Create `gen-ai-project/starburst-mcp2/analytics_service.py`: summaries, insights, chart recommendation, dashboard cards.
- Modify `gen-ai-project/starburst-mcp2/app_jwt.py`: call new services in `/api/chat`.
- Modify `gen-ai-project/starburst-mcp2/index.html`: render summaries and insights when present.
- Modify `gen-ai-project/starburst-mcp2/.env.example`: document LLM config.
- Add tests under `gen-ai-project/starburst-mcp2/tests/`.

## Tasks

### Task 1: Provider Abstraction

**Files:**
- Create: `gen-ai-project/starburst-mcp2/llm_provider.py`
- Test: `gen-ai-project/starburst-mcp2/tests/test_llm_provider.py`

- [ ] Define `LLMConfig`, `LLMMessage`, `LLMResponse`, `LLMProvider`, and `ProviderError`.
- [ ] Implement `MockLLMProvider` for deterministic tests.
- [ ] Implement OpenAI-compatible adapter for OpenAI and Kimi.
- [ ] Implement Anthropic adapter with Messages API shape.
- [ ] Implement `build_provider_from_env()`.
- [ ] Test disabled config returns `None`.
- [ ] Test mock provider returns JSON content.

### Task 2: Prompts and Metadata Context

**Files:**
- Create: `gen-ai-project/starburst-mcp2/prompts.py`
- Create: `gen-ai-project/starburst-mcp2/metadata_service.py`
- Test: `gen-ai-project/starburst-mcp2/tests/test_metadata_service.py`

- [ ] Convert schema cache data into compact table context.
- [ ] Build NL2SQL system and user prompts with Trino dialect rules.
- [ ] Include few-shot examples for top products, sales by region, and churn trends.
- [ ] Test table and column names appear in generated context.

### Task 3: SQL Validation

**Files:**
- Create: `gen-ai-project/starburst-mcp2/sql_validator.py`
- Test: `gen-ai-project/starburst-mcp2/tests/test_sql_validator.py`

- [ ] Block multi-statement SQL.
- [ ] Block write/destructive statements for generated business-user read flow.
- [ ] Validate referenced `catalog.schema.table` names against metadata when present.
- [ ] Inject `LIMIT 100` into row-returning SELECT statements without a limit.
- [ ] Test safe SELECT, blocked DROP, blocked multi-statement, and limit injection.

### Task 4: NL2SQL Orchestration

**Files:**
- Create: `gen-ai-project/starburst-mcp2/nl2sql_service.py`
- Test: `gen-ai-project/starburst-mcp2/tests/test_nl2sql_service.py`

- [ ] Preserve direct SQL passthrough for technical users.
- [ ] Use LLM provider for natural language when enabled.
- [ ] Parse JSON-only LLM response.
- [ ] Validate generated SQL.
- [ ] Fall back to legacy translator when provider is unavailable or low confidence.
- [ ] Return structured metadata: source, confidence, assumptions, follow-ups, chart recommendation.

### Task 5: Analytics Service

**Files:**
- Create: `gen-ai-project/starburst-mcp2/analytics_service.py`
- Test: `gen-ai-project/starburst-mcp2/tests/test_analytics_service.py`

- [ ] Generate deterministic fallback summaries from columns and rows.
- [ ] Detect simple KPIs for scalar, grouped, and time-series results.
- [ ] Build dashboard card recommendations from query result shape.
- [ ] Keep LLM insight generation optional.

### Task 6: FastAPI Integration

**Files:**
- Modify: `gen-ai-project/starburst-mcp2/app_jwt.py`
- Test: `gen-ai-project/starburst-mcp2/tests/test_app_jwt_nl.py`

- [ ] Initialize provider and services at module load.
- [ ] Replace direct `_nl_to_sql` call in `/api/chat` with service call.
- [ ] Preserve permission, confirmation, execution, fallback, and chart logic.
- [ ] Add `summary`, `insights`, `dashboard`, `llm_source`, `confidence`, and `assumptions` to response payload.
- [ ] Keep old response fields unchanged.

### Task 7: UI Rendering

**Files:**
- Modify: `gen-ai-project/starburst-mcp2/index.html`

- [ ] Add CSS for compact insight panels using existing colors.
- [ ] Render summary below executed SQL.
- [ ] Render insight bullets and dashboard cards when present.
- [ ] Do not change the main layout or theme.

### Task 8: Documentation and Validation

**Files:**
- Modify: `gen-ai-project/starburst-mcp2/.env.example`
- Verify: tests

- [ ] Add LLM environment variables to `.env.example`.
- [ ] Run `pytest tests/test_app_jwt_nl.py -q`.
- [ ] Run new focused tests.
- [ ] Run `pytest -m "not integration" -q` if dependencies allow.
