# Backend Features Plan

## Top-Level Overview

Extend the existing FastAPI backend with 8 features requested for the IBM Watson Challenge.
All 8 features build on top of the existing architecture (services, models, controllers, security)
without breaking the current pipeline. The work is organized into 6 focused sub-tasks,
each independently deliverable and reviewable.

**Confirmed decisions:**
- Cost estimate is **purely informational** — it does not block execution
- `GET /queries/saved` is filterable by both `user_id` and `tag`

**Scope**: `watson-challenge-2026/backend/`
**Out of scope**: Frontend changes, persistent database storage (all stores remain in-memory),
real AWS Athena cost integration.

---

## Design Decisions (confirmed)

| Feature | Decision |
|---|---|
| Cost estimation | Formula-based mock: table count + WHERE presence → bytes scanned → $5/TB rate |
| Approved queries | Auto-save on successful execution + explicit POST /queries/save with tags |
| Documentation export | GET /docs/export?user_id=X returns Markdown logbook |
| Anomaly thresholds | .env defaults + per-request overrides in QueryRequest body |

---

## Sub-Tasks

---

### Sub-Task 1 — Enrich Memory: Save Analysis Context

**Status**: [ ] pending

**Intent**
The current `memory_service` saves only `query` (NL text) and `sql` (generated SQL).
This sub-task extends each `Interaction` to also capture: tables referenced in the SQL,
filters applied (WHERE clause predicates), and the execution status.
This enriched context feeds into better LLM prompting and the documentation export (Sub-Task 5).

**Expected Outcomes**
- `Interaction` model has new fields: `tables_used`, `filters_applied`, `status`, `row_count`
- `save_interaction()` in `memory_service.py` accepts the new fields
- `query_service.py` passes the new fields when saving after execution
- `GET /memory/{user_id}` response includes the enriched fields

**Todo List**
1. Add `tables_used: list[str]`, `filters_applied: list[str]`, `status: str`, `row_count: int` to `Interaction` model in `models/memory.py`
2. Update `save_interaction()` signature in `services/memory_service.py` to accept the new fields
3. Add a helper `_extract_tables(sql: str) -> list[str]` in `memory_service.py` using a simple regex on `FROM` and `JOIN` keywords
4. Add a helper `_extract_filters(sql: str) -> list[str]` parsing `WHERE` clause tokens
5. Update `query_service.py` Step 9 to pass `tables_used`, `filters_applied`, `status`, `row_count` to `save_interaction()`

**Relevant Context**
- `watson-challenge-2026/backend/app/models/memory.py` — `Interaction` dataclass
- `watson-challenge-2026/backend/app/services/memory_service.py` — `save_interaction()`
- `watson-challenge-2026/backend/app/services/query_service.py` — Step 9 (line ~106)

---

### Sub-Task 2 — Cost Estimation Service + Endpoint

**Status**: [ ] pending

**Intent**
Add a cost estimation capability that evaluates SQL complexity and returns an estimated
scan size and dollar cost before execution. This is a mock implementation using a formula:
- Count referenced tables (each ~500MB base)
- Absence of a WHERE clause doubles the estimate (full scan)
- Rate: $5.00 per TB (BigQuery standard pricing)

Exposed both as an internal function (called in the query pipeline before execution)
and as a standalone `POST /cost/estimate` endpoint.

**Expected Outcomes**
- New `services/cost_service.py` with `estimate_cost(sql: str) -> CostEstimate`
- New `models/cost.py` with `CostEstimate` (bytes_scanned, estimated_cost_usd, table_count, has_filter, is_mock)
- New `controllers/cost_controller.py` with `POST /cost/estimate` endpoint
- `QueryResponse` includes a `cost_estimate` field
- Cost estimate is **purely informational** — it is attached to the response but does NOT block execution
- Query pipeline (Step 6, before execution) calls `estimate_cost()` and attaches to response

**Todo List**
1. Create `models/cost.py` with `CostEstimate` Pydantic model
2. Create `services/cost_service.py` implementing the formula-based `estimate_cost(sql: str) -> CostEstimate`
3. Create `controllers/cost_controller.py` with `POST /cost/estimate` accepting `{"sql": "..."}` and returning `CostEstimate`
4. Register the new router in `routers/routes.py`
5. Add `cost_estimate` field to `QueryResponse` in `models/query.py`
6. Call `estimate_cost()` in `query_service.py` after SQL validation (Step 5) and attach result to the final `QueryResponse`

