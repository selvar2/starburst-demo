# Enterprise AI Analytics Demo Prompts

Generated: `2026-05-10 21:48:21 IST`

Purpose: copy-ready leadership demo prompts for technical SQL users and non-technical natural language users.

---

# SECTION 1 — EXECUTIVE DEMO SCENARIOS

## Demo 1 — Executive Revenue Command Center

**User Type:** CEO / Executive Leadership

**Prompt:**

```text
Build an executive revenue dashboard showing sales, profit, regional performance, monthly trends, and top products.
```

**Expected Visualization:**

```text
KPI cards, bar charts, line charts, ranked tables
```

**Expected Insights:**

```text
Best region, revenue trend, profit contribution, top products
```

**Business Value:**

```text
Shows how leadership can get a board-ready view from one natural language request.
```

## Demo 2 — Customer Retention & Churn Risk

**User Type:** Customer Success Leader

**Prompt:**

```text
Summarize customer churn trends and show which regions or segments have the highest churn risk.
```

**Expected Visualization:**

```text
Line chart, churn KPI cards, segment comparison table
```

**Expected Insights:**

```text
Churn trend, highest-risk segments, saved revenue opportunities
```

**Business Value:**

```text
Demonstrates proactive risk detection from enterprise data.
```

## Demo 3 — Product Performance Intelligence

**User Type:** Product / Sales Leader

**Prompt:**

```text
Show top products by revenue, profit margin, reviews, and inventory performance.
```

**Expected Visualization:**

```text
Bar chart, KPI cards, product ranking table
```

**Expected Insights:**

```text
Best products, underperformers, margin opportunities
```

**Business Value:**

```text
Helps leadership connect product performance with revenue and inventory.
```

## Demo 4 — Financial Growth Review

**User Type:** CFO / Finance Team

**Prompt:**

```text
Build a profitability dashboard showing revenue, expenses, margin, forecast, and quarterly growth.
```

**Expected Visualization:**

```text
KPI cards, quarterly trend chart, expense breakdown
```

**Expected Insights:**

```text
Margin movement, forecast confidence, growth drivers
```

**Business Value:**

```text
Shows AI-assisted financial review without manual BI setup.
```

---

# SECTION 2 — TECHNICAL SQL QUERIES

## 1. Sales By Region

**User Type:** Data Analyst

**SQL:**

```sql
SELECT
    "region",
    SUM("revenue") AS total_revenue,
    SUM("profit") AS total_profit,
    SUM("units_sold") AS total_units
FROM "mcp2ohio"."test_writes"."sales_by_region"
GROUP BY "region"
ORDER BY total_revenue DESC;
```

**Expected Visualization:**

```text
Bar chart
```

**Expected Insights:**

```text
Top regions, profit contribution
```

**Business Value:**

```text
Shows regional performance instantly.
```

## 2. Monthly Sales Trend

**User Type:** BI Analyst

**SQL:**

```sql
SELECT
    "period_month",
    SUM("revenue") AS monthly_revenue,
    SUM("profit") AS monthly_profit
FROM "mcp2ohio"."test_writes"."monthly_sales"
GROUP BY "period_month"
ORDER BY "period_month";
```

**Expected Visualization:**

```text
Line chart
```

**Expected Insights:**

```text
Growth trend, peaks, dips
```

**Business Value:**

```text
Executive-ready revenue trend.
```

## 3. Top Products By Revenue

**User Type:** Sales Analyst

**SQL:**

```sql
SELECT
    "product_name",
    "category",
    "revenue",
    "profit_margin"
FROM "mcp2ohio"."test_writes"."product_sales"
ORDER BY "revenue" DESC
LIMIT 10;
```

**Expected Visualization:**

```text
Bar chart
```

**Expected Insights:**

```text
Top products, margin leaders
```

**Business Value:**

```text
Prioritizes revenue-generating products.
```

## 4. Churn Risk Analysis

**User Type:** Data Analyst

**SQL:**

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

**Expected Visualization:**

```text
Line or bar chart
```

**Expected Insights:**

```text
Highest churn risk, revenue exposure
```

**Business Value:**

```text
Supports retention planning.
```

## 5. Executive KPI Summary

**User Type:** Architect / Analyst

**SQL:**

```sql
SELECT *
FROM "mcp2ohio"."test_writes"."executive_summary"
LIMIT 100;
```

**Expected Visualization:**

```text
KPI cards
```

**Expected Insights:**

```text
Actual vs target, executive performance summary
```

**Business Value:**

```text
Demonstrates leadership-ready KPI reporting.
```

## 6. Product Ranking With Window Function

**User Type:** Advanced SQL User

**SQL:**

```sql
SELECT
    "category",
    "product_name",
    "revenue",
    RANK() OVER (
        PARTITION BY "category"
        ORDER BY "revenue" DESC
    ) AS category_rank
FROM "mcp2ohio"."test_writes"."product_sales"
ORDER BY "category", category_rank;
```

