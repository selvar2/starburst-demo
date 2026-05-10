"""NL2SQL orchestration for StarQuery AI."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Callable

from grounding import QueryClassification, classify_enterprise_query
from llm_provider import LLMProvider, ProviderError
from metadata_service import build_schema_context
from prompts import build_nl2sql_messages
from sql_validator import SQLValidationError, validate_generated_sql


_SQL_START = re.compile(
    r"^\s*(SELECT|WITH|INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|MERGE)\b",
    re.IGNORECASE,
)
_CREATE_SQL = re.compile(
    r"^\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:SCHEMA|TABLE|VIEW|MATERIALIZED\s+VIEW|CATALOG|ROLE|FUNCTION)\b",
    re.IGNORECASE,
)
_SHOW_SQL = re.compile(r"^\s*SHOW\s+(TABLES|SCHEMAS|CATALOGS|COLUMNS)\b", re.IGNORECASE)
_DESCRIBE_SQL = re.compile(r"^\s*DESCRIBE\s+\w+\.\w+\.\w+\b", re.IGNORECASE)


@dataclass(frozen=True)
class NL2SQLResult:
    sql: str | None
    source: str
    confidence: float | None = None
    assumptions: list[str] = field(default_factory=list)
    followups: list[str] = field(default_factory=list)
    chart: str | None = None
    warnings: list[str] = field(default_factory=list)
    error: str | None = None
    query_type: str = "unknown"
    grounding_reason: str = ""
    matched_terms: list[str] = field(default_factory=list)


LegacyTranslator = Callable[[str, str, str], str | None]


class NL2SQLService:
    def __init__(
        self,
        provider: LLMProvider | None,
        legacy_translator: LegacyTranslator,
        default_limit: int | None = None,
    ):
        self.provider = provider
        self.legacy_translator = legacy_translator
        self.default_limit = default_limit or _env_int("LLM_DEFAULT_LIMIT", 100)

    def translate(
        self,
        message: str,
        catalog: str,
        schema: str,
        schema_data: dict | None,
    ) -> NL2SQLResult:
        raw = message.strip()
        if _is_direct_sql(raw):
            return NL2SQLResult(
                sql=raw.rstrip(";"),
                source="sql",
                query_type="direct_sql",
                grounding_reason="Technical SQL input is treated as user-authored SQL.",
            )

        if re.match(r"^\s*create\b", raw, re.IGNORECASE):
            legacy_create = self.legacy_translator(raw, catalog, schema)
            if legacy_create and legacy_create.strip().lower() != raw.strip().lower():
                return NL2SQLResult(
                    sql=legacy_create,
                    source="legacy",
                    query_type="enterprise_query",
                    grounding_reason="Governed CREATE request matched an approved schema/table creation pattern.",
                )

        schema_context = build_schema_context(schema_data, catalog, schema)
        classification = classify_enterprise_query(raw, schema_context)
        if not classification.allowed:
            return _rejected_result(classification)

        if self.provider is not None:
            try:
                messages = build_nl2sql_messages(raw, catalog, schema, schema_context)
                response = self.provider.complete(messages)
                parsed = _parse_json_object(response.content)
                candidate = str(parsed.get("sql", "")).strip()
                validation = validate_generated_sql(candidate, schema_context, default_limit=self.default_limit)
                return NL2SQLResult(
                    sql=validation.sql,
                    source="llm",
                    confidence=_coerce_float(parsed.get("confidence")),
                    assumptions=_string_list(parsed.get("assumptions")),
                    followups=_string_list(parsed.get("followups")),
                    chart=str(parsed.get("chart") or "") or None,
                    warnings=validation.warnings,
                    query_type=classification.query_type,
                    grounding_reason=classification.reason,
                    matched_terms=classification.matched_terms,
                )
            except (ProviderError, SQLValidationError, ValueError, TypeError, json.JSONDecodeError) as exc:
                legacy = self.legacy_translator(raw, catalog, schema)
                if legacy and _is_safe_legacy_after_llm_failure(raw, legacy):
                    return NL2SQLResult(
                        sql=legacy,
                        source="legacy",
                        error=str(exc),
                        query_type=classification.query_type,
                        grounding_reason=classification.reason,
                        matched_terms=classification.matched_terms,
                    )
                return NL2SQLResult(
                    sql=None,
                    source="llm_error",
                    error=str(exc),
                    query_type=classification.query_type,
                    grounding_reason=classification.reason,
                    matched_terms=classification.matched_terms,
                )

        legacy = self.legacy_translator(raw, catalog, schema)
        return NL2SQLResult(
            sql=legacy,
            source="legacy" if legacy else "none",
            query_type=classification.query_type,
            grounding_reason=classification.reason,
            matched_terms=classification.matched_terms,
        )


def _rejected_result(classification: QueryClassification) -> NL2SQLResult:
    return NL2SQLResult(
        sql=None,
        source="rejected",
        confidence=0.0,
        error="NO RELEVANT INFORMATION EXISTS IN THE ENTERPRISE DATA SOURCES.",
        query_type=classification.query_type,
        grounding_reason=classification.reason,
        matched_terms=classification.matched_terms,
    )


def _is_direct_sql(raw: str) -> bool:
    return bool(_SQL_START.match(raw) or _CREATE_SQL.match(raw) or _SHOW_SQL.match(raw) or _DESCRIBE_SQL.match(raw))


def _is_safe_legacy_after_llm_failure(raw: str, legacy_sql: str) -> bool:
    """Avoid executing business-language text as raw SQL after provider errors."""
    if legacy_sql.strip().rstrip(";").lower() == raw.strip().rstrip(";").lower():
        return _is_direct_sql(raw)
    return True


def _parse_json_object(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("LLM response must be a JSON object.")
    return data


def _string_list(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    return [str(value)]


def _coerce_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default
