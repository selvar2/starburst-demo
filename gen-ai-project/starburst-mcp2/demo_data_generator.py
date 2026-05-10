"""Create executive-grade demo datasets in Starburst for BI demos.

The generator is deterministic. It creates visually rich distributions for
bar, line, pie, and KPI cards without relying on external data.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from typing import Iterable

from starburst_client_jwt import StarburstClientJWT as StarburstClient


CATALOG = "mcp2ohio"
SCHEMA = "test_writes"


@dataclass(frozen=True)
class TableSpec:
    name: str
    columns: list[tuple[str, str]]
    rows: list[dict]


REGIONS = [
    ("US-East", 1.28),
    ("US-West", 1.11),
    ("Central", 0.92),
    ("EMEA", 1.18),
    ("APAC", 1.36),
    ("LATAM", 0.74),
]
SEGMENTS = [
    ("Enterprise", 1.55),
    ("Mid-Market", 1.12),
    ("Commercial", 0.86),
    ("SMB", 0.62),
]
PRODUCTS = [
    ("Atlas AI Suite", "AI Platform", 1.74, 0.71),
    ("Nova BI Copilot", "Analytics", 1.42, 0.66),
    ("Apex Data Fabric", "Data Platform", 1.28, 0.63),
    ("Pulse Customer 360", "Customer Intelligence", 1.08, 0.58),
    ("Shield Governance", "Security", 0.95, 0.69),
    ("FlowOps Automation", "Operations", 0.81, 0.55),
    ("Edge Revenue Optimizer", "Revenue", 1.21, 0.61),
    ("Quantum Forecasting", "Planning", 1.63, 0.68),
]
CHANNELS = [("Direct", 1.35), ("Partner", 0.96), ("Marketplace", 0.78)]
MONTHS = [f"{year}-{month:02d}" for year in (2025, 2026) for month in range(1, 13)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default=CATALOG)
    parser.add_argument("--schema", default=SCHEMA)
    parser.add_argument("--reset", action="store_true", help="Drop and recreate demo tables.")
    args = parser.parse_args()

    client = StarburstClient()
    specs = build_specs(args.catalog, args.schema)
    print(f"Creating {len(specs)} executive demo tables in {args.catalog}.{args.schema}")
    for spec in specs:
        load_table(client, args.catalog, args.schema, spec, reset=args.reset)
    validate_visual_quality(client, args.catalog, args.schema, specs)
    print("Executive demo data generation complete.")


def build_specs(catalog: str, schema: str) -> list[TableSpec]:
    return [
        sales_fact(),
        regional_sales(),
        product_sales(),
        monthly_sales(),
        customer_sales(),
        customer_engagement(),
        customer_retention(),
        churn_metrics(),
        customer_segments(),
        inventory_metrics(),
        product_performance(),
        pricing_metrics(),
        review_analytics(),
        profit_loss(),
        expense_breakdown(),
        revenue_forecast(),
        quarterly_growth(),
        executive_summary(),
        kpi_metrics(),
        operational_metrics(),
    ]


def load_table(client: StarburstClient, catalog: str, schema: str, spec: TableSpec, reset: bool) -> None:
    fqn = f"{catalog}.{schema}.{spec.name}"
    if reset:
        print(f"DROP TABLE IF EXISTS {fqn}")
        client.execute(f"DROP TABLE IF EXISTS {fqn}")
    col_defs = ", ".join(f"{name} {typ}" for name, typ in spec.columns)
    print(f"CREATE TABLE IF NOT EXISTS {fqn}")
    client.execute(f"CREATE TABLE IF NOT EXISTS {fqn} ({col_defs})")
    if reset and spec.rows:
        insert_rows(client, fqn, [name for name, _typ in spec.columns], spec.rows)
    print(f"  loaded rows={len(spec.rows)}")


def insert_rows(client: StarburstClient, fqn: str, columns: list[str], rows: list[dict], chunk_size: int = 80) -> None:
    for start in range(0, len(rows), chunk_size):
        chunk = rows[start:start + chunk_size]
        values = []
        for row in chunk:
            values.append("(" + ", ".join(sql_literal(row.get(col)) for col in columns) + ")")
        sql = f"INSERT INTO {fqn} ({', '.join(columns)}) VALUES " + ", ".join(values)
        client.execute(sql)


def validate_visual_quality(client: StarburstClient, catalog: str, schema: str, specs: list[TableSpec]) -> None:
    print("Validation summary:")
    for spec in specs:
        numeric_cols = [name for name, typ in spec.columns if typ in {"INTEGER", "DOUBLE"}]
        if not numeric_cols:
            continue
        col = choose_metric_column(numeric_cols)
        fqn = f"{catalog}.{schema}.{spec.name}"
        result = client.execute(f"SELECT COUNT(*) AS rows, MIN({col}) AS min_value, MAX({col}) AS max_value, AVG({col}) AS avg_value FROM {fqn}")
        row = result["rows"][0]
        min_value = float(row[1] or 0)
        max_value = float(row[2] or 0)
        spread = round(max_value / min_value, 2) if min_value else 0
        print(f"  {spec.name}: rows={row[0]}, metric={col}, min={round(min_value, 2)}, max={round(max_value, 2)}, spread={spread}x")


def choose_metric_column(columns: list[str]) -> str:
    priority = [
        "revenue", "actual_value", "forecast_revenue", "gross_profit", "operating_profit",
        "ltv", "retention_rate", "engagement_score", "expense_amount", "inventory_value",
        "reviews", "stock_units",
    ]
    for name in priority:
        if name in columns:
            return name
    return columns[0]


def sales_fact() -> TableSpec:
    cols = [
        ("period_month", "VARCHAR"), ("fiscal_year", "INTEGER"), ("fiscal_quarter", "VARCHAR"),
        ("region", "VARCHAR"), ("product_segment", "VARCHAR"), ("product_name", "VARCHAR"),
        ("channel", "VARCHAR"), ("revenue", "DOUBLE"), ("units_sold", "INTEGER"),
        ("gross_margin", "DOUBLE"), ("discount_rate", "DOUBLE"), ("customer_count", "INTEGER"),
    ]
    rows = []
    for mi, month in enumerate(MONTHS):
        year = int(month[:4])
        q = f"Q{((int(month[-2:]) - 1) // 3) + 1}"
        trend = 1 + (mi * 0.028)
        season = 1 + 0.18 * math.sin((mi + 2) / 12 * math.pi * 2)
        for region, region_mult in REGIONS:
            for product, segment, product_mult, margin in PRODUCTS:
                if (mi + len(region) + len(product)) % 3 == 0:
                    continue
                channel, channel_mult = CHANNELS[(mi + len(product)) % len(CHANNELS)]
                revenue = 185000 * trend * season * region_mult * product_mult * channel_mult
                if region == "APAC" and q == "Q4":
                    revenue *= 1.34
                if product == "Quantum Forecasting" and year == 2026:
                    revenue *= 1.22
                rows.append({
                    "period_month": month,
                    "fiscal_year": year,
                    "fiscal_quarter": q,
                    "region": region,
                    "product_segment": segment,
                    "product_name": product,
                    "channel": channel,
                    "revenue": round(revenue, 2),
                    "units_sold": int(revenue / (920 + (len(product) * 14))),
                    "gross_margin": round(margin + (0.015 if year == 2026 else 0), 3),
                    "discount_rate": round(0.05 + ((mi + len(region)) % 8) * 0.008, 3),
                    "customer_count": int(revenue / 18500),
                })
    return TableSpec("sales_fact", cols, rows)


def regional_sales() -> TableSpec:
    cols = [
        ("region", "VARCHAR"), ("fiscal_year", "INTEGER"), ("revenue", "DOUBLE"),
        ("gross_profit", "DOUBLE"), ("growth_rate", "DOUBLE"), ("target_attainment", "DOUBLE"),
        ("strategic_accounts", "INTEGER"),
    ]
    rows = []
    for year in (2025, 2026):
        for idx, (region, mult) in enumerate(REGIONS):
            revenue = 8200000 * mult * (1.18 if year == 2026 else 1.0) * (1 + idx * 0.045)
            rows.append({
                "region": region, "fiscal_year": year, "revenue": round(revenue, 2),
                "gross_profit": round(revenue * (0.54 + idx * 0.025), 2),
                "growth_rate": round(0.09 + idx * 0.027 + (0.04 if year == 2026 else 0), 3),
                "target_attainment": round(0.88 + idx * 0.052 + (0.06 if year == 2026 else 0), 3),
                "strategic_accounts": 42 + idx * 17 + (9 if year == 2026 else 0),
            })
    return TableSpec("regional_sales", cols, rows)


def product_sales() -> TableSpec:
    cols = [
        ("product_name", "VARCHAR"), ("product_segment", "VARCHAR"), ("revenue", "DOUBLE"),
        ("units_sold", "INTEGER"), ("average_deal_size", "DOUBLE"), ("gross_margin", "DOUBLE"),
        ("win_rate", "DOUBLE"),
    ]
    rows = []
    for idx, (product, segment, mult, margin) in enumerate(PRODUCTS):
        revenue = 5200000 * mult * (1 + idx * 0.08)
        rows.append({
            "product_name": product, "product_segment": segment, "revenue": round(revenue, 2),
            "units_sold": int(1800 * mult * (1 + idx * 0.05)),
            "average_deal_size": round(revenue / max(300, 620 * mult), 2),
            "gross_margin": margin,
            "win_rate": round(0.31 + idx * 0.035, 3),
        })
    return TableSpec("product_sales", cols, rows)


def monthly_sales() -> TableSpec:
    cols = [
        ("period_month", "VARCHAR"), ("fiscal_year", "INTEGER"), ("revenue", "DOUBLE"),
        ("gross_profit", "DOUBLE"), ("pipeline_value", "DOUBLE"), ("new_customers", "INTEGER"),
        ("retained_customers", "INTEGER"),
    ]
    rows = []
    for mi, month in enumerate(MONTHS):
        year = int(month[:4])
        trend = 1 + mi * 0.035
        season = 1 + 0.22 * math.sin((mi + 1) / 12 * math.pi * 2)
        revenue = 4200000 * trend * season
        if month.endswith("11") or month.endswith("12"):
            revenue *= 1.18
        rows.append({
            "period_month": month, "fiscal_year": year, "revenue": round(revenue, 2),
            "gross_profit": round(revenue * (0.59 + (mi % 5) * 0.012), 2),
            "pipeline_value": round(revenue * (1.55 + (mi % 4) * 0.08), 2),
            "new_customers": 180 + mi * 9 + (45 if month.endswith("12") else 0),
            "retained_customers": 1540 + mi * 31,
        })
    return TableSpec("monthly_sales", cols, rows)


def customer_sales() -> TableSpec:
    cols = [
        ("customer_segment", "VARCHAR"), ("region", "VARCHAR"), ("revenue", "DOUBLE"),
        ("ltv", "DOUBLE"), ("average_order_value", "DOUBLE"), ("customer_count", "INTEGER"),
        ("expansion_rate", "DOUBLE"),
    ]
    rows = []
    for segment, seg_mult in SEGMENTS:
        for idx, (region, region_mult) in enumerate(REGIONS):
            revenue = 1350000 * seg_mult * region_mult * (1 + idx * 0.06)
            rows.append({
                "customer_segment": segment, "region": region, "revenue": round(revenue, 2),
                "ltv": round(42000 * seg_mult * (1 + idx * 0.05), 2),
                "average_order_value": round(8800 * seg_mult * region_mult, 2),
                "customer_count": int(revenue / (22000 * seg_mult)),
                "expansion_rate": round(0.08 + seg_mult * 0.035 + idx * 0.01, 3),
            })
    return TableSpec("customer_sales", cols, rows)


def customer_engagement() -> TableSpec:
    cols = [
        ("period_month", "VARCHAR"), ("customer_segment", "VARCHAR"), ("engagement_score", "DOUBLE"),
        ("active_users", "INTEGER"), ("sessions", "INTEGER"), ("feature_adoption", "DOUBLE"),
        ("satisfaction_score", "DOUBLE"),
    ]
    rows = []
    for mi, month in enumerate(MONTHS):
        for segment, mult in SEGMENTS:
            base = 61 + mi * 0.72 + mult * 12
            rows.append({
                "period_month": month, "customer_segment": segment,
                "engagement_score": round(min(96, base + 5 * math.sin(mi / 3)), 2),
                "active_users": int(18000 * mult * (1 + mi * 0.025)),
                "sessions": int(94000 * mult * (1 + mi * 0.031)),
                "feature_adoption": round(min(0.94, 0.42 + mi * 0.012 + mult * 0.08), 3),
                "satisfaction_score": round(min(4.9, 3.7 + mult * 0.42 + mi * 0.012), 2),
            })
    return TableSpec("customer_engagement", cols, rows)


def customer_retention() -> TableSpec:
    cols = [
        ("customer_segment", "VARCHAR"), ("fiscal_quarter", "VARCHAR"), ("retention_rate", "DOUBLE"),
        ("renewal_revenue", "DOUBLE"), ("expansion_revenue", "DOUBLE"), ("at_risk_accounts", "INTEGER"),
    ]
    rows = []
    for qi, q in enumerate(["2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2", "2026-Q3", "2026-Q4"]):
        for segment, mult in SEGMENTS:
            rows.append({
                "customer_segment": segment, "fiscal_quarter": q,
                "retention_rate": round(min(0.97, 0.78 + qi * 0.018 + mult * 0.075), 3),
                "renewal_revenue": round(2100000 * mult * (1 + qi * 0.055), 2),
                "expansion_revenue": round(620000 * mult * (1 + qi * 0.082), 2),
                "at_risk_accounts": max(5, int(82 - qi * 5 - mult * 19)),
            })
    return TableSpec("customer_retention", cols, rows)


def churn_metrics() -> TableSpec:
    cols = [
        ("period_month", "VARCHAR"), ("region", "VARCHAR"), ("churn_rate", "DOUBLE"),
        ("churned_revenue", "DOUBLE"), ("saved_revenue", "DOUBLE"), ("risk_score", "DOUBLE"),
    ]
    rows = []
    for mi, month in enumerate(MONTHS):
        for idx, (region, mult) in enumerate(REGIONS):
            churn = max(0.018, 0.082 - mi * 0.0017 + idx * 0.004)
            rows.append({
                "period_month": month, "region": region, "churn_rate": round(churn, 3),
                "churned_revenue": round(480000 * churn * mult * 10, 2),
                "saved_revenue": round(610000 * (1 - churn) * (0.7 + idx * 0.08), 2),
                "risk_score": round(38 + churn * 480 + idx * 2, 2),
            })
    return TableSpec("churn_metrics", cols, rows)


def customer_segments() -> TableSpec:
    cols = [
        ("customer_segment", "VARCHAR"), ("accounts", "INTEGER"), ("revenue", "DOUBLE"),
        ("ltv", "DOUBLE"), ("churn_rate", "DOUBLE"), ("nps", "DOUBLE"),
    ]
    rows = []
    for idx, (segment, mult) in enumerate(SEGMENTS):
        rows.append({
            "customer_segment": segment, "accounts": int(840 * (2.1 - mult + idx * 0.4)),
            "revenue": round(9200000 * mult, 2), "ltv": round(52000 * mult, 2),
            "churn_rate": round(0.075 - idx * 0.011, 3), "nps": round(42 + mult * 20, 1),
        })
    return TableSpec("customer_segments", cols, rows)


def inventory_metrics() -> TableSpec:
    cols = [
        ("product_name", "VARCHAR"), ("stock_units", "INTEGER"), ("inventory_value", "DOUBLE"),
        ("sell_through_rate", "DOUBLE"), ("days_on_hand", "INTEGER"), ("stockout_risk", "DOUBLE"),
    ]
    rows = []
    for idx, (product, _segment, mult, _margin) in enumerate(PRODUCTS):
        stock = int(6400 * (1.9 - mult + idx * 0.17))
        rows.append({
            "product_name": product, "stock_units": stock,
            "inventory_value": round(stock * (840 + mult * 1120), 2),
            "sell_through_rate": round(0.38 + mult * 0.22, 3),
            "days_on_hand": max(14, int(95 - mult * 25 + idx * 4)),
            "stockout_risk": round(max(0.06, 0.34 - stock / 50000), 3),
        })
    return TableSpec("inventory_metrics", cols, rows)


def product_performance() -> TableSpec:
    cols = [
        ("product_name", "VARCHAR"), ("revenue", "DOUBLE"), ("gross_margin", "DOUBLE"),
        ("market_share", "DOUBLE"), ("growth_rate", "DOUBLE"), ("quality_score", "DOUBLE"),
    ]
    rows = []
    for idx, (product, _segment, mult, margin) in enumerate(PRODUCTS):
        rows.append({
            "product_name": product, "revenue": round(7800000 * mult * (1 + idx * 0.045), 2),
            "gross_margin": margin, "market_share": round(0.08 + mult * 0.045 + idx * 0.008, 3),
            "growth_rate": round(0.11 + mult * 0.065 + idx * 0.015, 3),
            "quality_score": round(78 + margin * 22 + idx * 0.7, 2),
        })
    return TableSpec("product_performance", cols, rows)


def pricing_metrics() -> TableSpec:
    cols = [
        ("product_name", "VARCHAR"), ("list_price", "DOUBLE"), ("net_price", "DOUBLE"),
        ("discount_rate", "DOUBLE"), ("price_elasticity", "DOUBLE"), ("gross_margin", "DOUBLE"),
    ]
    rows = []
    for idx, (product, _segment, mult, margin) in enumerate(PRODUCTS):
        list_price = 48000 * mult * (1 + idx * 0.05)
        discount = 0.06 + (idx % 4) * 0.025
        rows.append({
            "product_name": product, "list_price": round(list_price, 2),
            "net_price": round(list_price * (1 - discount), 2),
            "discount_rate": round(discount, 3),
            "price_elasticity": round(-0.7 - idx * 0.08, 2),
            "gross_margin": margin,
        })
    return TableSpec("pricing_metrics", cols, rows)


def review_analytics() -> TableSpec:
    cols = [
        ("product_name", "VARCHAR"), ("reviews", "INTEGER"), ("rating", "DOUBLE"),
        ("positive_sentiment", "DOUBLE"), ("support_cases", "INTEGER"), ("nps", "DOUBLE"),
    ]
    rows = []
    for idx, (product, _segment, mult, _margin) in enumerate(PRODUCTS):
        rows.append({
            "product_name": product, "reviews": int(18500 * mult * (1 + idx * 0.12)),
            "rating": round(min(4.9, 3.8 + mult * 0.42 - idx * 0.015), 2),
            "positive_sentiment": round(min(0.95, 0.68 + mult * 0.12), 3),
            "support_cases": int(420 * (2.2 - mult + idx * 0.12)),
            "nps": round(34 + mult * 24 - idx * 0.8, 1),
        })
    return TableSpec("review_analytics", cols, rows)


def profit_loss() -> TableSpec:
    cols = [
        ("fiscal_quarter", "VARCHAR"), ("revenue", "DOUBLE"), ("cost_of_goods", "DOUBLE"),
        ("gross_profit", "DOUBLE"), ("operating_expense", "DOUBLE"), ("operating_profit", "DOUBLE"),
        ("net_margin", "DOUBLE"),
    ]
    rows = []
    for qi, q in enumerate(["2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2", "2026-Q3", "2026-Q4"]):
        revenue = 14500000 * (1 + qi * 0.082) * (1.14 if q.endswith("Q4") else 1)
        cogs = revenue * (0.39 - qi * 0.006)
        gross = revenue - cogs
        opex = revenue * (0.29 - qi * 0.004)
        rows.append({
            "fiscal_quarter": q, "revenue": round(revenue, 2),
            "cost_of_goods": round(cogs, 2), "gross_profit": round(gross, 2),
            "operating_expense": round(opex, 2), "operating_profit": round(gross - opex, 2),
            "net_margin": round((gross - opex) / revenue, 3),
        })
    return TableSpec("profit_loss", cols, rows)


def expense_breakdown() -> TableSpec:
    cols = [
        ("expense_category", "VARCHAR"), ("expense_amount", "DOUBLE"), ("budget_amount", "DOUBLE"),
        ("variance_amount", "DOUBLE"), ("expense_share", "DOUBLE"),
    ]
    categories = [
        ("Cloud Infrastructure", 4200000, 3900000), ("Sales & Marketing", 6100000, 6500000),
        ("Research & Development", 7200000, 6900000), ("Customer Success", 2800000, 2600000),
        ("Security & Compliance", 1900000, 1750000), ("General Operations", 1500000, 1600000),
    ]
    total = sum(v for _c, v, _b in categories)
    rows = [{
        "expense_category": c, "expense_amount": v, "budget_amount": b,
        "variance_amount": v - b, "expense_share": round(v / total, 3),
    } for c, v, b in categories]
    return TableSpec("expense_breakdown", cols, rows)


def revenue_forecast() -> TableSpec:
    cols = [
        ("period_month", "VARCHAR"), ("actual_revenue", "DOUBLE"), ("forecast_revenue", "DOUBLE"),
        ("forecast_confidence", "DOUBLE"), ("pipeline_coverage", "DOUBLE"),
    ]
    rows = []
    for mi, month in enumerate(MONTHS):
        actual = 4300000 * (1 + mi * 0.032) * (1 + 0.16 * math.sin((mi + 1) / 12 * math.pi * 2))
        forecast = actual * (1.02 + ((mi % 5) - 2) * 0.012)
        rows.append({
            "period_month": month, "actual_revenue": round(actual, 2),
            "forecast_revenue": round(forecast, 2),
            "forecast_confidence": round(0.76 + min(0.18, mi * 0.006), 3),
            "pipeline_coverage": round(2.4 + (mi % 6) * 0.12, 2),
        })
    return TableSpec("revenue_forecast", cols, rows)


def quarterly_growth() -> TableSpec:
    cols = [
        ("fiscal_quarter", "VARCHAR"), ("revenue", "DOUBLE"), ("yoy_growth", "DOUBLE"),
        ("qoq_growth", "DOUBLE"), ("gross_margin", "DOUBLE"), ("customer_growth", "DOUBLE"),
    ]
    rows = []
    quarters = ["2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2", "2026-Q3", "2026-Q4"]
    for qi, q in enumerate(quarters):
        rows.append({
            "fiscal_quarter": q, "revenue": round(13200000 * (1 + qi * 0.09), 2),
            "yoy_growth": round(0.12 + qi * 0.018, 3),
            "qoq_growth": round(0.045 + (qi % 4) * 0.018, 3),
            "gross_margin": round(0.57 + qi * 0.009, 3),
            "customer_growth": round(0.08 + qi * 0.012, 3),
        })
    return TableSpec("quarterly_growth", cols, rows)


def executive_summary() -> TableSpec:
    cols = [
        ("kpi_name", "VARCHAR"), ("actual_value", "DOUBLE"), ("target_value", "DOUBLE"),
        ("benchmark_value", "DOUBLE"), ("trend_direction", "VARCHAR"), ("executive_note", "VARCHAR"),
    ]
    rows = [
        {"kpi_name": "Annual Recurring Revenue", "actual_value": 184500000, "target_value": 172000000, "benchmark_value": 160000000, "trend_direction": "up", "executive_note": "ARR is ahead of plan with strong enterprise expansion."},
        {"kpi_name": "Gross Margin", "actual_value": 0.642, "target_value": 0.61, "benchmark_value": 0.58, "trend_direction": "up", "executive_note": "Margin expansion reflects improved platform economics."},
        {"kpi_name": "Net Revenue Retention", "actual_value": 1.31, "target_value": 1.22, "benchmark_value": 1.16, "trend_direction": "up", "executive_note": "Expansion revenue is outpacing contraction."},
        {"kpi_name": "Logo Churn", "actual_value": 0.034, "target_value": 0.045, "benchmark_value": 0.052, "trend_direction": "down", "executive_note": "Churn is below target and improving."},
        {"kpi_name": "Pipeline Coverage", "actual_value": 3.18, "target_value": 2.75, "benchmark_value": 2.4, "trend_direction": "up", "executive_note": "Pipeline coverage supports next-quarter growth."},
    ]
    return TableSpec("executive_summary", cols, rows)


def kpi_metrics() -> TableSpec:
    cols = [
        ("kpi_name", "VARCHAR"), ("business_unit", "VARCHAR"), ("actual_value", "DOUBLE"),
        ("target_value", "DOUBLE"), ("previous_value", "DOUBLE"), ("variance_to_target", "DOUBLE"),
        ("trend_percent", "DOUBLE"),
    ]
    source = [
        ("Revenue", "Global Sales", 184500000, 172000000, 156200000),
        ("Gross Profit", "Finance", 118450000, 104920000, 96700000),
        ("Customer LTV", "Customer Success", 68400, 62000, 59100),
        ("Forecast Accuracy", "Planning", 0.91, 0.86, 0.82),
        ("Operational SLA", "Operations", 0.982, 0.975, 0.963),
        ("NPS", "Customer Success", 67, 61, 58),
    ]
    rows = []
    for name, unit, actual, target, previous in source:
        rows.append({
            "kpi_name": name, "business_unit": unit, "actual_value": actual,
            "target_value": target, "previous_value": previous,
            "variance_to_target": round(actual - target, 3),
            "trend_percent": round((actual - previous) / previous, 3),
        })
    return TableSpec("kpi_metrics", cols, rows)


def operational_metrics() -> TableSpec:
    cols = [
        ("operation_area", "VARCHAR"), ("actual_value", "DOUBLE"), ("target_value", "DOUBLE"),
        ("sla_rate", "DOUBLE"), ("incident_count", "INTEGER"), ("automation_rate", "DOUBLE"),
    ]
    rows = [
        {"operation_area": "Data Platform", "actual_value": 99.92, "target_value": 99.8, "sla_rate": 0.999, "incident_count": 3, "automation_rate": 0.81},
        {"operation_area": "AI Services", "actual_value": 98.74, "target_value": 98.5, "sla_rate": 0.987, "incident_count": 7, "automation_rate": 0.76},
        {"operation_area": "Customer Support", "actual_value": 94.6, "target_value": 92.0, "sla_rate": 0.946, "incident_count": 18, "automation_rate": 0.63},
        {"operation_area": "Security Operations", "actual_value": 99.2, "target_value": 98.8, "sla_rate": 0.992, "incident_count": 4, "automation_rate": 0.88},
        {"operation_area": "Revenue Operations", "actual_value": 96.1, "target_value": 94.0, "sla_rate": 0.961, "incident_count": 11, "automation_rate": 0.71},
    ]
    return TableSpec("operational_metrics", cols, rows)


def sql_literal(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


if __name__ == "__main__":
    main()
