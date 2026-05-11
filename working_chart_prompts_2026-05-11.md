# Working Chart-Safe Prompts For StarQuery / Starburst Demo

Generated: `2026-05-11`

Catalog: `mcp2ohio`

Schema: `test_writes`

Purpose: chart-safe demo prompts and SQL examples for the StarQuery / Starburst application.

Reference file used: `working_prompts_2026-05-10-234021-ist.md`

Important chart rule: prompts that return only one row and one numeric value are intentionally excluded. For example, `Sum of revenue from sales_by_region` can execute as `SELECT SUM(revenue) AS total_revenue FROM mcp2ohio.test_writes.sales_by_region LIMIT 100`, but that result is a KPI/metric shape, not a chart-friendly dataset.

---

# 1. Natural Language SELECT Prompts That Definitely Provide Charts

Use these prompts for read-only chart demos. Each prompt is designed to return multiple rows with at least one label/dimension and at least one numeric measure.

## Regional Revenue Chart

**Prompt:**

```text
Show all data from sales_by_region
```

**Expected chart:** `bar`

**Why this charts:** multiple region/quarter rows with numeric revenue, units sold, and profit measures.

## Regional Sales Trend Chart

**Prompt:**

```text
Show all data from regional_sales
```

**Expected chart:** `bar`

**Why this charts:** multiple region rows with numeric revenue, gross profit, growth rate, target attainment, and strategic account measures.

## Monthly Revenue Trend Chart

**Prompt:**

```text
Show all data from monthly_sales
```

**Expected chart:** `line`

**Why this charts:** `period_month` is a time/month dimension with numeric revenue, gross profit, pipeline value, and customer measures.

## Product Revenue Leaderboard Chart

**Prompt:**

```text
Top 10 revenue from product_sales
```

**Expected chart:** `bar`

**Why this charts:** returns multiple products ordered by revenue with numeric revenue, units sold, average deal size, gross margin, and win rate.

## Customer Segment Revenue Chart

**Prompt:**

```text
Show all data from customer_segments
```

**Expected chart:** `bar`

**Why this charts:** returns multiple customer segments with numeric accounts, revenue, LTV, churn rate, and NPS.

## Churn Risk Trend Chart

**Prompt:**

```text
Show all data from churn_metrics
```

**Expected chart:** `line`

**Why this charts:** `period_month` is a time/month dimension with multiple region rows and numeric churn/risk measures.

## Expense Breakdown Chart

**Prompt:**

```text
Show all data from expense_breakdown
```

**Expected chart:** `bar`

**Why this charts:** returns expense categories with numeric expense, budget, variance, and share measures.

## Quarterly Growth Chart

**Prompt:**

```text
Show all data from quarterly_growth
```

**Expected chart:** `bar`

**Why this charts:** returns fiscal quarters with numeric revenue, YoY growth, QoQ growth, margin, and customer growth measures.

## Revenue Forecast Trend Chart

**Prompt:**

```text
Show all data from revenue_forecast
```

**Expected chart:** `line`

**Why this charts:** `period_month` is a time/month dimension with actual revenue, forecast revenue, confidence, and pipeline coverage.

---

# 2. SQL SELECT Prompts That Definitely Provide Charts

These SQL prompts are read-only, single-statement queries. They include `LIMIT` and return chart-compatible datasets.

Validation summary from existing prompt references, deterministic demo data, and chart rules:

| SQL Prompt | Validated Rows | Expected Chart |
|---|---:|---|
| Sales by region | multiple rows | `bar` |
| Regional revenue by region | 6 | `pie` |
| Monthly revenue trend | 24 | `line` |
| Top products by revenue | 8 | `bar` |
| Customer segment revenue | 4 | `pie` |
| Churn risk by month and region | 100 | `line` |
| Expense breakdown by category | 6 | `bar` |
| Quarterly revenue growth | 8 | `bar` |
| Revenue forecast by month | 24 | `line` |

## Sales By Region

```sql
SELECT
    region,
    quarter,
    revenue,
    units_sold,
    profit
FROM mcp2ohio.test_writes.sales_by_region
ORDER BY revenue DESC
LIMIT 20
```

## Regional Revenue By Region

```sql
SELECT
    region,
    SUM(revenue) AS total_revenue,
    SUM(gross_profit) AS total_gross_profit,
    SUM(strategic_accounts) AS total_strategic_accounts
FROM mcp2ohio.test_writes.regional_sales
GROUP BY region
ORDER BY total_revenue DESC
LIMIT 100
```

## Monthly Revenue Trend

```sql
SELECT
    period_month,
    SUM(revenue) AS total_revenue,
    SUM(gross_profit) AS total_gross_profit,
    SUM(pipeline_value) AS total_pipeline_value
FROM mcp2ohio.test_writes.monthly_sales
GROUP BY period_month
ORDER BY period_month
LIMIT 100
```

## Top Products By Revenue

```sql
SELECT
    product_name,
    revenue,
    units_sold,
    gross_margin,
    win_rate
FROM mcp2ohio.test_writes.product_sales
ORDER BY revenue DESC
LIMIT 10
```

## Customer Segment Revenue