**Expected Visualization:**

```text
Ranked table, bar chart
```

**Expected Insights:**

```text
Top products by category
```

**Business Value:**

```text
Shows advanced SQL support.
```

## 7. Quarterly Growth Analysis

**User Type:** Finance Analyst

**SQL:**

```sql
SELECT
    "quarter",
    "revenue",
    "growth_rate",
    "profit_margin"
FROM "mcp2ohio"."test_writes"."quarterly_growth"
ORDER BY "quarter";
```

**Expected Visualization:**

```text
Line chart, KPI cards
```

**Expected Insights:**

```text
QoQ growth, margin trend
```

**Business Value:**

```text
Supports CFO-level planning.
```

## 8. Revenue Forecast

**User Type:** Finance / Planning Analyst

**SQL:**

```sql
SELECT
    "period_month",
    "forecast_revenue",
    "forecast_profit",
    "confidence_score"
FROM "mcp2ohio"."test_writes"."revenue_forecast"
ORDER BY "period_month";
```

**Expected Visualization:**

```text
Forecast line chart
```

**Expected Insights:**

```text
Forecast trend, confidence levels
```

**Business Value:**

```text
Shows predictive analytics readiness.
```

---

# SECTION 3 — NON-TECHNICAL NATURAL LANGUAGE PROMPTS

## Sales Analytics

**Prompt:**

```text
Show sales by region and explain which region is performing best.
```

**Expected Visualization:**

```text
Bar chart, KPI cards
```

**Expected Insights:**

```text
Top region, revenue spread
```

**Business Value:**

```text
Lets executives ask business questions directly.
```

**Prompt:**

```text
Show monthly revenue trends and summarize growth.
```

**Expected Visualization:**

```text
Line chart
```

**Expected Insights:**

```text
Growth, decline, seasonality
```

**Business Value:**

```text
Fast trend visibility.
```

**Prompt:**

```text
Which products generated the most revenue?
```

**Expected Visualization:**

```text
Top product bar chart
```

**Expected Insights:**

```text
Product ranking, revenue leaders
```

**Business Value:**

```text
Helps sales and product teams prioritize.
```

## Customer Analytics

**Prompt:**

```text
Show customer engagement trends by segment.
```

**Expected Visualization:**

```text
Line chart, segment table
```

**Expected Insights:**

```text
Best and weakest segments
```

**Business Value:**

```text
Improves customer strategy.
```

**Prompt:**

```text
Which customer segments have the highest lifetime value?
```

**Expected Visualization:**

```text
Bar chart, KPI cards
```

**Expected Insights:**

```text
High-value segments
```

**Business Value:**

```text
Supports targeted investment.
```

## Churn Analytics

**Prompt:**

```text
Analyze churn rate and saved revenue by region.
```

**Expected Visualization:**

```text
Bar or line chart
```

**Expected Insights:**

```text
Highest churn, saved revenue opportunities
```

**Business Value:**

```text
Helps retention teams act faster.
```

**Prompt:**

```text
Show churn trends over time and identify risk areas.
```

**Expected Visualization:**

```text
Line chart, risk KPI cards
```

**Expected Insights:**

```text
Churn spikes, risky periods
```

**Business Value:**

```text
Reduces revenue leakage.
```

---

# SECTION 4 — DASHBOARD GENERATION PROMPTS

## Executive Sales Dashboard

**Prompt:**

```text
Build an executive sales dashboard with revenue, profit, regional ranking, monthly trend, and top products.
```

**Expected Visualization:**

```text
KPI cards, bar chart, line chart, ranking table
```

**Expected Insights:**

```text
Best region, growth trend, product leaders
```

**Business Value:**

```text
Demonstrates one-prompt dashboard generation.
```

## Customer Retention Dashboard

**Prompt:**

```text
Create a customer retention dashboard showing churn, retention rate, saved revenue, and high-risk segments.
```

**Expected Visualization:**

```text
KPI cards, churn trend, segment comparison
```

**Expected Insights:**

```text
Retention risks, churn drivers
```

**Business Value:**

```text
Shows AI-driven customer intelligence.
```

## Product Performance Dashboard

**Prompt:**

```text
Build a product performance dashboard showing revenue, margin, inventory, pricing, and review performance.
```

**Expected Visualization:**

```text
Product bar charts, KPI cards, inventory table
```

**Expected Insights:**

```text
Top products, margin gaps, stock risks
```

**Business Value:**

```text
Connects product, finance, and operations.
```

## CFO Profitability Dashboard

**Prompt:**

```text
Build a profitability dashboard showing revenue, expenses, forecast, margin, and quarterly growth.
```

**Expected Visualization:**

