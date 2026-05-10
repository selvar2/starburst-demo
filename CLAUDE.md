# StarQuery AI Agent Guidelines

## Project AI Guidelines

StarQuery AI serves both technical SQL users and non-technical business users. Technical users may enter SQL directly. Business users may enter natural language, which should be converted to validated SQL through the LLM layer when enabled.

Agents working on this project must preserve the existing authentication flow, theme, exports, charting behavior, and permission model. Prefer additive, feature-flagged changes over rewrites.

## LLM Prompting Rules

- Always include current catalog, schema, table, and column context.
- State the SQL dialect explicitly as Trino/Starburst unless another database adapter is selected.
- Ask the model for JSON only; do not parse prose when structured output is required.
- Require the model to name assumptions and confidence.
- Require generated SQL to be a single statement.
- Require `LIMIT` for exploratory row-returning queries.
- Do not allow the model to invent tables or columns outside provided metadata.
- Use few-shot examples for common BI asks: top N, time series, regional filters, KPI summaries, and dashboard requests.

## SQL Safety Rules

- Never execute raw user text as SQL after LLM transformation without validation.
- Preserve direct SQL support for technical users, but still classify permissions.
- Generated business-user SQL defaults to read-only `SELECT` unless the user explicitly asks for a write.
- Block multi-statement SQL and unsafe comments.
- Block `DROP`, `TRUNCATE`, `ALTER`, `GRANT`, `REVOKE`, and write statements from the LLM read flow.
- Validate referenced tables and columns against metadata when metadata is available.
- Inject a conservative `LIMIT` when a generated `SELECT` has no limit.
- Keep destructive operations behind `context.confirm=true`.

## Architecture Constraints

- `app_jwt.py` remains the FastAPI entry point.
- `starburst_client_jwt.py` authentication must not be replaced in this migration.
- New AI logic belongs in dedicated service modules.
- Provider-specific code belongs only in provider adapters.
- Prompt text belongs in `prompts.py`, not route handlers.
- UI additions must match the existing single-file theme and should be compact.
- No API keys, tokens, passwords, or tenant secrets may be committed.

## Coding Standards

- Use Python type hints for new modules.
- Use dataclasses or Pydantic models for structured service contracts.
- Keep functions small and single-purpose.
- Use structured exceptions for expected validation/provider failures.
- Avoid broad rewrites of existing regex behavior unless tests require it.
- Preserve backwards compatibility in API response fields.
- Add tests for new behavior before relying on it.

## Agent Behavior Rules

- Read relevant files before editing.
- Update documentation when adding environment variables or service behavior.
- Run focused tests after backend changes.
- If live Starburst credentials are unavailable or network is blocked, state that clearly and rely on unit tests.
- Treat existing uncommitted changes as user-owned.
- Prefer rollback-friendly feature flags.
