# Working SQL and Natural Language Prompts - 2026-05-11 01:21:18 IST

This file contains only prompts and SQL forms validated against the current `Data Analytics AI` app on `http://127.0.0.1:8001/`.

Sensitive values are not included.

## Environment

```text
Catalog: mcp2ohio
Primary schema: test_writes
Backend: gen-ai-project/starburst-mcp2/app_jwt.py
App URL: http://127.0.0.1:8001/
```

---

# 1. SELECT Operations

## 1.1 SQL SELECT - Show Demo Data

```sql
SELECT * FROM "mcp2ohio"."test_writes"."demo" LIMIT 100;
```

## 1.2 SQL SELECT - Count Rows

```sql
SELECT COUNT(*) AS row_count
FROM "mcp2ohio"."test_writes"."demo";
```

## 1.3 SQL SELECT - Top Demo Amounts

```sql
SELECT "id", "name", "amount"
FROM "mcp2ohio"."test_writes"."demo"
ORDER BY "amount" DESC
LIMIT 20;
```

## 1.4 SQL SELECT - Regional Revenue

```sql
SELECT "region", "quarter", "revenue", "units_sold", "profit"
FROM "mcp2ohio"."test_writes"."sales_by_region"
ORDER BY "revenue" DESC
LIMIT 20;
```

## 1.5 SQL SELECT - Monthly Sales Trend

```sql
SELECT "period_month", "fiscal_year", "revenue", "gross_profit", "pipeline_value"
FROM "mcp2ohio"."test_writes"."monthly_sales"
ORDER BY "period_month"
LIMIT 100;
```

## 1.6 SQL SELECT - Product Sales

```sql
SELECT "product_name", "product_segment", "revenue", "units_sold", "gross_margin", "win_rate"
FROM "mcp2ohio"."test_writes"."product_sales"
ORDER BY "revenue" DESC
LIMIT 20;
```

## 1.7 SQL SELECT - Customer Sales

```sql
SELECT "customer_segment", "region", "revenue", "ltv", "customer_count", "expansion_rate"
FROM "mcp2ohio"."test_writes"."customer_sales"
ORDER BY "revenue" DESC
LIMIT 20;
```

## 1.8 Natural Language SELECT - Tables

```text
show all tables
```

## 1.9 Natural Language SELECT - Describe Demo

```text
describe demo table
```

## 1.10 Natural Language SELECT - Demo Data

```text
show all data from demo
```

## 1.11 Natural Language SELECT - Count Demo Rows

```text
count rows in demo
```

## 1.12 Natural Language SELECT - Regional Revenue

```text
show regional revenue ordered by highest revenue
```

## 1.13 Natural Language SELECT - Product Revenue

```text
show top product sales by revenue
```

## 1.14 Natural Language SELECT - Monthly Sales Trend

```text
show monthly sales trend by revenue
```

---

# 2. CREATE Operations

## 2.1 SQL CREATE SCHEMA

```sql
CREATE SCHEMA "mcp2ohio"."scratch_sch";
```

## 2.2 SQL CREATE TABLE

```sql
CREATE TABLE "mcp2ohio"."test_writes"."scratch_table" (
  "id" INTEGER,
  "label" VARCHAR
);
```

## 2.3 SQL CREATE Customer Metrics Table

```sql
CREATE TABLE IF NOT EXISTS "mcp2ohio"."test_writes"."customer_metrics_nl" (
  "customer_id" BIGINT,
  "customer_name" VARCHAR,
  "revenue" DOUBLE,
  "growth_percent" DOUBLE
);
```

## 2.4 SQL CREATE Dashboard Metrics Table

```sql
CREATE TABLE IF NOT EXISTS "mcp2ohio"."test_writes"."dashboard_metrics_nl" (
  "dashboard_id" VARCHAR,
  "chart_type" VARCHAR,
  "metric_value" DOUBLE,
  "generated_at" TIMESTAMP
);
```

## 2.5 SQL CREATE Executive KPI Table

```sql
CREATE TABLE IF NOT EXISTS "mcp2ohio"."test_writes"."executive_kpis_nl" (
  "kpi_name" VARCHAR,
  "current_value" DOUBLE,
  "target_value" DOUBLE,
  "trend_direction" VARCHAR
);
```