**Relevant Context**
- `watson-challenge-2026/backend/app/models/query.py` — `QueryResponse`
- `watson-challenge-2026/backend/app/services/query_service.py` — step ordering
- `watson-challenge-2026/backend/app/routers/routes.py` — router registration pattern

---

### Sub-Task 3 — Approved/Saved Queries Service + Endpoints

**Status**: [ ] pending

**Intent**
Introduce a "saved queries" repository where validated, useful queries can be stored
for reuse. Queries are auto-saved on every successful execution and can also be
explicitly saved via a dedicated endpoint with optional tags and description.
Provides a `GET /queries/saved` endpoint for retrieval.

**Expected Outcomes**
- New `models/saved_query.py` with `SavedQuery` model (id, user_id, question, sql, tables_used, tags, description, created_at, auto_saved)
- New `services/saved_queries_service.py` with `auto_save()`, `save_query()`, `get_saved_queries()`, `delete_saved_query()`
- New `controllers/saved_queries_controller.py` with:
  - `GET /queries/saved?user_id=X&tag=Y` — list saved queries, filterable by `user_id` and optional `tag`
  - `POST /queries/save` — explicitly save with tags/description
  - `DELETE /queries/saved/{query_id}` — remove
- `query_service.py` calls `auto_save()` on successful execution (Step 9)

**Todo List**
1. Create `models/saved_query.py` with `SavedQuery` and `SaveQueryRequest` Pydantic models
2. Create `services/saved_queries_service.py` with in-memory store `_SAVED: dict[str, SavedQuery]` and the four public functions
3. Create `controllers/saved_queries_controller.py` with the three endpoints
4. Register the new router in `routers/routes.py`
5. In `query_service.py`, call `auto_save()` at Step 9 (alongside `save_interaction()`) on `status == "success"`

**Relevant Context**
- `watson-challenge-2026/backend/app/services/memory_service.py` — pattern to replicate for the in-memory store
- `watson-challenge-2026/backend/app/controllers/audit_controller.py` — controller pattern to follow
- `watson-challenge-2026/backend/app/routers/routes.py`

---

### Sub-Task 4 — SQL Validation Endpoint (Standalone)

**Status**: [ ] pending

**Intent**
The SQL validator already exists in `security/sql_validator.py` and is called internally
by the query pipeline. This sub-task exposes it as a dedicated `POST /sql/validate`
endpoint so the frontend can validate SQL independently (e.g. before showing the
approval dialog to the user) without triggering a full query execution.

**Expected Outcomes**
- New `controllers/sql_controller.py` with `POST /sql/validate` endpoint
- Endpoint accepts `{"sql": "..."}` and returns `{"valid": bool, "reason": str}`
- No changes to the existing `sql_validator.py` logic
- New router registered in `routers/routes.py`

**Todo List**
1. Create `controllers/sql_controller.py` with a single `POST /sql/validate` route
2. The handler calls the existing `validate_sql()` from `security/sql_validator.py` and returns its `ValidationResult`
3. Register the router in `routers/routes.py`

**Relevant Context**
- `watson-challenge-2026/backend/app/security/sql_validator.py` — `validate_sql()` already returns `ValidationResult(valid, reason)`
- `watson-challenge-2026/backend/app/controllers/query_controller.py` — controller pattern

---

### Sub-Task 5 — Documentation Export Endpoint (Markdown Logbook)

**Status**: [ ] pending

**Intent**
Generate a human-readable Markdown logbook for a user's session — suitable for
copy-paste into Confluence, Notion, or a daily standup doc. The logbook is assembled
from the enriched memory store (built in Sub-Task 1) and includes: session header,
each query with its SQL, tables used, filters, execution result summary, and insights.

**Expected Outcomes**
- New `services/docs_service.py` with `export_logbook(user_id: str) -> str` returning Markdown text
- New `controllers/docs_controller.py` with `GET /docs/export?user_id=X`
  - Returns `text/markdown` content-type with the logbook as the body
- Logbook structure per interaction:
  ```
  ## Query N — HH:MM
  **Question:** ...
  **SQL:**
  ```sql
  ...
  ```
  **Tables:** table_a, table_b
  **Filters:** col > value
  **Result:** N rows | Status: success
  ```

**Todo List**
1. Create `services/docs_service.py` with `export_logbook(user_id: str) -> str`
   - Pulls from `get_user_memory(user_id)` (enriched by Sub-Task 1)
   - Iterates interactions and formats each as a Markdown section
