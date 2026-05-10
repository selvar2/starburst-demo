# Working CRUD Operation Prompts

Timestamp: 2026-05-11 01:21:18 IST

Scope: working prompts for the current Starburst demo app using approved test data sources:

- Catalog: `mcp2ohio`
- Schema: `test_writes`
- Main demo tables: `demo`, `sales_by_region`, `monthly_sales`, `product_sales`, `customer_sales`

Notes:

- These prompts are intentionally grounded in tables and columns that exist in the current environment.
- Destructive SQL prompts use filtered conditions only.
- Delete prompts should trigger the app confirmation flow before execution.
- For repeated demos, adjust test IDs such as `950001` / `950002` if those rows already exist.

---

## 1. SELECT Operations

### 1.1 SQL: Show Schemas

```sql
SHOW SCHEMAS FROM "mcp2ohio";
```

### 1.2 SQL: Show Tables

```sql
SHOW TABLES FROM "mcp2ohio"."test_writes";
```

### 1.3 SQL: Describe Demo Table

```sql
DESCRIBE "mcp2ohio"."test_writes"."demo";
```

### 1.4 SQL: Select Demo Data

```sql
SELECT "id", "name", "amount"
FROM "mcp2ohio"."test_writes"."demo"
ORDER BY "amount" DESC
LIMIT 20;
```

### 1.5 SQL: Regional Revenue

```sql
SELECT "region", "revenue", "profit", "units_sold"
FROM "mcp2ohio"."test_writes"."sales_by_region"
ORDER BY "revenue" DESC
LIMIT 10;
```

### 1.6 SQL: Monthly Sales Trend

```sql
SELECT "period_month", "revenue", "gross_profit", "pipeline_value"
FROM "mcp2ohio"."test_writes"."monthly_sales"
ORDER BY "period_month"
LIMIT 100;
```

### 1.7 Natural Language: Show Tables

```text
Show all tables
```

### 1.8 Natural Language: Describe Demo Table

```text
Describe demo table
```

### 1.9 Natural Language: Show Demo Data

```text
Show all data from demo
```

### 1.10 Natural Language: Count Demo Rows

```text
Count rows in demo
```

---

## 2. CREATE Operations

### 2.1 SQL: Create Scratch Schema

```sql
CREATE SCHEMA IF NOT EXISTS "mcp2ohio"."scratch_sch";
```

### 2.2 SQL: Create Scratch Table

```sql
CREATE TABLE IF NOT EXISTS "mcp2ohio"."test_writes"."scratch_table" (
    "id" INTEGER,
    "label" VARCHAR
);
```

### 2.3 SQL: Create KPI Demo Table

```sql
CREATE TABLE IF NOT EXISTS "mcp2ohio"."test_writes"."executive_kpis_demo" (
    "kpi_name" VARCHAR,
    "current_value" DOUBLE,
    "target_value" DOUBLE,
    "trend_direction" VARCHAR
);
```

### 2.4 Natural Language: Create Scratch Schema

```text
create a scratch schema
```

### 2.5 Natural Language: Create Sandbox Schema

```text
create a sandbox schema for testing
```

### 2.6 Natural Language: Create Customer Metrics Table

```text
create a customer metrics table with id and revenue
```

### 2.7 Natural Language: Create Dashboard Metrics Table

```text
create a dashboard metrics table
```

### 2.8 Natural Language: Create Executive KPI Table

```text
create an executive KPI table
```

---

## 3. INSERT Operations

### 3.1 SQL: Insert High-Value Demo Row

```sql
INSERT INTO "mcp2ohio"."test_writes"."demo" ("id", "name", "amount")
VALUES (950001, 'leadership_revenue_250m', 250000000.00);
```

### 3.2 SQL: Insert Multiple Executive Demo Rows

```sql
INSERT INTO "mcp2ohio"."test_writes"."demo" ("id", "name", "amount")
VALUES
    (950002, 'north_america_growth_180m', 180000000.00),
    (950003, 'enterprise_pipeline_320m', 320000000.00),
    (950004, 'global_profit_145m', 145000000.00);
```

### 3.3 SQL: Insert Regional Sales Row

```sql
INSERT INTO "mcp2ohio"."test_writes"."sales_by_region" ("region", "quarter", "revenue", "units_sold", "profit")
VALUES ('executive_east', 'Q1-2028', 132000000.00, 156000, 48200000.00);
```

### 3.4 SQL: Insert Monthly Sales Trend Row

```sql
INSERT INTO "mcp2ohio"."test_writes"."monthly_sales" (
    "period_month",
    "fiscal_year",
    "revenue",
    "gross_profit",
    "pipeline_value",
    "new_customers",
    "retained_customers"
)
VALUES ('2027-03', 2027, 245000000.00, 151000000.00, 312000000.00, 5100, 20600);
```

### 3.5 Natural Language: Insert Demo Row

```text
add a new row into catalog mcp2ohio, schema test_writes, table demo with id 960001, name nl_enterprise_revenue_125m, amount 125000000
```

### 3.6 Natural Language: Insert Monthly Sales Row

