"""
test_insights_service.py — Unit tests for app/services/insights_service.py

Run with:
    pytest tests/test_insights_service.py -v
"""

import pytest
from app.services.insights_service import analyze_results, _numeric_values, _detect_outliers_iqr
from app.models.insight import InsightReport, Insight


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

SALES_DATA = [
    {"region": "North", "total_sales": 18450.75},
    {"region": "East",  "total_sales": 15230.00},
    {"region": "South", "total_sales": 9870.50},
    {"region": "West",  "total_sales": 8200.00},
]

UNIFORM_DATA = [
    {"channel": "online",   "amount": 100.0},
    {"channel": "in-store", "amount": 100.0},
    {"channel": "partner",  "amount": 100.0},
]

SINGLE_ROW = [{"region": "North", "total_sales": 5000.0}]

EMPTY_DATA: list = []

NULL_DATA = [
    {"region": None,    "total_sales": 100.0},
    {"region": "South", "total_sales": 200.0},
    {"region": "",      "total_sales": 300.0},
]

OUTLIER_DATA = [
    {"metric": 10.0},
    {"metric": 11.0},
    {"metric": 12.0},
    {"metric": 11.5},
    {"metric": 10.5},
    {"metric": 500.0},   # outlier
]

COUNT_DATA = [
    {"region": "North", "cnt": 12},
    {"region": "South", "cnt": 8},
    {"region": "East",  "cnt": 15},
    {"region": "West",  "cnt": 5},
]


# ---------------------------------------------------------------------------
# 1. Return type & structure
# ---------------------------------------------------------------------------

class TestReturnType:
    def test_returns_insight_report(self):
        report = analyze_results(SALES_DATA)
        assert isinstance(report, InsightReport)

    def test_report_has_all_fields(self):
        report = analyze_results(SALES_DATA)
        assert hasattr(report, "row_count")
        assert hasattr(report, "columns_analyzed")
        assert hasattr(report, "key_insights")
        assert hasattr(report, "trends")
        assert hasattr(report, "anomalies")
        assert hasattr(report, "summary")

    def test_insights_are_insight_objects(self):
        report = analyze_results(SALES_DATA)
        for ins in report.key_insights + report.trends + report.anomalies:
            assert isinstance(ins, Insight)

    def test_insight_has_category_and_message(self):
        report = analyze_results(SALES_DATA)
        assert report.key_insights[0].category == "key_insight"
        assert len(report.key_insights[0].message) > 0

    def test_model_dump_serializable(self):
        report = analyze_results(SALES_DATA)
        d = report.model_dump()
        assert isinstance(d, dict)
        assert "key_insights" in d
        assert "summary" in d


# ---------------------------------------------------------------------------
# 2. Empty result set
# ---------------------------------------------------------------------------

class TestEmptyResults:
    def test_empty_returns_report(self):
        report = analyze_results(EMPTY_DATA)
        assert isinstance(report, InsightReport)

    def test_empty_row_count(self):
        report = analyze_results(EMPTY_DATA)
        assert report.row_count == 0

    def test_empty_has_no_data_insight(self):
        report = analyze_results(EMPTY_DATA)
        assert any("no results" in i.message.lower() or "no data" in i.message.lower()
                   for i in report.key_insights)

    def test_empty_summary_mentions_no_data(self):
        report = analyze_results(EMPTY_DATA)
        assert "no data" in report.summary.lower() or "no result" in report.summary.lower()


# ---------------------------------------------------------------------------
# 3. Row count accuracy
# ---------------------------------------------------------------------------

class TestRowCount:
    def test_row_count_matches_input(self):
        report = analyze_results(SALES_DATA)
        assert report.row_count == 4

    def test_single_row(self):
        report = analyze_results(SINGLE_ROW)
        assert report.row_count == 1

    def test_summary_mentions_record_count(self):
        report = analyze_results(SALES_DATA)
        assert "4" in report.summary


# ---------------------------------------------------------------------------
# 4. Key insights — numeric column
# ---------------------------------------------------------------------------

class TestNumericInsights:
    def test_produces_key_insights(self):
        report = analyze_results(SALES_DATA)
        assert len(report.key_insights) > 0

    def test_top_value_mentioned(self):
        report = analyze_results(SALES_DATA)
        messages = " ".join(i.message for i in report.key_insights)
        assert "18,450" in messages or "18450" in messages

    def test_lowest_value_mentioned(self):
        report = analyze_results(SALES_DATA)
        messages = " ".join(i.message for i in report.key_insights)
        assert "8,200" in messages or "8200" in messages

    def test_total_calculated(self):
        report = analyze_results(SALES_DATA)
        messages = " ".join(i.message for i in report.key_insights)
        # sum = 51,751.25
        assert "51,751" in messages or "51751" in messages

    def test_count_data_insights(self):
        report = analyze_results(COUNT_DATA)
        messages = " ".join(i.message for i in report.key_insights)
        assert "15" in messages  # max is 15