## 2.6 Natural Language CREATE - Scratch Schema

```text
create a scratch schema
```

## 2.7 Natural Language CREATE - Sandbox Schema

```text
create a sandbox schema for testing
```

## 2.8 Natural Language CREATE - Demo Analytics Namespace

```text
create a demo analytics namespace
```

## 2.9 Natural Language CREATE - Customer Metrics Table

```text
create a customer metrics table with id and revenue
```

## 2.10 Natural Language CREATE - Dashboard Metrics Table

```text
create a dashboard metrics table
```

## 2.11 Natural Language CREATE - Product Analytics Table

```text
create a product analytics table
```

## 2.12 Natural Language CREATE - Executive KPI Table

```text
create an executive KPI table
```

## 2.13 Natural Language CREATE - Sandbox Table

```text
create a sandbox table for dashboard testing
```

---

# 3. INSERT Operations

## 3.1 SQL INSERT - Single Demo Row

```sql
INSERT INTO "mcp2ohio"."test_writes"."demo" ("id", "name", "amount")
VALUES (910001, 'executive_revenue_85m', 85000000.00);
```

## 3.2 SQL INSERT - Multi-Row Demo

```sql
INSERT INTO "mcp2ohio"."test_writes"."demo" ("id", "name", "amount")
VALUES
  (910002, 'us_east_sales_120m', 120000000.50),
  (910003, 'europe_growth_98m', 98000000.25),
  (910004, 'enterprise_profit_156m', 156000000.80);
```

## 3.3 SQL INSERT - Regional Sales

```sql
INSERT INTO "mcp2ohio"."test_writes"."sales_by_region"
  ("region", "quarter", "revenue", "units_sold", "profit")
VALUES
  ('Executive West', 'Q4-2027', 88000000.00, 124000, 29500000.00);
```

## 3.4 SQL INSERT - Monthly Sales

```sql
INSERT INTO "mcp2ohio"."test_writes"."monthly_sales"
  ("period_month", "fiscal_year", "revenue", "gross_profit", "pipeline_value", "new_customers", "retained_customers")
VALUES
  ('2027-02', 2027, 210000000.00, 125000000.00, 265000000.00, 4200, 18400);
```

## 3.5 Natural Language INSERT - Demo Row

```text
add a new row into catalog mcp2ohio, schema test_writes, table demo with id 920001, name nl_enterprise_revenue_125m, amount 125000000
```

## 3.6 Natural Language INSERT - Monthly Sales

```text
add a new row into catalog mcp2ohio, schema test_writes, table monthly_sales with period_month 2027-03, fiscal_year 2027, revenue 245000000, gross_profit 151000000, pipeline_value 312000000, new_customers 5100, retained_customers 20600
```

## 3.7 Natural Language INSERT - Regional Sales

```text
add a new row into catalog mcp2ohio, schema test_writes, table sales_by_region with region executive_east, quarter Q1-2028, revenue 132000000, units_sold 156000, profit 48200000
```

## 3.8 Natural Language INSERT - Product Sales

```text
add a new row into catalog mcp2ohio, schema test_writes, table product_sales with product_name executive_ai_platform, product_segment enterprise_ai, revenue 175000000, units_sold 28400, average_deal_size 6161.97, gross_margin 0.72, win_rate 0.81
```

## 3.9 Natural Language INSERT - Customer Sales

```text
add a new row into catalog mcp2ohio, schema test_writes, table customer_sales with customer_segment enterprise_strategic, region north_america, revenue 145000000, ltv 880000, average_order_value 125000, customer_count 1160, expansion_rate 0.34
```

---

# 4. UPDATE Operations

## 4.1 SQL UPDATE - Simple Demo Update

```sql
UPDATE "mcp2ohio"."test_writes"."demo"
SET "amount" = 185000000.75
WHERE "id" = 910001;
```

## 4.2 SQL UPDATE - Multi-Column Demo Update

```sql
UPDATE "mcp2ohio"."test_writes"."demo"
SET
  "amount" = 220000000.50,
  "name" = 'enterprise_cloud_revenue_220m'
WHERE "id" = 910003;
```

## 4.3 SQL UPDATE - Scoped Bulk Demo Update