```text
add a new row into catalog mcp2ohio, schema test_writes, table monthly_sales with period_month 2027-04, fiscal_year 2027, revenue 265000000, gross_profit 163000000, pipeline_value 335000000, new_customers 5400, retained_customers 21400
```

### 3.7 Natural Language: Insert Regional Sales Row

```text
add a new row into catalog mcp2ohio, schema test_writes, table sales_by_region with region executive_west, quarter Q2-2028, revenue 158000000, units_sold 171000, profit 61000000
```

### 3.8 Natural Language: Insert Product Sales Row

```text
add a new row into catalog mcp2ohio, schema test_writes, table product_sales with product_name executive_ai_platform, product_segment enterprise_ai, revenue 175000000, units_sold 28400, average_deal_size 6161.97, gross_margin 0.72, win_rate 0.81
```

### 3.9 Natural Language: Insert Customer Sales Row

```text
add a new row into catalog mcp2ohio, schema test_writes, table customer_sales with customer_segment enterprise_strategic, region north_america, revenue 145000000, ltv 880000, average_order_value 125000, customer_count 1160, expansion_rate 0.34
```

---

## 4. UPDATE Operations

### 4.1 SQL: Update Single Demo Row

```sql
UPDATE "mcp2ohio"."test_writes"."demo"
SET "amount" = 185000000.75
WHERE "id" = 950001;
```

### 4.2 SQL: Update Demo Name And Amount

```sql
UPDATE "mcp2ohio"."test_writes"."demo"
SET
    "amount" = 220000000.50,
    "name" = 'enterprise_cloud_revenue_220m'
WHERE "id" = 950003;
```

### 4.3 SQL: Scoped Bulk Update

```sql
UPDATE "mcp2ohio"."test_writes"."demo"
SET "amount" = "amount" * 1.25
WHERE "id" IN (950002, 950004)
AND "amount" > 100000000;
```

### 4.4 SQL: Update Regional Sales KPI Row

```sql
UPDATE "mcp2ohio"."test_writes"."sales_by_region"
SET
    "revenue" = 168000000.00,
    "profit" = 62500000.00,
    "units_sold" = 188000
WHERE "region" = 'executive_east'
AND "quarter" = 'Q1-2028';
```

### 4.5 Natural Language: Update Demo Row

```text
in catalog mcp2ohio, schema test_writes, table demo, update the row where id = 960001 and set amount to 195000000 and set name to nl_updated_us_east_sales_195m
```

### 4.6 Natural Language: Update Product Sales Row

```text
change revenue to 205000000 in catalog mcp2ohio, schema test_writes, table product_sales where product_name = 'executive_ai_platform'
```

### 4.7 Natural Language: Update Regional Sales Row

```text
in catalog mcp2ohio, schema test_writes, table sales_by_region, update the row where region = 'executive_east' and quarter = 'Q1-2028' and set revenue to 198000000 and set profit to 82000000
```

### 4.8 Natural Language: Update Customer Sales Row

```text
in catalog mcp2ohio, schema test_writes, table customer_sales, update the row where customer_segment = 'enterprise_strategic' and region = 'north_america' and set revenue to 188000000 and set ltv to 950000 and set expansion_rate to 0.42
```

### 4.9 Natural Language: Update Monthly Sales Row

```text
change revenue to 315000000 in catalog mcp2ohio, schema test_writes, table monthly_sales where period_month = '2027-03'
```

---

## 5. DELETE Operations

### 5.1 SQL: Setup Row For SQL Delete Test

```sql
INSERT INTO "mcp2ohio"."test_writes"."demo" ("id", "name", "amount")
VALUES (970001, 'delete_sql_test_row', 12345.67);
```

### 5.2 SQL: Safe Filtered Delete

```sql
DELETE FROM "mcp2ohio"."test_writes"."demo"
WHERE "id" = 970001;
```

### 5.3 SQL: Setup Row For Natural Language Delete Test

```sql
INSERT INTO "mcp2ohio"."test_writes"."demo" ("id", "name", "amount")
VALUES (970002, 'delete_nl_test_row', 23456.78);
```

### 5.4 Natural Language: Safe Fully Qualified Delete

```text
delete from mcp2ohio.test_writes.demo where id = 970002
```

### 5.5 Natural Language: Confirmation Text

If the UI asks for confirmation, use the confirmation action in the app. For API-style test flows, the confirmed context should be equivalent to:

```text
confirm=true
```

---

## 6. Leadership Demo Flow

### 6.1 Prepare High-Value Rows

```sql
INSERT INTO "mcp2ohio"."test_writes"."demo" ("id", "name", "amount")
VALUES
    (980001, 'executive_arr_410m', 410000000.00),
    (980002, 'strategic_pipeline_360m', 360000000.00),
    (980003, 'global_margin_pool_190m', 190000000.00);
```

### 6.2 Show Executive Demo Data

```sql
SELECT "name", "amount"
FROM "mcp2ohio"."test_writes"."demo"
WHERE "id" IN (980001, 980002, 980003)
ORDER BY "amount" DESC;
```

### 6.3 Natural Language: Show Demo Data

```text
Show all data from demo
```

### 6.4 Natural Language: Count Demo Rows

```text
Count rows in demo
```
