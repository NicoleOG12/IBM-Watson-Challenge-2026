"""
insights_service.py — Automatic analysis of SQL query result sets.

Produces business-friendly insights, trends, and anomaly flags from any
list-of-dict result set returned by the execution service.

The analysis is purely statistical (no LLM call) and works on three levels:

  Key insights  — top/bottom performers, dominant categories, totals
  Trends        — spread / variance across numeric columns, distributions
  Anomalies     — outliers detected via IQR fence, empty results, nulls

Public API
----------
    from app.services.insights_service import analyze_results

    report = analyze_results(rows, columns)
    # report is an InsightReport
"""

import logging
import statistics
from typing import Any, List, Optional

from app.models.insight import Insight, InsightReport

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_float(value: Any) -> Optional[float]:
    """Try to coerce a value to float; return None on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value: float) -> str:
    """Format a float for display: integer-like → no decimals, else 2 dp."""
    return f"{value:,.0f}" if value == int(value) else f"{value:,.2f}"


def _numeric_values(rows: List[dict], col: str) -> List[float]:
    """Extract all non-null numeric values for a column across all rows."""
    result = []
    for row in rows:
        v = _to_float(row.get(col))
        if v is not None:
            result.append(v)
    return result


def _detect_outliers_iqr(values: List[float], iqr_multiplier: float = 1.5) -> List[float]:
    """
    Return values that fall outside [Q1 - k·IQR, Q3 + k·IQR].
    Requires at least 4 data points; returns [] otherwise.

    Args:
        values:         Numeric values to check.
        iqr_multiplier: Fence multiplier k (default 1.5, Tukey standard).
                        Smaller values detect more outliers; larger values fewer.
    """
    if len(values) < 4:
        return []
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    q1 = statistics.median(sorted_vals[: n // 2])
    q3 = statistics.median(sorted_vals[n // 2 + (n % 2):])
    iqr = q3 - q1
    if iqr == 0:
        return []
    low, high = q1 - iqr_multiplier * iqr, q3 + iqr_multiplier * iqr
    return [v for v in values if v < low or v > high]


def _label_column(col: str) -> str:
    """Turn a snake_case column name into a human label."""
    return col.replace("_", " ").strip()


# ---------------------------------------------------------------------------
# Per-column analysers
# ---------------------------------------------------------------------------

def _analyse_numeric_column(
    rows: List[dict],
    col: str,
    variation_threshold: float = 30.0,
    iqr_multiplier: float = 1.5,
) -> tuple[list[Insight], list[Insight], list[Insight]]:
    """
    Return (key_insights, trends, anomalies) for a single numeric column.

    Args:
        rows:               Result rows to analyse.
        col:                Column name to analyse.
        variation_threshold: CV (%) above which the column is flagged as highly variable.
        iqr_multiplier:      IQR fence multiplier for outlier detection.
    """
    key: list[Insight] = []
    trends: list[Insight] = []
    anomalies: list[Insight] = []

    values = _numeric_values(rows, col)
    if not values:
        return key, trends, anomalies

    label = _label_column(col)
    total = sum(values)
    mean = statistics.mean(values)
    n = len(values)
    max_val = max(values)
    min_val = min(values)

    # --- Key insight: total (only meaningful for aggregation columns) -------
    if n > 1:
        key.append(Insight(
            category="key_insight",
            message=f"Total {label}: {_fmt(total)} across {n} records.",
            value=_fmt(total),
            column=col,
        ))

    # --- Key insight: top row by this column --------------------------------
    top_row = max(rows, key=lambda r: _to_float(r.get(col)) or float("-inf"))
    key.append(Insight(
        category="key_insight",
        message=f"Highest {label} is {_fmt(max_val)}" + (
            f" (row: {_first_string_value(top_row, col)})." if _first_string_value(top_row, col) else "."
        ),
        value=_fmt(max_val),
        column=col,
    ))

    # --- Key insight: bottom row by this column -----------------------------
    if n > 1:
        bot_row = min(rows, key=lambda r: _to_float(r.get(col)) or float("inf"))
        key.append(Insight(
            category="key_insight",
            message=f"Lowest {label} is {_fmt(min_val)}" + (
                f" (row: {_first_string_value(bot_row, col)})." if _first_string_value(bot_row, col) else "."
            ),
            value=_fmt(min_val),
            column=col,
        ))

    # --- Trend: spread ratio ------------------------------------------------
    if n > 1 and min_val != 0:
        spread = max_val / min_val
        trends.append(Insight(
            category="trend",
            message=(
                f"{label.capitalize()} spans from {_fmt(min_val)} to {_fmt(max_val)} "
                f"— a {spread:.1f}× spread. "
                + ("Values are relatively uniform." if spread < 1.5 else
                   "There is notable variation between records.")
            ),
            column=col,
        ))

    # --- Trend: average -----------------------------------------------------
    if n > 1:
        trends.append(Insight(
            category="trend",
            message=f"Average {label}: {_fmt(mean)} per record.",
            value=_fmt(mean),
            column=col,
        ))

    # --- Trend: stdev (only if enough points) -------------------------------
    if n >= 3:
        try:
            stdev = statistics.stdev(values)
            cv = (stdev / mean * 100) if mean != 0 else 0
            if cv > variation_threshold:
                trends.append(Insight(
                    category="trend",
                    message=(
                        f"High variability in {label} (CV={cv:.0f}%, threshold={variation_threshold:.0f}%). "
                        "Some records are significantly above or below the average."
                    ),
                    column=col,
                ))
        except statistics.StatisticsError:
            pass

    # --- Anomalies: IQR outliers --------------------------------------------
    outliers = _detect_outliers_iqr(values, iqr_multiplier=iqr_multiplier)
    for outlier in outliers:
        anomalies.append(Insight(
            category="anomaly",
            message=(
                f"Unusual {label} value detected: {_fmt(outlier)}. "
                "This is significantly outside the typical range."
            ),
            value=_fmt(outlier),
            column=col,
        ))

    return key, trends, anomalies


def _first_string_value(row: dict, skip_col: str) -> Optional[str]:
    """Return the value of the first string column in a row (used as a row label)."""
    for k, v in row.items():
        if k == skip_col:
            continue
        if v is not None and _to_float(v) is None:
            return str(v)
    return None


def _analyse_string_column(
    rows: List[dict], col: str
) -> tuple[list[Insight], list[Insight], list[Insight]]:
    """
    Return (key_insights, trends, anomalies) for a categorical column.
    """
    key: list[Insight] = []
    trends: list[Insight] = []
    anomalies: list[Insight] = []

    values = [str(row.get(col, "")) for row in rows if row.get(col) is not None]
    if not values:
        return key, trends, anomalies

    label = _label_column(col)
    unique = list(dict.fromkeys(values))  # preserve order, deduplicate
    n_unique = len(unique)
    n_total = len(values)

    # --- Key insight: cardinality -------------------------------------------
    if n_unique == 1:
        key.append(Insight(
            category="key_insight",
            message=f"All {n_total} records share the same {label}: '{unique[0]}'.",
            value=unique[0],
            column=col,
        ))
    elif n_unique <= 10:
        key.append(Insight(
            category="key_insight",
            message=f"{label.capitalize()} has {n_unique} distinct values: {', '.join(unique)}.",
            column=col,
        ))
    else:
        key.append(Insight(
            category="key_insight",
            message=f"{label.capitalize()} contains {n_unique} unique values across {n_total} records.",
            column=col,
        ))

    # --- Trend: most frequent value -----------------------------------------
    freq: dict[str, int] = {}
    for v in values:
        freq[v] = freq.get(v, 0) + 1
    most_common = max(freq, key=lambda k: freq[k])
    pct = freq[most_common] / n_total * 100
    if n_unique > 1:
        trends.append(Insight(
            category="trend",
            message=(
                f"'{most_common}' is the most frequent {label}, "
                f"appearing in {freq[most_common]} of {n_total} records ({pct:.0f}%)."
            ),
            value=most_common,
            column=col,
        ))

    # --- Anomaly: null / empty values in source rows ------------------------
    null_count = sum(1 for row in rows if row.get(col) is None or str(row.get(col, "")).strip() == "")
    if null_count > 0:
        anomalies.append(Insight(
            category="anomaly",
            message=f"{null_count} record(s) have missing or empty {label} values.",
            value=str(null_count),
            column=col,
        ))

    return key, trends, anomalies


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def analyze_results(
    rows: List[dict],
    columns: Optional[List[str]] = None,
    variation_threshold: float = 30.0,
    iqr_multiplier: float = 1.5,
) -> InsightReport:
    """
    Analyse a SQL query result set and return a business-friendly InsightReport.

    The function auto-detects numeric vs. categorical columns and applies the
    appropriate analysis to each.

    Args:
        rows:                List of dicts, one per result row (as returned by execute_query).
        columns:             Optional ordered list of column names. Inferred from rows if omitted.
        variation_threshold: CV (%) above which a numeric column is flagged as highly variable.
                             Defaults to 30.0 (overridden by ANOMALY_VARIATION_THRESHOLD or per-request).
        iqr_multiplier:      IQR fence multiplier for outlier detection. Defaults to 1.5.
                             Overridden by ANOMALY_IQR_MULTIPLIER or per-request anomaly_rules.

    Returns:
        InsightReport with key_insights, trends, anomalies, and a plain summary.

    Example:
        >>> data = [
        ...     {"region": "North", "total_sales": 18450.75},
        ...     {"region": "East",  "total_sales": 15230.00},
        ...     {"region": "South", "total_sales": 9870.50},
        ...     {"region": "West",  "total_sales": 8200.00},
        ... ]
        >>> report = analyze_results(data)
        >>> report.key_insights[0].message
        'Total total sales: 51,751.25 across 4 records.'
    """
    if not rows:
        return InsightReport(
            row_count=0,
            columns_analyzed=[],
            key_insights=[Insight(
                category="key_insight",
                message="The query returned no results. Try broadening your filters.",
            )],
            trends=[],
            anomalies=[],
            summary="No data returned by the query.",
        )

    # Derive columns list
    if not columns:
        columns = list(rows[0].keys()) if rows else []

    all_key: list[Insight] = []
    all_trends: list[Insight] = []
    all_anomalies: list[Insight] = []
    analyzed_cols: list[str] = []

    for col in columns:
        num_vals = _numeric_values(rows, col)
        if len(num_vals) > len(rows) * 0.5:
            # Treat as numeric if more than half the rows have numeric values
            k, t, a = _analyse_numeric_column(
                rows, col,
                variation_threshold=variation_threshold,
                iqr_multiplier=iqr_multiplier,
            )
        else:
            k, t, a = _analyse_string_column(rows, col)

        if k or t or a:
            analyzed_cols.append(col)
        all_key.extend(k)
        all_trends.extend(t)
        all_anomalies.extend(a)

    # Build plain-English summary
    parts = [f"{len(rows)} record(s) analysed."]
    if all_key:
        parts.append(all_key[0].message)
    if all_anomalies:
        parts.append(f"{len(all_anomalies)} anomaly/anomalies detected.")
    else:
        parts.append("No anomalies detected.")
    summary = " ".join(parts)

    logger.info(
        "Insights generated",
        extra={
            "row_count": len(rows),
            "insights": len(all_key),
            "trends": len(all_trends),
            "anomalies": len(all_anomalies),
        },
    )

    return InsightReport(
        row_count=len(rows),
        columns_analyzed=analyzed_cols,
        key_insights=all_key,
        trends=all_trends,
        anomalies=all_anomalies,
        summary=summary,
    )