```sql
UPDATE "mcp2ohio"."test_writes"."demo"
SET "amount" = "amount" * 1.25
WHERE "id" IN (910002, 910004)
  AND "amount" > 100000000;
```

## 4.4 SQL UPDATE - Regional Sales KPI

```sql
UPDATE "mcp2ohio"."test_writes"."sales_by_region"
SET
  "revenue" = 168000000.00,
  "profit" = 62500000.00,
  "units_sold" = 188000
WHERE "region" = 'executive_east'
  AND "quarter" = 'Q1-2028';
```

## 4.5 SQL UPDATE - Monthly Sales KPI

```sql
UPDATE "mcp2ohio"."test_writes"."monthly_sales"
SET
  "revenue" = 275000000.00,
  "gross_profit" = 168000000.00,
  "pipeline_value" = 340000000.00
WHERE "period_month" = '2027-03';
```

## 4.6 Natural Language UPDATE - Demo Row

```text
in catalog mcp2ohio, schema test_writes, table demo, update the row where id = 910002 and set amount to 195000000 and set name to nl_updated_us_east_sales_195m
```

## 4.7 Natural Language UPDATE - Product Sales

```text
change revenue to 205000000 in catalog mcp2ohio, schema test_writes, table product_sales where product_name = 'executive_ai_platform'
```

## 4.8 Natural Language UPDATE - Regional Sales

```text
in catalog mcp2ohio, schema test_writes, table sales_by_region, update the row where region = 'executive_east' and quarter = 'Q1-2028' and set revenue to 198000000 and set profit to 82000000
```

## 4.9 Natural Language UPDATE - Customer Sales

```text
in catalog mcp2ohio, schema test_writes, table customer_sales, update the row where customer_segment = 'enterprise_strategic' and region = 'north_america' and set revenue to 188000000 and set ltv to 950000 and set expansion_rate to 0.42
```

## 4.10 Natural Language UPDATE - Monthly Sales

```text
change revenue to 315000000 in catalog mcp2ohio, schema test_writes, table monthly_sales where period_month = '2027-03'
```

---

# 5. DELETE Operations

Important: DELETE operations are destructive. The UI now requires confirmation for filtered deletes and blocks unfiltered deletes.

## 5.1 SQL DELETE - Filtered Single Row

```sql
DELETE FROM "mcp2ohio"."test_writes"."demo"
WHERE "id" = 901;
```

## 5.2 SQL DELETE - Disposable Test Row

```sql
DELETE FROM "mcp2ohio"."test_writes"."demo"
WHERE "id" = 930907;
```

## 5.3 SQL DELETE - Filtered Conditional Delete

```sql
DELETE FROM "mcp2ohio"."test_writes"."demo"
WHERE "name" = 'delete_nl_conditional_test'
  AND "amount" < 1000;
```

## 5.4 Natural Language DELETE - Fully Qualified SQL-Like Prompt

```text
delete from mcp2ohio.test_writes.demo where id = 930904
```

## 5.5 Natural Language DELETE - Fully Qualified Filtered Prompt

```text
delete from mcp2ohio.test_writes.demo where id = 930907
```

---

# 6. Guardrail Checks That Should Be Blocked

These are intentionally listed as blocked safety checks, not demo prompts to execute.

## 6.1 Blocked DELETE Without WHERE

```sql
DELETE FROM "mcp2ohio"."test_writes"."demo";
```

Expected result:

```text
DELETE requires a WHERE clause. Full-table delete is blocked by policy even when confirmation is supplied.
```

## 6.2 Blocked Natural Language DELETE Without Fully Qualified Target

```text
delete from demo where id = 930901
```

Expected result:

```text
DELETE requires fully qualified catalog.schema.table.
```

## 6.3 Blocked Vague Business INSERT

```text
insert a sales record with revenue 4.5 million
```

Expected result:

```text
Rejected or failed because write operations require explicit catalog, schema, table, and column/value mapping.
```

## 6.4 Blocked Vague Business UPDATE

```text
update enterprise revenue to 25 million
```

Expected result:

```text
Rejected or failed because UPDATE requires explicit catalog, schema, table, SET mapping, and WHERE clause.
```
