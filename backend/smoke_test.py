"""Smoke tests for all new backend features."""

# Test cost estimation
from app.services.cost_service import estimate_cost
est = estimate_cost("SELECT * FROM orders WHERE status = 1")
assert est.has_filter is True, "should detect WHERE"
assert est.table_count == 1
assert est.is_mock is True
est2 = estimate_cost("SELECT * FROM orders JOIN customers ON orders.cid = customers.id")
assert est2.has_filter is False, "no WHERE = full scan"
assert est2.table_count == 2
assert est2.estimated_cost_usd > est.estimated_cost_usd, "full scan should cost more"
print(f"Cost OK: filtered={est.estimated_cost_usd:.6f} USD  full_scan={est2.estimated_cost_usd:.6f} USD")

# Test memory enrichment helpers
from app.services.memory_service import _extract_tables, _extract_filters, save_interaction, get_user_memory

tables = _extract_tables("SELECT * FROM sales JOIN regions ON sales.rid = regions.id")
assert "sales" in tables and "regions" in tables, f"got {tables}"

filters = _extract_filters("SELECT * FROM t WHERE region = 'North' AND amount > 100")
assert len(filters) == 2, f"expected 2 filters, got {filters}"

save_interaction("u1", "test q", "SELECT * FROM sales WHERE id=1", status="success", row_count=5)
mem = get_user_memory("u1")
assert mem.interactions[0].tables_used == ["sales"]
assert mem.interactions[0].row_count == 5
assert mem.interactions[0].status == "success"
print(f"Memory OK: tables={mem.interactions[0].tables_used}, filters={mem.interactions[0].filters_applied}")

# Test saved queries
from app.services.saved_queries_service import auto_save, save_query, get_saved_queries, delete_saved_query
from app.models.saved_query import SaveQueryRequest

sq = auto_save("u1", "what are top sales?", "SELECT * FROM sales LIMIT 10")
assert sq.auto_saved is True

req = SaveQueryRequest(user_id="u1", question="manual save", sql="SELECT 1", tags=["test"], description="desc")
sq2 = save_query(req)
assert sq2.auto_saved is False
assert sq2.tags == ["test"]

results = get_saved_queries(user_id="u1")
assert len(results) == 2, f"expected 2, got {len(results)}"

tagged = get_saved_queries(user_id="u1", tag="test")
assert len(tagged) == 1, f"expected 1, got {len(tagged)}"

deleted = delete_saved_query(sq.id)
assert deleted is True
print(f"Saved queries OK: auto_saved={sq.auto_saved}, explicit tags={sq2.tags}")

# Test anomaly thresholds propagation
from app.services.insights_service import analyze_results

data = [
    {"region": "A", "val": 100},
    {"region": "B", "val": 1000},
    {"region": "C", "val": 105},
    {"region": "D", "val": 102},
]
report_strict = analyze_results(data, variation_threshold=5.0, iqr_multiplier=0.5)
report_loose  = analyze_results(data, variation_threshold=200.0, iqr_multiplier=5.0)
assert len(report_strict.anomalies) >= len(report_loose.anomalies), (
    f"strict should detect >= anomalies than loose: {len(report_strict.anomalies)} vs {len(report_loose.anomalies)}"
)
print(f"Anomaly thresholds OK: strict={len(report_strict.anomalies)} anomalies, loose={len(report_loose.anomalies)}")

# Test docs export
from app.services.docs_service import export_logbook

md = export_logbook("u1")
assert md is not None, "should return markdown for user with history"
assert "## Query 1" in md, "should contain query section"
assert "sales" in md, "should mention the sales table"
assert "id=1" in md or "id" in md, "should contain filter info"
none_result = export_logbook("nonexistent_user")
assert none_result is None, "should return None for user with no history"
print("Docs export OK")

# Test SQL validation controller model
from app.controllers.sql_controller import SqlValidateResponse
r = SqlValidateResponse(valid=True, reason="SQL is valid.")
assert r.valid is True
print("SQL controller model OK")

# Test each controller's routes are defined with expected paths
from fastapi.routing import APIRoute
from app.controllers.cost_controller import router as cost_r
from app.controllers.sql_controller import router as sql_r
from app.controllers.saved_queries_controller import router as sq_r
from app.controllers.docs_controller import router as docs_r

cost_paths  = [r.path for r in cost_r.routes if isinstance(r, APIRoute)]
sql_paths   = [r.path for r in sql_r.routes if isinstance(r, APIRoute)]
sq_paths    = [r.path for r in sq_r.routes if isinstance(r, APIRoute)]
docs_paths  = [r.path for r in docs_r.routes if isinstance(r, APIRoute)]

assert "/cost/estimate" in cost_paths, f"cost_paths={cost_paths}"
assert "/sql/validate" in sql_paths, f"sql_paths={sql_paths}"
assert "/queries/saved" in sq_paths, f"sq_paths={sq_paths}"
assert "/queries/save" in sq_paths, f"sq_paths={sq_paths}"
assert "/queries/saved/{query_id}" in sq_paths, f"sq_paths={sq_paths}"
assert "/docs/export" in docs_paths, f"docs_paths={docs_paths}"
print(f"Router registration OK: cost={cost_paths}, sql={sql_paths}, sq={sq_paths}, docs={docs_paths}")

print()
print("All smoke tests passed!")
