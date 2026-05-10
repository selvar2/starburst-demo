from grounding import classify_enterprise_query
from metadata_service import SchemaContext


def test_general_knowledge_without_metadata_match_is_rejected():
    context = SchemaContext(
        text="",
        tables={("mcp2ohio", "test_writes", "products"): {"product_name", "price"}},
    )

    result = classify_enterprise_query("what is aws", context)

    assert result.allowed is False
    assert result.query_type == "general_knowledge"


def test_enterprise_column_request_is_allowed():
    context = SchemaContext(
        text="",
        tables={("mcp2ohio", "test_writes", "products"): {"product_name", "price"}},
    )

    result = classify_enterprise_query("show product_name from products", context)

    assert result.allowed is True
    assert result.query_type == "enterprise_query"
    assert "product_name" in result.matched_terms
