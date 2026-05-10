# Working Demo Prompts Based On Live Data Sources

Generated: `2026-05-10 23:40:21 IST`

Catalog: `mcp2ohio`

Schema: `test_writes`

Purpose: leadership-safe demo prompts and SQL queries using verified tables and columns from the running application.

---

# SECTION 1 — EXECUTIVE DEMO SCENARIOS

## Sales Performance

**User Type:** Executive / Sales Leader

**Prompt:**

```text
Show all data from sales_by_region
```

**Expected Output:**

```text
Table, bar chart, KPI summary, regional insights
```

**Prompt:**

```text
Group by region from sales_by_region
```

**Expected Output:**

```text
Regional revenue comparison, bar chart, executive summary
```

**Prompt:**

```text
Sum of revenue from sales_by_region
```

**Expected Output:**

```text
Revenue KPI card
```

## Monthly Revenue Trend

**User Type:** CFO / Revenue Leader

**Prompt:**

```text
Show all data from monthly_sales
```

**Expected Output:**

```text
Monthly sales table, trend chart, KPI cards
```

**Prompt:**

```text
Group by period_month from monthly_sales
```

**Expected Output:**

```text
Monthly trend chart
```

**Prompt:**

```text
Sum of revenue from monthly_sales
```

**Expected Output:**

```text
Total revenue KPI
```

## Customer & Churn Review

**User Type:** Customer Success Leader

**Prompt:**

```text
Show all data from churn_metrics
```

**Expected Output:**

```text
Churn table, line chart, churn insights
```

**Prompt:**

```text
Group by region from churn_metrics
```

**Expected Output:**

```text
Churn by region, risk comparison
```

**Prompt:**

```text
Average of churn_rate from churn_metrics
```

**Expected Output:**

```text
Churn KPI card
```

---

# SECTION 2 — TECHNICAL SQL QUERIES

## Sales By Region

```sql
SELECT
    "region",
    SUM("revenue") AS total_revenue,
    SUM("profit") AS total_profit,
    SUM("units_sold") AS total_units_sold
FROM "mcp2ohio"."test_writes"."sales_by_region"
GROUP BY "region"
ORDER BY total_revenue DESC;
```

## Monthly Sales Trend

```sql
SELECT
    "period_month",
    SUM("revenue") AS total_revenue,
    SUM("gross_profit") AS total_gross_profit,
    SUM("pipeline_value") AS total_pipeline_value
FROM "mcp2ohio"."test_writes"."monthly_sales"
GROUP BY "period_month"
ORDER BY "period_month";
```

## Product Revenue

```sql
SELECT
    "product_name",
    "product_segment",
    "revenue",
    "units_sold",
    "average_deal_size",
    "gross_margin",
    "win_rate"
FROM "mcp2ohio"."test_writes"."product_sales"
ORDER BY "revenue" DESC
LIMIT 10;
```

## Customer Segment Revenue

```sql
SELECT
    "customer_segment",
    SUM("revenue") AS total_revenue,
    AVG("ltv") AS avg_ltv,
    AVG("average_order_value") AS avg_order_value,
    SUM("customer_count") AS total_customers
FROM "mcp2ohio"."test_writes"."customer_sales"
GROUP BY "customer_segment"
ORDER BY total_revenue DESC;
```

## Churn Risk

```sql
SELECT
    "period_month",
    "region",
    "churn_rate",
    "churned_revenue",
    "saved_revenue",
    "risk_score"
FROM "mcp2ohio"."test_writes"."churn_metrics"
ORDER BY "risk_score" DESC
LIMIT 100;
```

## Executive KPI Summary

```sql
SELECT
    "kpi_name",
    "actual_value",
    "target_value",
    "benchmark_value",
    "trend_direction",
    "executive_note"
FROM "mcp2ohio"."test_writes"."executive_summary"
LIMIT 100;
```

## Operational Metrics

```sql
SELECT
    "operation_area",
    "actual_value",
    "target_value",
    "sla_rate",
    "incident_count",
    "automation_rate"
FROM "mcp2ohio"."test_writes"."operational_metrics"
ORDER BY "incident_count" DESC;
```

---

