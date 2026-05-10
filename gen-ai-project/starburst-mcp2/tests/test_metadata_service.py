def test_build_schema_context_includes_tables_and_columns():
    from metadata_service import build_schema_context

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

    context = build_schema_context(schema_data, catalog="mcp2ohio", default_schema="sales")

    assert "mcp2ohio.sales.orders" in context.text
    assert "region varchar" in context.text
    assert "revenue double" in context.text
    assert ("mcp2ohio", "sales", "orders") in context.tables
    assert "revenue" in context.tables[("mcp2ohio", "sales", "orders")]
