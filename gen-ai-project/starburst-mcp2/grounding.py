"""Enterprise grounding policy for natural-language analytics requests."""

from __future__ import annotations

import re
from dataclasses import dataclass

from metadata_service import SchemaContext


@dataclass(frozen=True)
class QueryClassification:
    query_type: str
    allowed: bool
    reason: str
    matched_terms: list[str]


_GENERAL_KNOWLEDGE_RE = re.compile(
    r"^\s*(what\s+is|what\s+are|who\s+is|define|explain|tell\s+me\s+about|how\s+does)\b",
    re.IGNORECASE,
)
_ENTERPRISE_ACTION_RE = re.compile(
    r"\b(show|list|count|sum|avg|average|min|max|top|bottom|trend|compare|group|filter|dashboard|chart|kpi|sales|revenue|profit|rows?|columns?|describe)\b",
    re.IGNORECASE,
)


def classify_enterprise_query(message: str, schema_context: SchemaContext) -> QueryClassification:
    text = message.strip()
    terms = _metadata_terms(schema_context)
    matched = sorted(term for term in terms if _contains_term(text, term))

    if _GENERAL_KNOWLEDGE_RE.search(text):
        if matched:
            return QueryClassification(
                query_type="enterprise_metadata_lookup",
                allowed=True,
                reason="The request asks for a definition, but it matches available enterprise metadata.",
                matched_terms=matched[:10],
            )
        return QueryClassification(
            query_type="general_knowledge",
            allowed=False,
            reason="The request does not match available enterprise data assets.",
            matched_terms=[],
        )

    if matched or _ENTERPRISE_ACTION_RE.search(text):
        return QueryClassification(
            query_type="enterprise_query",
            allowed=True,
            reason="The request matches enterprise analytics intent or available metadata.",
            matched_terms=matched[:10],
        )

    return QueryClassification(
        query_type="out_of_scope",
        allowed=False,
        reason="The request cannot be answered using available enterprise data.",
        matched_terms=[],
    )


def _metadata_terms(schema_context: SchemaContext) -> set[str]:
    terms: set[str] = set()
    for _catalog, schema, table in schema_context.tables:
        terms.add(schema)
        terms.add(table)
        terms.update(schema_context.tables[(_catalog, schema, table)])
    return {t for t in terms if len(t) > 1}


def _contains_term(text: str, term: str) -> bool:
    normalized = text.lower()
    escaped = re.escape(term.lower())
    return bool(re.search(rf"(?<![a-zA-Z0-9_]){escaped}(?![a-zA-Z0-9_])", normalized))