# SECTION 3 — WORKING NATURAL LANGUAGE PROMPTS

## Schema And Discovery

```text
Show all tables
```

```text
Describe sales_by_region
```

```text
Describe monthly_sales
```

```text
Describe product_sales
```

```text
Describe customer_sales
```

```text
Describe churn_metrics
```

```text
Describe executive_summary
```

```text
Describe operational_metrics
```

## Sales Analytics

```text
Show all data from sales_by_region
```

```text
Count rows in sales_by_region
```

```text
Group by region from sales_by_region
```

```text
Sum of revenue from sales_by_region
```

```text
Average of profit from sales_by_region
```

```text
Top 10 revenue from sales_by_region
```

## Monthly Sales Analytics

```text
Show all data from monthly_sales
```

```text
Group by period_month from monthly_sales
```

```text
Sum of revenue from monthly_sales
```

## Product Analytics

```text
Show all data from product_sales
```

```text
Group by product_segment from product_sales
```

```text
Sum of revenue from product_sales
```

## Customer Analytics

```text
Show all data from customer_sales
```

```text
Group by customer_segment from customer_sales
```

```text
Sum of revenue from customer_sales
```

## Churn Analytics

```text
Show all data from churn_metrics
```

```text
Group by region from churn_metrics
```

```text
Average of churn_rate from churn_metrics
```

## Executive KPI Analytics

```text
Show all data from executive_summary
```

```text
Group by kpi_name from executive_summary
```

## Operational Analytics

```text
Show all data from operational_metrics
```

```text
Group by operation_area from operational_metrics
```

---

# SECTION 4 — DASHBOARD GENERATION PROMPTS

Use these safer dashboard-style prompts because they map directly to current working query patterns.

```text
Show all data from sales_by_region
```

```text
Group by region from sales_by_region
```

```text
Show all data from monthly_sales
```

```text
Group by period_month from monthly_sales
```

```text
Show all data from churn_metrics
```

```text
Group by region from churn_metrics
```

---

# SECTION 5 — KPI & INSIGHT PROMPTS

```text
Show all data from executive_summary
```

```text
Group by kpi_name from executive_summary
```

```text
Show all data from kpi_metrics
```

```text
Group by business_unit from kpi_metrics
```

```text
Show all data from operational_metrics
```

```text
Group by operation_area from operational_metrics
```

---

# SECTION 6 — DRILL-DOWN ANALYTICS PROMPTS

```text
Group by region from sales_by_region
```

```text
Group by period_month from monthly_sales
```

```text
Group by product_segment from product_sales
```

```text
Group by customer_segment from customer_sales
```

```text
Group by region from churn_metrics
```

```text
Group by operation_area from operational_metrics
```

---

# SECTION 7 — ADVANCED ENTERPRISE ANALYTICS DEMOS

For advanced demos, prefer SQL because it is deterministic.

## Product Ranking

```sql
SELECT
    "product_segment",
    "product_name",
    "revenue",
    "gross_margin",
    RANK() OVER (
        PARTITION BY "product_segment"
        ORDER BY "revenue" DESC
    ) AS revenue_rank
FROM "mcp2ohio"."test_writes"."product_sales"
ORDER BY "product_segment", revenue_rank;
```

## Monthly Moving Average

```sql
SELECT
    "period_month",
    "revenue",
    AVG("revenue") OVER (
        ORDER BY "period_month"
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS revenue_3_month_moving_avg
FROM "mcp2ohio"."test_writes"."monthly_sales"
ORDER BY "period_month";
```

## Forecast Variance

```sql
SELECT
    "period_month",
    "actual_revenue",
    "forecast_revenue",
    ("actual_revenue" - "forecast_revenue") AS forecast_variance,
    "forecast_confidence",
    "pipeline_coverage"
FROM "mcp2ohio"."test_writes"."revenue_forecast"
ORDER BY "period_month";
```

---

# Recommended Leadership Demo Sequence

```text
Show all data from sales_by_region
```

```text
Group by region from sales_by_region
```

```text
Show all data from monthly_sales
```

```text
Group by period_month from monthly_sales
```

```text
Show all data from churn_metrics
```

```text
Average of churn_rate from churn_metrics
```