```sql
SELECT
    customer_segment,
    SUM(revenue) AS total_revenue,
    SUM(accounts) AS total_accounts,
    AVG(ltv) AS avg_ltv,
    AVG(nps) AS avg_nps
FROM mcp2ohio.test_writes.customer_segments
GROUP BY customer_segment
ORDER BY total_revenue DESC
LIMIT 100
```

## Churn Risk By Month And Region

```sql
SELECT
    period_month,
    region,
    churn_rate,
    churned_revenue,
    saved_revenue,
    risk_score
FROM mcp2ohio.test_writes.churn_metrics
ORDER BY risk_score DESC
LIMIT 100
```

## Expense Breakdown By Category

```sql
SELECT
    expense_category,
    expense_amount,
    budget_amount,
    variance_amount,
    expense_share
FROM mcp2ohio.test_writes.expense_breakdown
ORDER BY expense_amount DESC
LIMIT 100
```

## Quarterly Revenue Growth

```sql
SELECT
    fiscal_quarter,
    revenue,
    yoy_growth,
    qoq_growth,
    gross_margin,
    customer_growth
FROM mcp2ohio.test_writes.quarterly_growth
ORDER BY fiscal_quarter
LIMIT 100
```

## Revenue Forecast By Month

```sql
SELECT
    period_month,
    actual_revenue,
    forecast_revenue,
    forecast_confidence,
    pipeline_coverage
FROM mcp2ohio.test_writes.revenue_forecast
ORDER BY period_month
LIMIT 100
```

---

# 3. Natural Language CREATE, INSERT, And UPDATE Prompts

Do not test this section during chart validation. These are write-operation examples only.

## CREATE Prompts

```text
Create a scratch schema
```

```text
Create a sandbox schema for testing
```

```text
Create a scratch table for dashboard testing
```

```text
Create a customer metrics table with id and revenue
```

```text
Create an executive KPI table
```

## INSERT Prompts

```text
Add a new row into catalog mcp2ohio, schema test_writes, table scratch_nl_table with id 101, label regional_chart_demo
```

```text
Insert a record into mcp2ohio.test_writes.customer_metrics_nl where customer_id = 9001, customer_name = Acme Enterprise, revenue = 125000.50, growth_percent = 0.18
```

```text
In catalog mcp2ohio, schema test_writes, add a row to table executive_kpis_nl with kpi_name Annual Recurring Revenue, current_value 184500000, target_value 172000000, trend_direction up
```

## UPDATE Prompts

```text
Update mcp2ohio.test_writes.scratch_nl_table and set label = regional_chart_ready where id = 101
```

```text
In catalog mcp2ohio, schema test_writes, table customer_metrics_nl, update the row where customer_id = 9001 and set revenue to 130000.75
```

```text
Change trend_direction to up in catalog mcp2ohio, schema test_writes, table executive_kpis_nl for the row where kpi_name = 'Annual Recurring Revenue'
```

---

# 4. SQL CREATE, INSERT, And UPDATE Prompts

Do not test this section during chart validation. These are write-operation examples only.

## CREATE SQL Prompts

```sql
CREATE SCHEMA IF NOT EXISTS mcp2ohio.sandbox_schema
```

```sql
CREATE TABLE IF NOT EXISTS mcp2ohio.test_writes.scratch_nl_table (
    id INTEGER,
    label VARCHAR
)
```

```sql
CREATE TABLE IF NOT EXISTS mcp2ohio.test_writes.customer_metrics_nl (
    customer_id BIGINT,
    customer_name VARCHAR,
    revenue DOUBLE,
    growth_percent DOUBLE
)
```

```sql
CREATE TABLE IF NOT EXISTS mcp2ohio.test_writes.executive_kpis_nl (
    kpi_name VARCHAR,
    current_value DOUBLE,
    target_value DOUBLE,
    trend_direction VARCHAR
)
```

## INSERT SQL Prompts

```sql
INSERT INTO mcp2ohio.test_writes.scratch_nl_table (id, label)
VALUES (101, 'regional_chart_demo')
```

```sql
INSERT INTO mcp2ohio.test_writes.customer_metrics_nl (customer_id, customer_name, revenue, growth_percent)
VALUES (9001, 'Acme Enterprise', 125000.50, 0.18)
```

```sql
INSERT INTO mcp2ohio.test_writes.executive_kpis_nl (kpi_name, current_value, target_value, trend_direction)
VALUES ('Annual Recurring Revenue', 184500000, 172000000, 'up')
```

## UPDATE SQL Prompts

```sql
UPDATE mcp2ohio.test_writes.scratch_nl_table
SET label = 'regional_chart_ready'
WHERE id = 101
```

```sql
UPDATE mcp2ohio.test_writes.customer_metrics_nl
SET revenue = 130000.75
WHERE customer_id = 9001
```

```sql
UPDATE mcp2ohio.test_writes.executive_kpis_nl
SET trend_direction = 'up'
WHERE kpi_name = 'Annual Recurring Revenue'
```

---

# Excluded Prompts

The following prompt types are excluded because they do not reliably provide charts:

- `Sum of revenue from sales_by_region`
- `Sum of revenue from monthly_sales`
- `Average of churn_rate from churn_metrics`
- Any single aggregate query that returns only one numeric KPI value
- Any unsafe destructive prompt
