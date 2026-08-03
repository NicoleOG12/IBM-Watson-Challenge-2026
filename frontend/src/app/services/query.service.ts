import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { delay, map, of, Observable } from 'rxjs';
import { QueryResult, HistoryEntry } from '../models/copilot.models';
import { CopilotStateService } from './copilot-state.service';

// ─────────────────────────────────────────────────────────────
// QueryService
//
// execute()    → resolves from CopilotStateService cache
//               (the backend already ran the query inside ask())
// getHistory() → GET /api/memory/{userId}
// cancel()     → stays mock (no cancel endpoint on the backend)
// ─────────────────────────────────────────────────────────────

const API = '/api';
const DEMO_USER = 'nicole.goncalves@acme.com';

@Injectable({ providedIn: 'root' })
export class QueryService {
  private http  = inject(HttpClient);
  private state = inject(CopilotStateService);

  // ── Resolves from cached BackendQueryResponse ────────────
  // The backend already executed the query inside POST /query.
  // We read the result from the state cache and map it to the
  // QueryResult shape the chat component expects.
  // --------------------------------------------------------
  execute(sessionId: string, sql: string): Observable<QueryResult> {
    const cached = this.state.lastResponse();
    if (cached?.result) {
      const d = cached.result.data;
      const meta = d.metadata;
      return of<QueryResult>({
        executionId: cached.query_id,
        rowCount:    d.row_count,
        durationMs:  meta?.execution_time_ms ?? 0,
        columns:     d.columns,
        rows:        d.rows,
        hasMore:     false,
      });
    }
    // ── MOCK fallback when no cached response ───────────────
    return of(MOCK_RESULT).pipe(delay(2300));
  }

  // ── GET /api/memory/{userId} ─────────────────────────────
  // Maps UserMemory.interactions to HistoryEntry[]
  // --------------------------------------------------------
  getHistory(userId: string = DEMO_USER, limit = 50): Observable<HistoryEntry[]> {
    return this.http.get<{ interactions: Array<{
      query:     string;
      sql:       string;
      timestamp: string;
      status:    string;
      row_count: number;
    }> }>(`${API}/memory/${userId}`).pipe(
      map(mem => (mem.interactions ?? []).slice(-limit).reverse().map((i, idx) => ({
        executionId: `hist_${idx}`,
        question:    i.query,
        engine:      'aws' as const,
        rowCount:    i.row_count ?? 0,
        durationMs:  0,
        timestamp:   new Date(i.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      }))),
    );
    // ── MOCK (fallback) ─────────────────────────────────────
    // return of(MOCK_HISTORY).pipe(delay(400));
  }

  // ── Stays mock — no cancel endpoint on the backend ───────
  cancel(sessionId: string): Observable<{ cancelled: boolean }> {
    return of({ cancelled: true }).pipe(delay(200));
  }

  // ── GET /api/query/results/:executionId — not implemented ─
  getResults(executionId: string): Observable<QueryResult> {
    return of(MOCK_RESULT).pipe(delay(300));
  }
}

// ─────────────────────────────────────────────────────────────
//  MOCK DATA — kept as reference / fallback
// ─────────────────────────────────────────────────────────────

export const MOCK_RESULT: QueryResult = {
  executionId: 'exec_7b2c',
  rowCount: 8,
  durationMs: 2300,
  columns: ['product_name', 'q2_revenue', 'q3_revenue', 'pct_change'],
  rows: [
    { product_name: 'Notebook Pro X15',      q2_revenue: 842000, q3_revenue: 506000, pct_change: -39.9 },
    { product_name: 'Monitor UltraWide 34"', q2_revenue: 621500, q3_revenue: 414200, pct_change: -33.3 },
    { product_name: 'Headset Gamer RGB',     q2_revenue: 310000, q3_revenue: 217000, pct_change: -30.0 },
    { product_name: 'Mechanical Keyboard Pro', q2_revenue: 198000, q3_revenue: 140000, pct_change: -29.3 },
    { product_name: 'Webcam 4K Ultra',       q2_revenue: 155000, q3_revenue: 112000, pct_change: -27.7 },
  ],
  hasMore: false,
};

const MOCK_HISTORY: HistoryEntry[] = [
  { executionId: 'exec_7b2c', question: 'Sales drop Q3 vs Q2 by product', engine: 'aws', rowCount: 8,  durationMs: 2300, timestamp: '09:16' },
  { executionId: 'exec_6a1d', question: 'Top 10 customers by revenue',    engine: 'aws', rowCount: 10, durationMs: 1800, timestamp: 'yesterday' },
  { executionId: 'exec_5c9e', question: 'Churn rate last month',          engine: 'redshift', rowCount: 1,  durationMs: 900,  timestamp: 'Mon' },
];