# ---------------------------------------------------------------------------
# 5. Trends
# ---------------------------------------------------------------------------

class TestTrends:
    def test_produces_trends(self):
        report = analyze_results(SALES_DATA)
        assert len(report.trends) > 0

    def test_trend_category_label(self):
        report = analyze_results(SALES_DATA)
        assert all(t.category == "trend" for t in report.trends)

    def test_spread_mentioned(self):
        report = analyze_results(SALES_DATA)
        messages = " ".join(t.message for t in report.trends)
        assert "spread" in messages.lower() or "average" in messages.lower()

    def test_average_trend_present(self):
        report = analyze_results(SALES_DATA)
        messages = " ".join(t.message for t in report.trends)
        assert "average" in messages.lower()

    def test_uniform_data_no_high_variability(self):
        report = analyze_results(UNIFORM_DATA)
        messages = " ".join(t.message for t in report.trends)
        assert "high variability" not in messages.lower()


# ---------------------------------------------------------------------------
# 6. Anomaly detection
# ---------------------------------------------------------------------------

class TestAnomalyDetection:
    def test_no_anomalies_in_normal_data(self):
        report = analyze_results(SALES_DATA)
        assert len(report.anomalies) == 0

    def test_summary_no_anomalies(self):
        report = analyze_results(SALES_DATA)
        assert "no anomalies" in report.summary.lower()

    def test_outlier_detected(self):
        report = analyze_results(OUTLIER_DATA)
        assert len(report.anomalies) > 0
        assert any("500" in a.message for a in report.anomalies)

    def test_anomaly_category_label(self):
        report = analyze_results(OUTLIER_DATA)
        assert all(a.category == "anomaly" for a in report.anomalies)

    def test_null_values_flagged(self):
        report = analyze_results(NULL_DATA)
        anomaly_messages = " ".join(a.message for a in report.anomalies)
        assert "missing" in anomaly_messages.lower() or "empty" in anomaly_messages.lower()

    def test_summary_mentions_anomalies_when_present(self):
        report = analyze_results(OUTLIER_DATA)
        assert "anomal" in report.summary.lower()


# ---------------------------------------------------------------------------
# 7. Categorical column analysis
# ---------------------------------------------------------------------------

class TestCategoricalColumn:
    def test_distinct_values_mentioned(self):
        report = analyze_results(SALES_DATA, columns=["region"])
        messages = " ".join(i.message for i in report.key_insights)
        assert "4" in messages  # 4 distinct regions

    def test_most_frequent_in_trends(self):
        data = [
            {"channel": "online"},
            {"channel": "online"},
            {"channel": "in-store"},
        ]
        report = analyze_results(data, columns=["channel"])
        messages = " ".join(t.message for t in report.trends)
        assert "online" in messages

    def test_single_category_all_same(self):
        data = [{"region": "North"}, {"region": "North"}, {"region": "North"}]
        report = analyze_results(data, columns=["region"])
        messages = " ".join(i.message for i in report.key_insights)
        assert "same" in messages.lower() or "north" in messages.lower()


# ---------------------------------------------------------------------------
# 8. columns parameter
# ---------------------------------------------------------------------------

class TestColumnsParam:
    def test_explicit_columns_respected(self):
        report = analyze_results(SALES_DATA, columns=["total_sales"])
        assert "region" not in report.columns_analyzed

    def test_inferred_columns_from_rows(self):
        report = analyze_results(SALES_DATA)
        assert len(report.columns_analyzed) > 0


# ---------------------------------------------------------------------------
# 9. Internal helpers
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_numeric_values_extraction(self):
        vals = _numeric_values(SALES_DATA, "total_sales")
        assert vals == [18450.75, 15230.00, 9870.50, 8200.00]

    def test_numeric_values_skips_non_numeric(self):
        vals = _numeric_values(SALES_DATA, "region")
        assert vals == []

    def test_detect_outliers_iqr_finds_outlier(self):
        vals = [10.0, 11.0, 12.0, 11.5, 10.5, 500.0]
        outliers = _detect_outliers_iqr(vals)
        assert 500.0 in outliers

    def test_detect_outliers_iqr_no_outlier(self):
        vals = [10.0, 11.0, 12.0, 11.5, 10.5, 10.8]
        outliers = _detect_outliers_iqr(vals)
        assert len(outliers) == 0

    def test_detect_outliers_requires_minimum_points(self):
        outliers = _detect_outliers_iqr([1.0, 2.0, 3.0])
        assert outliers == []
