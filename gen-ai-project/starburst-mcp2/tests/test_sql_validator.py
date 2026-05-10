import pytest


def test_validate_generated_sql_adds_limit():
    from metadata_service import SchemaContext
    from sql_validator import validate_generated_sql

    context = SchemaContext(text="", tables={("mcp2ohio", "sales", "orders"): {"region", "revenue"}})

    result = validate_generated_sql(
        "SELECT region, revenue FROM mcp2ohio.sales.orders",
        context,
        default_limit=50,
    )

    assert result.sql == "SELECT region, revenue FROM mcp2ohio.sales.orders LIMIT 50"


def test_validate_generated_sql_blocks_drop():
    from sql_validator import SQLValidationError, validate_generated_sql

    with pytest.raises(SQLValidationError):
        validate_generated_sql("DROP TABLE mcp2ohio.sales.orders", None)


def test_validate_generated_sql_blocks_multi_statement():
    from sql_validator import SQLValidationError, validate_generated_sql

    with pytest.raises(SQLValidationError):
        validate_generated_sql("SELECT 1; SELECT 2", None)


def test_validate_generated_sql_rejects_unknown_table():
    from metadata_service import SchemaContext
    from sql_validator import SQLValidationError, validate_generated_sql

    context = SchemaContext(text="", tables={("mcp2ohio", "sales", "orders"): {"region"}})

    with pytest.raises(SQLValidationError):
        validate_generated_sql("SELECT * FROM mcp2ohio.sales.missing", context)


def test_validate_generated_sql_rejects_unknown_selected_column():
    from metadata_service import SchemaContext
    from sql_validator import SQLValidationError, validate_generated_sql

    context = SchemaContext(text="", tables={("mcp2ohio", "sales", "orders"): {"region"}})

    with pytest.raises(SQLValidationError):
        validate_generated_sql("SELECT revenue FROM mcp2ohio.sales.orders", context)


def test_validate_generated_sql_rejects_literal_answer_without_table():
    from sql_validator import SQLValidationError, validate_generated_sql

    with pytest.raises(SQLValidationError):
        validate_generated_sql("SELECT 'AWS is Amazon Web Services' AS answer", None)
