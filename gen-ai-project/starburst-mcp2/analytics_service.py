"""Data-grounded executive analytics summaries and dashboard hints."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InsightResult:
    summary: str
    insights: list[str]
    dashboard: dict
    kpis: list[dict]
    trend_highlights: list[str]
    recommendations: list[str]
    chart_explanation: str


def build_result_insights(
    message: str,
    sql: str,
    columns: list[str],
    rows: list[list],
    chart: str,
) -> InsightResult:
    profile = _profile(columns, rows)
    summary = _executive_summary(message, columns, rows, profile)
    insights = _business_insights(columns, rows, profile)
    kpis = _kpi_cards(columns, rows, profile)
    trend_highlights = _trend_highlights(columns, rows, profile)
    recommendations = _recommendations(columns, rows, profile)
    chart_explanation = _chart_explanation(columns, rows, chart, profile)
    dashboard = {
        "title": _dashboard_title(message),
        "cards": [
            {
                "type": card.get("type", "metric"),
                "title": card["label"],
                "value": card["value"],
                "subtitle": card.get("subtitle", ""),
                "columns": columns[:4],
                "row_count": len(rows),
            }
            for card in kpis[:4]
        ] or [
            {
                "type": chart or "table",
                "title": _dashboard_title(message),
                "columns": columns[:4],
                "row_count": len(rows),
            }
        ],
        "chart_explanation": chart_explanation,
        "recommendations": recommendations,
    }
    return InsightResult(
        summary=summary,
        insights=insights,
        dashboard=dashboard,
        kpis=kpis,
        trend_highlights=trend_highlights,
        recommendations=recommendations,
        chart_explanation=chart_explanation,
    )


def _profile(columns: list[str], rows: list[list]) -> dict:
    numeric = []
    text = []
    for idx, col in enumerate(columns):
        values = [r[idx] for r in rows if len(r) > idx and r[idx] is not None]
        if values and all(isinstance(v, (int, float)) for v in values):
            nums = [float(v) for v in values]
            numeric.append({
                "idx": idx,
                "name": col,
                "values": nums,
                "min": min(nums),
                "max": max(nums),
                "sum": sum(nums),
                "avg": sum(nums) / len(nums),
                "spread": (max(nums) / min(nums)) if min(nums) else 0,
            })
        else:
            text.append({"idx": idx, "name": col, "values": values})
    return {"numeric": numeric, "text": text}


def _executive_summary(message: str, columns: list[str], rows: list[list], profile: dict) -> str:
    if not rows:
        return "No rows matched the current enterprise data request."
    if _is_kpi_table(columns):
        name_idx = _col_idx(columns, "kpi_name")
        actual_idx = _col_idx(columns, "actual_value")
        target_idx = _col_idx(columns, "target_value")
        lead = rows[0]
        lead_text = f"{lead[name_idx]} is {_format_value(str(lead[name_idx]), float(lead[actual_idx]))}"
        if target_idx is not None and lead[target_idx] not in (None, 0):
            variance = (float(lead[actual_idx]) - float(lead[target_idx])) / float(lead[target_idx])
            lead_text += f" versus target ({variance * 100:+.1f}%)."
        else:
            lead_text += "."
        return f"Returned {len(rows)} executive KPIs from approved enterprise data. {lead_text}"
    metric = _primary_metric(profile)
    label = _primary_label(profile)
    if metric and label:
        total = metric["sum"]
        top_idx = metric["values"].index(metric["max"])
        top_label = rows[top_idx][label["idx"]]
        return (
            f"Returned {len(rows)} rows from approved enterprise data. "
            f"Total {metric['name']} is {_format_value(metric['name'], total)}, "
            f"with {top_label} leading at {_format_value(metric['name'], metric['max'])}."
        )
    if metric:
        return (
            f"Returned {len(rows)} rows with {len(columns)} columns. "
            f"Average {metric['name']} is {_format_value(metric['name'], metric['avg'])} "
            f"and maximum is {_format_value(metric['name'], metric['max'])}."
        )
    return f"Returned {len(rows)} rows with {len(columns)} columns from approved enterprise data sources."


def _business_insights(columns: list[str], rows: list[list], profile: dict) -> list[str]:
    insights: list[str] = []
    if _is_kpi_table(columns):
        name_idx = _col_idx(columns, "kpi_name")
        actual_idx = _col_idx(columns, "actual_value")
        target_idx = _col_idx(columns, "target_value")
        for row in rows[:3]:
            if target_idx is not None and row[target_idx] not in (None, 0):
                variance = (float(row[actual_idx]) - float(row[target_idx])) / float(row[target_idx])
                insights.append(f"{row[name_idx]} is {_format_value(str(row[name_idx]), float(row[actual_idx]))}, {variance * 100:+.1f}% versus target.")
            else:
                insights.append(f"{row[name_idx]} is {_format_value(str(row[name_idx]), float(row[actual_idx]))}.")
        return insights
    metric = _primary_metric(profile)
    label = _primary_label(profile)
    if not rows:
        return ["No data was returned for analysis."]
    if metric and label:
        pairs = []
        for i, row in enumerate(rows):
            if len(row) > label["idx"] and i < len(metric["values"]):
                pairs.append((row[label["idx"]], metric["values"][i]))
        pairs.sort(key=lambda item: item[1], reverse=True)
        if pairs:
            insights.append(f"Top performer is {pairs[0][0]} with {_format_value(metric['name'], pairs[0][1])}.")
        if len(pairs) > 1:
            insights.append(f"Lowest performer is {pairs[-1][0]} with {_format_value(metric['name'], pairs[-1][1])}.")
        if metric["spread"] >= 2:
            insights.append(f"{metric['name']} has strong variance at {metric['spread']:.1f}x from low to high, which should create a clear executive chart.")
    for num in profile["numeric"][:3]:
        if any(key in num["name"].lower() for key in ("growth", "margin", "retention", "churn", "rate")):
            insights.append(f"Average {num['name']} is {_format_value(num['name'], num['avg'])}.")
    return insights[:5] or ["Review the returned table for detailed records."]


def _kpi_cards(columns: list[str], rows: list[list], profile: dict) -> list[dict]:
    if _is_kpi_table(columns):
        name_idx = _col_idx(columns, "kpi_name")
        actual_idx = _col_idx(columns, "actual_value")
        target_idx = _col_idx(columns, "target_value")
        cards = []
        for row in rows[:6]:
            subtitle = ""
            if target_idx is not None and row[target_idx] not in (None, 0):
                variance = (float(row[actual_idx]) - float(row[target_idx])) / float(row[target_idx])
                subtitle = f"{variance * 100:+.1f}% vs target"
            cards.append({
                "type": "metric",
                "label": str(row[name_idx]),
                "value": _format_value(str(row[name_idx]), float(row[actual_idx])),
                "subtitle": subtitle,
            })
        return cards
    cards = []
    for num in profile["numeric"][:5]:
        cards.append({
            "type": "metric",
            "label": _title(num["name"]),
            "value": _format_value(num["name"], num["sum"] if _is_additive(num["name"]) else num["avg"]),
            "subtitle": f"max {_format_value(num['name'], num['max'])}",
        })
    return cards


def _trend_highlights(columns: list[str], rows: list[list], profile: dict) -> list[str]:
    metric = _primary_metric(profile)
    if not metric or len(metric["values"]) < 3:
        return []
    first = metric["values"][0]
    last = metric["values"][-1]
    if first:
        change = (last - first) / first
        direction = "growth" if change >= 0 else "decline"
        return [f"{metric['name']} shows {direction} of {change * 100:.1f}% from first to last returned row."]
    return []


def _recommendations(columns: list[str], rows: list[list], profile: dict) -> list[str]:
    metric = _primary_metric(profile)
    label = _primary_label(profile)
    if not metric or not label or not rows:
        return ["Use additional dimensions or filters to expand executive analysis."]
    top_idx = metric["values"].index(metric["max"])
    low_idx = metric["values"].index(metric["min"])
    return [
        f"Protect momentum in {rows[top_idx][label['idx']]} with executive focus on capacity and retention.",
        f"Review underperformance drivers for {rows[low_idx][label['idx']]} and compare against top performer playbooks.",
    ]


def _chart_explanation(columns: list[str], rows: list[list], chart: str, profile: dict) -> str:
    if _is_kpi_table(columns):
        return "The KPI cards compare actual values against enterprise targets and benchmarks using only returned database rows."
    metric = _primary_metric(profile)
    label = _primary_label(profile)
    if not rows or not metric:
        return "The result is best reviewed as a table because no numeric measure was returned."
    if label:
        return (
            f"The {chart or 'chart'} compares {metric['name']} by {label['name']}. "
            f"The range from {_format_value(metric['name'], metric['min'])} to {_format_value(metric['name'], metric['max'])} "
            "provides enough spread for a clear executive visualization."
        )
    return f"The {chart or 'chart'} summarizes {metric['name']} across the returned rows."


def _primary_metric(profile: dict) -> dict | None:
    if not profile["numeric"]:
        return None
    priority = ("revenue", "sales", "profit", "actual", "forecast", "ltv", "retention", "growth", "margin", "reviews")
    for key in priority:
        for num in profile["numeric"]:
            if key in num["name"].lower():
                return num
    return profile["numeric"][0]


def _primary_label(profile: dict) -> dict | None:
    return profile["text"][0] if profile["text"] else None


def _is_additive(name: str) -> bool:
    return any(key in name.lower() for key in ("revenue", "sales", "profit", "expense", "value", "units", "customers", "reviews", "stock"))


def _format_value(name: str, value: float) -> str:
    lname = name.lower()
    if any(key in lname for key in ("margin", "retention", "churn", "rate", "accuracy")):
        return f"{value * 100:.1f}%" if abs(value) <= 5 else f"{value:.1f}%"
    if any(key in lname for key in ("nps", "score")):
        return f"{value:.1f}"
    if any(key in lname for key in ("revenue", "sales", "profit", "expense", "value", "ltv", "price", "amount")):
        if abs(value) >= 1_000_000:
            return f"${value / 1_000_000:.1f}M"
        if abs(value) >= 1_000:
            return f"${value / 1_000:.1f}K"
        return f"${value:,.0f}"
    if any(key in lname for key in ("rate", "margin", "churn", "retention", "growth", "share", "attainment", "accuracy")):
        return f"{value * 100:.1f}%" if abs(value) <= 5 else f"{value:.1f}%"
    return f"{value:,.0f}" if abs(value) >= 100 else f"{value:.2f}"


def _is_kpi_table(columns: list[str]) -> bool:
    lower = {c.lower() for c in columns}
    return "kpi_name" in lower and "actual_value" in lower


def _col_idx(columns: list[str], name: str) -> int | None:
    for idx, col in enumerate(columns):
        if col.lower() == name:
            return idx
    return None


def _title(name: str) -> str:
    return name.replace("_", " ").title()


def _dashboard_title(message: str) -> str:
    cleaned = " ".join(message.strip().split())
    if not cleaned:
        return "Query Result"
    return cleaned[:1].upper() + cleaned[1:80]
