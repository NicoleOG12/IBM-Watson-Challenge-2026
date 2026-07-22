import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { delay, map, of, tap, Observable } from 'rxjs';
import { PipelineStep } from '../models/copilot.models';
import { CopilotStateService, BackendQueryResponse } from './copilot-state.service';

const API = '/api';

// ─────────────────────────────────────────────────────────────
// CopilotService
//
// ask()          → POST /api/query (full pipeline)
//                  Caches the full BackendQueryResponse in
//                  CopilotStateService for downstream steps.
// interpret()    → stays mock (no dedicated NLU endpoint;
//                  pipeline steps are synthesised from the response)
// getNextSteps() → reads from CopilotStateService cache
// ─────────────────────────────────────────────────────────────

// Hard-coded user for demo — replace with real auth session
const DEMO_USER = 'alex.rodrigues@acme.com';

@Injectable({ providedIn: 'root' })
export class CopilotService {
  private http  = inject(HttpClient);
  private state = inject(CopilotStateService);

  // ── POST /api/query ──────────────────────────────────────
  // Fires the full backend pipeline (NL→SQL→Execute→Insights).
  // Caches the response so sql.service and query.service can
  // read SQL and results without re-calling the backend.
  // Returns { sessionId } matching the shape the chat expects.
  // --------------------------------------------------------
  ask(question: string): Observable<{ sessionId: string }> {
    return this.http.post<BackendQueryResponse>(`${API}/query`, {
      user_id:                DEMO_USER,
      natural_language_query: question,
    }).pipe(
      tap(response => this.state.set(response)),
      map(response => {
        if (response.status === 'rejected') {
          const reason = response.result?.['explanation']
            ?? response.result?.['error']
            ?? 'This type of operation is not permitted. Only read-only analytical queries are allowed.';
          throw new Error(reason);
        }
        return { sessionId: response.query_id };
      }),
    );
    // ── MOCK (fallback) ─────────────────────────────────────
    // return of({ sessionId: 'sess_9f3a' }).pipe(delay(400));
  }

  // ── Stays mock — synthesised from pipeline response ──────
  // In the real flow, step statuses are derived from the
  // cached BackendQueryResponse by chat.component.ts.
  // --------------------------------------------------------
  interpret(question: string): Observable<PipelineStep[]> {
    // ── MOCK ────────────────────────────────────────────────
    return of(MOCK_PIPELINE_STEPS).pipe(delay(100));
    // ── REAL → POST /api/copilot/interpret (not yet implemented) ──
    // return this.http.post<PipelineStep[]>(`${API}/copilot/interpret`, { question });
  }

  // ── Read next steps from cached BackendQueryResponse ─────
  // The backend computes next steps inside POST /query.
  // We read them from the state cache to avoid a second API call
  // that would run rule-based suggestions instead of the cached ones.
  // --------------------------------------------------------
  getNextSteps(executionId: string): Observable<string[]> {
    const cached = this.state.lastResponse();
    if (cached?.next_steps && cached.next_steps.length > 0) {
      return of(cached.next_steps);
    }
    // ── Fallback: fetch from API when cache is empty ────────
    return this.http.get<{ next_steps: string[] }>(`${API}/copilot/next-steps`, {
      params: { execution_id: executionId },
    }).pipe(
      map(r => r.next_steps ?? []),
    );
  }
}

// ─────────────────────────────────────────────────────────────
//  MOCK DATA — kept as reference / fallback
// ─────────────────────────────────────────────────────────────

const MOCK_PIPELINE_STEPS: PipelineStep[] = [
  { label: 'NLU Interpretation',        status: 'done',   endpoint: 'POST /api/query' },
  { label: 'Catalog resolved',          status: 'done',   endpoint: 'GET /api/catalog/resolve' },
  { label: 'SQL generated via ICA',     status: 'done',   endpoint: 'POST /api/query' },
  { label: 'Cost estimated',            status: 'warn',   endpoint: 'POST /api/cost/estimate' },
  { label: 'Awaiting execution',        status: 'active', endpoint: 'POST /api/query' },
];

const MOCK_NEXT_STEPS: string[] = [
  'What was the total financial impact of this Q3 drop?',
  'Which regions were most affected?',
  'Compare with the same period last year',
  'Show products with the highest growth in the same period',
];