```text
Financial KPI cards, trend charts, forecast panel
```

**Expected Insights:**

```text
Profitability drivers, expense risks
```

**Business Value:**

```text
Shows finance-grade analytics automation.
```

---

# SECTION 5 — KPI & INSIGHT PROMPTS

## Executive KPI Performance

**Prompt:**

```text
Summarize executive KPI performance and highlight metrics above or below target.
```

**Expected Visualization:**

```text
KPI cards
```

**Expected Insights:**

```text
Target gaps, top metrics
```

**Business Value:**

```text
Leadership-ready KPI review.
```

## Latest Period KPI Snapshot

**Prompt:**

```text
Show revenue, profit, and margin KPIs for the latest period.
```

**Expected Visualization:**

```text
KPI cards, summary panel
```

**Expected Insights:**

```text
Revenue health, margin status
```

**Business Value:**

```text
Fast executive snapshot.
```

## Strongest And Weakest Metrics

**Prompt:**

```text
Identify the strongest and weakest business metrics.
```

**Expected Visualization:**

```text
KPI ranking cards
```

**Expected Insights:**

```text
Best/worst performers
```

**Business Value:**

```text
Helps leaders focus attention.
```

## Explain Result

**Prompt:**

```text
Explain the key business insights from this result.
```

**Expected Visualization:**

```text
AI summary and insight panel
```

**Expected Insights:**

```text
Trends, outliers, risks
```

**Business Value:**

```text
Turns tables into executive narrative.
```

---

# SECTION 6 — DRILL-DOWN ANALYTICS PROMPTS

## North America Sales Drill-Down

**Prompt:**

```text
Drill down into North America sales by product and quarter.
```

**Expected Visualization:**

```text
Filtered table, bar chart
```

**Expected Insights:**

```text
Product-level regional drivers
```

**Business Value:**

```text
Moves from executive view to operational detail.
```

## Highest Revenue Region Breakdown

**Prompt:**

```text
Show monthly breakdown for the highest revenue region.
```

**Expected Visualization:**

```text
Line chart
```

**Expected Insights:**

```text
Seasonal performance
```

**Business Value:**

```text
Explains what is driving regional success.
```

## Churn By Region And Segment

**Prompt:**

```text
Expand churn analysis by region and customer segment.
```

**Expected Visualization:**

```text
Segment comparison chart
```

**Expected Insights:**

```text
High-risk segments
```

**Business Value:**

```text
Helps retention teams prioritize action.
```

## Product Regional Underperformance

**Prompt:**

```text
Compare product performance across regions and identify underperformers.
```

**Expected Visualization:**

```text
Multi-dimensional table, bar chart
```

**Expected Insights:**

```text
Product-region gaps
```

**Business Value:**

```text
Supports sales and product strategy.
```

---

# SECTION 7 — ADVANCED ENTERPRISE ANALYTICS DEMOS

## AI Anomaly Detection

**User Type:** Executive / Analyst

**Prompt:**

```text
Detect unusual revenue patterns and explain possible business risks.
```

**Expected Visualization:**

```text
Trend chart, anomaly summary
```

**Expected Insights:**

```text
Spikes, drops, risk periods
```

**Business Value:**

```text
Demonstrates AI-driven monitoring.
```

## Forecast Review

**User Type:** Finance Leader

**Prompt:**

```text
Compare actual revenue with forecast and summarize where performance is ahead or behind plan.
```

**Expected Visualization:**

```text
Actual vs forecast line chart
```

**Expected Insights:**

```text
Forecast variance, risk areas
```

**Business Value:**

```text
Shows planning and forecasting intelligence.
```

## Multi-Dimensional Revenue Analysis

**User Type:** Business Analyst

**Prompt:**

```text
Compare revenue by region, product category, customer segment, and quarter.
```

**Expected Visualization:**

```text
Pivot-style table, grouped bar chart
```

**Expected Insights:**

```text
Revenue drivers across dimensions
```

**Business Value:**

```text
Shows enterprise-scale analytical flexibility.
```

## Operational Performance Review

**User Type:** COO / Operations

**Prompt:**

```text
Show operational metrics and identify bottlenecks or underperforming areas.
```

**Expected Visualization:**

```text
KPI cards, operational ranking table
```

**Expected Insights:**

```text
Efficiency gaps, operational risks
```

**Business Value:**

```text
Supports operational decision-making.
```

## Leadership Closing Demo

**User Type:** Executive

**Prompt:**

```text
Create a leadership dashboard showing revenue growth, profitability, churn risk, customer engagement, product performance, and forecast outlook.
```

**Expected Visualization:**

```text
Executive panel with KPIs, charts, summaries, drill-downs
```

**Expected Insights:**

```text
Business health, growth risks, priorities
```

**Business Value:**

```text
Shows the platform as an AI-powered enterprise BI command center.
```