2. Create `controllers/docs_controller.py` with `GET /docs/export`
   - Uses FastAPI `Response` with `media_type="text/markdown"`
   - Returns 404 if user has no history
3. Register the router in `routers/routes.py`

**Relevant Context**
- `watson-challenge-2026/backend/app/services/memory_service.py` — `get_user_memory()`
- `watson-challenge-2026/backend/app/models/memory.py` — `UserMemory`, `Interaction` (enriched in Sub-Task 1)

---

### Sub-Task 6 — Configurable Anomaly Detection Rules

**Status**: [ ] pending

**Intent**
The `insights_service.py` currently uses hardcoded thresholds:
- CV > 30% triggers a "high variability" trend insight
- IQR multiplier is hardcoded to 1.5

This sub-task makes both thresholds configurable via `.env` defaults (applied globally)
with optional per-request overrides passed in `QueryRequest`. This satisfies the
requirement of "defining detection rules (e.g. variation > X%)".

**Expected Outcomes**
- `config.py` has two new settings: `ANOMALY_VARIATION_THRESHOLD` (default 30) and `ANOMALY_IQR_MULTIPLIER` (default 1.5)
- `analyze_results()` in `insights_service.py` accepts optional `variation_threshold` and `iqr_multiplier` parameters
- `QueryRequest` model gains an optional `anomaly_rules: AnomalyRules | None` field
- `query_service.py` passes the per-request thresholds (or falls back to config defaults) when calling `analyze_results()`
- New `models/anomaly.py` with `AnomalyRules` Pydantic model

**Todo List**
1. Add `ANOMALY_VARIATION_THRESHOLD: float = 30.0` and `ANOMALY_IQR_MULTIPLIER: float = 1.5` to `config.py`
2. Create `models/anomaly.py` with `AnomalyRules(variation_threshold: float | None, iqr_multiplier: float | None)`
3. Add `anomaly_rules: AnomalyRules | None = None` to `QueryRequest` in `models/query.py`
4. Update `analyze_results()` signature in `insights_service.py` to accept `variation_threshold: float` and `iqr_multiplier: float` with config defaults
5. Replace hardcoded `30` (CV threshold) and `1.5` (IQR multiplier) in `insights_service.py` with the passed parameters
6. In `query_service.py` Step 7, resolve thresholds (per-request if provided, else config defaults) and pass to `analyze_results()`
7. Update `.env.example` with the two new variables

**Relevant Context**
- `watson-challenge-2026/backend/app/config.py` — `Settings` class (Pydantic BaseSettings)
- `watson-challenge-2026/backend/app/services/insights_service.py` — `_analyse_numeric_column()` lines ~165 and ~63 (hardcoded values)
- `watson-challenge-2026/backend/app/models/query.py` — `QueryRequest`
- `watson-challenge-2026/backend/app/services/query_service.py` — Step 7 `self._analyse()`

---

## Execution Order

```
Sub-Task 1  →  Sub-Task 2  →  Sub-Task 3
    ↓
Sub-Task 4 (independent — no deps)
    ↓
Sub-Task 5 (depends on Sub-Task 1 for enriched memory)
    ↓
Sub-Task 6 (independent — only touches insights + config)
```

Sub-Tasks 4 and 6 are fully independent and can be done in any order.
Sub-Task 5 must come after Sub-Task 1.
Sub-Tasks 2 and 3 depend only on Sub-Task 1 (for the enriched memory fields on the response).

---

## Files Created / Modified Summary

| File | Action |
|---|---|
| `models/memory.py` | Modified — enrich `Interaction` |
| `models/cost.py` | Created |
| `models/saved_query.py` | Created |
| `models/anomaly.py` | Created |
| `models/query.py` | Modified — add `cost_estimate`, `anomaly_rules` |
| `services/memory_service.py` | Modified — enrich `save_interaction()` + extraction helpers |
| `services/cost_service.py` | Created |
| `services/saved_queries_service.py` | Created |
| `services/docs_service.py` | Created |
| `services/insights_service.py` | Modified — parameterize thresholds |
| `services/query_service.py` | Modified — wire new services into pipeline |
| `controllers/cost_controller.py` | Created |
| `controllers/sql_controller.py` | Created |
| `controllers/saved_queries_controller.py` | Created |
| `controllers/docs_controller.py` | Created |
| `routers/routes.py` | Modified — register 4 new routers |
| `config.py` | Modified — add anomaly threshold settings |
| `.env.example` | Modified — document new env vars |
