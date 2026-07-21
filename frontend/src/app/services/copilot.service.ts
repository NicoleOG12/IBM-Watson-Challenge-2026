import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { delay, map, of, tap, Observable } from 'rxjs';
import { PipelineStep } from '../models/copilot.models';
import { CopilotStateService, BackendQueryResponse } from './copilot-state.service';

// ─────────────────────────────────────────────────────────────
// CopilotService
//
// ask()          → POST /api/query (full pipeline)
//                  Caches the full BackendQueryResponse in
//                  CopilotStateService for downstream steps.
// interpret()    → stays mock (no dedicated NLU endpoint;
//                  pipeline steps are synthesised from the response)
// getNextSteps() → GET /api/copilot/next-steps?execution_id=
// ─────────────────────────────────────────────────────────────

const API = '/api';

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
      map(response => ({ sessionId: response.query_id })),
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

  // ── GET /api/copilot/next-steps?execution_id= ────────────
  // Returns LLM-generated follow-up question suggestions.
  // Falls back to mock when the backend endpoint is not yet live.
  // --------------------------------------------------------
  getNextSteps(executionId: string): Observable<string[]> {
    return this.http.get<{ next_steps: string[] }>(`${API}/copilot/next-steps`, {
      params: { execution_id: executionId },
    }).pipe(
      map(r => r.next_steps ?? []),
    );
    // ── MOCK (fallback) ─────────────────────────────────────
    // return of(MOCK_NEXT_STEPS).pipe(delay(600));
  }
}

// ─────────────────────────────────────────────────────────────
//  MOCK DATA — kept as reference / fallback
// ─────────────────────────────────────────────────────────────

const MOCK_PIPELINE_STEPS: PipelineStep[] = [
  { label: 'Interpretação NLU',   status: 'done', endpoint: 'POST /api/query' },
  { label: 'Catálogo resolvido',  status: 'done', endpoint: 'GET /api/catalog/resolve' },
  { label: 'SQL gerado',          status: 'done', endpoint: 'POST /api/query' },
  { label: 'Custo estimado',      status: 'warn', endpoint: 'POST /api/cost/estimate' },
  { label: 'Aguardando execução', status: 'active', endpoint: 'POST /api/query' },
];

const MOCK_NEXT_STEPS: string[] = [
  'Qual foi o impacto financeiro total dessa queda no Q3?',
  'Quais regiões foram mais afetadas?',
  'Compare com o mesmo período do ano anterior',
  'Mostre os produtos com maior crescimento no mesmo período',
];
