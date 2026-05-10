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
    assert result.dashboard["cards"][0]["type"] == "bar"
