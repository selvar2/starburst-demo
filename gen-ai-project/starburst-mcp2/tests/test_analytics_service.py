def test_build_result_insights_summarizes_rows_and_columns():
    from analytics_service import build_result_insights

    result = build_result_insights(
        message="top products by revenue",
        sql="SELECT product, revenue FROM mcp2ohio.sales.orders LIMIT 5",
        columns=["product", "revenue"],
        rows=[["A", 100.0], ["B", 80.0]],
        chart="bar",
    )

    assert "2 rows" in result.summary
    assert result.insights
    assert result.dashboard["cards"][0]["type"] == "metric"
    assert result.kpis[0]["label"] == "Revenue"
    assert result.kpis[0]["value"] == "$180"


def test_demo_tables_render_presentation_ready_metrics_and_bullets():
    from analytics_service import build_result_insights
    from demo_data_generator import CATALOG, SCHEMA, build_specs

    expected_values = {
        ("customer_engagement", "Feature Adoption"): "64.1%",
        ("pricing_metrics", "Price Elasticity"): "-0.98",
        ("review_analytics", "Positive Sentiment"): "83.2%",
        ("revenue_forecast", "Forecast Confidence"): "82.9%",
        ("executive_summary", "Annual Recurring Revenue"): "$184.5M",
        ("executive_summary", "Gross Margin"): "64.2%",
        ("executive_summary", "Net Revenue Retention"): "131.0%",
        ("executive_summary", "Logo Churn"): "3.4%",
        ("kpi_metrics", "Revenue"): "$184.5M",
        ("kpi_metrics", "Gross Profit"): "$118.5M",
        ("kpi_metrics", "Customer LTV"): "$68.4K",
        ("kpi_metrics", "Forecast Accuracy"): "91.0%",
    }

    for spec in build_specs(CATALOG, SCHEMA):
        columns = [name for name, _ in spec.columns]
        rows = [[row.get(col) for col in columns] for row in spec.rows[:100]]
        result = build_result_insights(
            message=f'SELECT * FROM "{CATALOG}"."{SCHEMA}"."{spec.name}" LIMIT 100',
            sql=f'SELECT * FROM "{CATALOG}"."{SCHEMA}"."{spec.name}" LIMIT 100',
            columns=columns,
            rows=rows,
            chart="line",
        )

        assert result.kpis, spec.name
        assert result.insights, spec.name

        for insight in result.insights:
            lowered = insight.lower()
            assert "returned rows" not in lowered, (spec.name, insight)
            assert "row high" not in lowered, (spec.name, insight)
            assert "first returned row" not in lowered, (spec.name, insight)

        kpis_by_label = {card["label"]: card["value"] for card in result.kpis}
        for (table_name, label), expected in expected_values.items():
            if table_name == spec.name:
                assert kpis_by_label[label] == expected

        if spec.name == "customer_engagement":
            assert "Engagement Score averaged 82.2, reaching a high of 96.0." in result.insights
            assert "Engagement Score increased by 13.0% across the selected range." in result.trend_highlights

        bad_values = {"0.64", "1.31", "0.03", "0.91", "0.83"}
        for card in result.kpis[:6]:
            assert not str(card["value"]).startswith("$-"), (spec.name, card)
            assert str(card["value"]) not in bad_values, (spec.name, card)
