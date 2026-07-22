"""Smoke tests for remaining features (Sub-Tasks C, D, E, F)."""
import asyncio

# ── Sub-Task C: Next steps service ────────────────────────────────────────────
from app.services.next_steps_service import generate_next_steps, _rule_based_suggestions
from app.models.insight import InsightReport

stub = InsightReport(row_count=3, columns_analyzed=[], key_insights=[], trends=[], anomalies=[], summary="3 rows.")
suggestions = asyncio.run(generate_next_steps("top vendas por região", stub, [{"region": "North", "total": 100}]))
assert len(suggestions) == 3, f"expected 3, got {len(suggestions)}"
assert all(isinstance(s, str) and len(s) > 0 for s in suggestions)
print(f"Next steps OK: {suggestions[0][:50]}...")

# ── Sub-Task D: Query matching ────────────────────────────────────────────────
from app.services.saved_queries_service import auto_save, delete_saved_query
from app.services.query_matching_service import find_matching_query, _tokenise, _jaccard

# Token + Jaccard helpers
t1 = _tokenise("total sales by region last quarter")
t2 = _tokenise("sales grouped by region")
score = _jaccard(t1, t2)
assert score > 0, f"expected >0 jaccard, got {score}"
print(f"Jaccard OK: score={score:.3f}")

# End-to-end matching
sq = auto_save("u_test", "total sales grouped by region", "SELECT region, SUM(amount) FROM sales GROUP BY 1")
match = find_matching_query("sales total by region", user_id="u_test")
assert match is not None, "should find a match"
assert match.id == sq.id
delete_saved_query(sq.id)
no_match = find_matching_query("completely unrelated xyz abc 123", user_id="u_test")
assert no_match is None, f"should not match, got {no_match}"
print(f"Query matching OK: matched id={sq.id[:8]}...")

# ── Sub-Task E: Rich metadata ─────────────────────────────────────────────────
from app.models.response import ExecutionMetadataPayload, DataPayload
m = ExecutionMetadataPayload(execution_time_ms=12.5, bytes_processed=150_000_000, engine="mock-sqlite", row_count=4)
d = DataPayload(columns=["x"], rows=[{"x": 1}], row_count=1, execution_mode="mock", metadata=m)
dumped = d.model_dump()
assert dumped["metadata"]["execution_time_ms"] == 12.5
assert dumped["metadata"]["bytes_processed"] == 150_000_000
print(f"Rich metadata OK: engine={dumped['metadata']['engine']}, bytes={dumped['metadata']['bytes_processed']}")

# ── Sub-Task F: Update saved query ────────────────────────────────────────────
from app.services.saved_queries_service import save_query, update_saved_query
from app.models.saved_query import SaveQueryRequest, UpdateSavedQueryRequest

req = SaveQueryRequest(user_id="u2", question="what are orders", sql="SELECT * FROM orders", tags=["old"])
sq2 = save_query(req)
upd = update_saved_query(sq2.id, UpdateSavedQueryRequest(tags=["new", "test"], description="updated desc"))
assert upd is not None
assert upd.tags == ["new", "test"]
assert upd.description == "updated desc"
assert upd.sql == sq2.sql  # unchanged
not_found = update_saved_query("nonexistent", UpdateSavedQueryRequest(tags=["x"]))
assert not_found is None
print(f"Update saved query OK: tags={upd.tags}, desc={upd.description}")

# ── Copilot controller import ─────────────────────────────────────────────────
from app.controllers.copilot_controller import router as copilot_r
from fastapi.routing import APIRoute
paths = [r.path for r in copilot_r.routes if isinstance(r, APIRoute)]
assert "/copilot/next-steps" in paths, f"missing /copilot/next-steps in {paths}"
print(f"Copilot controller OK: {paths}")

# ── PATCH route in saved queries controller ───────────────────────────────────
from app.controllers.saved_queries_controller import router as sq_r
sq_paths = [r.path for r in sq_r.routes if isinstance(r, APIRoute)]
assert "/queries/saved/{query_id}" in sq_paths
assert "/queries/match" in sq_paths
print(f"Saved queries routes OK: {sq_paths}")

print("\nAll remaining feature smoke tests passed!")
