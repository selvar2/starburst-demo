def test_nl2sql_service_preserves_direct_sql():
    from nl2sql_service import NL2SQLService

    service = NL2SQLService(provider=None, legacy_translator=lambda msg, cat, sch: None)

    result = service.translate(
        "SELECT * FROM mcp2ohio.sales.orders",
        catalog="mcp2ohio",
        schema="sales",
        schema_data={"schemas": []},
    )

    assert result.sql == "SELECT * FROM mcp2ohio.sales.orders"
    assert result.source == "sql"


def test_nl2sql_service_uses_legacy_when_provider_missing():
    from nl2sql_service import NL2SQLService

    service = NL2SQLService(
        provider=None,
        legacy_translator=lambda msg, cat, sch: f"SELECT * FROM {cat}.{sch}.orders LIMIT 100",
    )

    result = service.translate(
        "show orders",
        catalog="mcp2ohio",
        schema="sales",
        schema_data={"schemas": []},
    )

    assert result.sql == "SELECT * FROM mcp2ohio.sales.orders LIMIT 100"
    assert result.source == "legacy"


def test_nl2sql_service_parses_llm_json_and_validates():
    from llm_provider import MockLLMProvider
    from nl2sql_service import NL2SQLService

    provider = MockLLMProvider(
        '{"sql":"SELECT region, revenue FROM mcp2ohio.sales.orders",'
        '"confidence":0.91,"assumptions":["using orders"],'
        '"chart":"bar","followups":["show top regions"]}'
    )
    service = NL2SQLService(provider=provider, legacy_translator=lambda msg, cat, sch: None)

    schema_data = {
        "schemas": [
            {
                "name": "sales",
                "tables": [
                    {
                        "name": "orders",
                        "columns": [
                            {"name": "region", "type": "varchar"},
                            {"name": "revenue", "type": "double"},
                        ],
                    }
                ],
            }
        ]
    }

    result = service.translate("sales by region", "mcp2ohio", "sales", schema_data)

    assert result.sql == "SELECT region, revenue FROM mcp2ohio.sales.orders LIMIT 100"
    assert result.source == "llm"
    assert result.confidence == 0.91
    assert result.assumptions == ["using orders"]
    assert result.chart == "bar"
