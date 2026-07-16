import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { delay, of, Observable } from 'rxjs';
import { QueryResult, HistoryEntry } from '../models/copilot.models';

// ─────────────────────────────────────────────────────────────
// QueryService
//
// PARA ALTERNAR ENTRE MOCK E REAL:
//   → Mock  : bloco `of(MOCK_*).pipe(delay(ms))`  ← ATIVO
//   → Real  : descomente `this.http.*` e comente o bloco MOCK
// ─────────────────────────────────────────────────────────────

const API = '/api';

@Injectable({ providedIn: 'root' })
export class QueryService {
  // REAL → descomente:
  // private http = inject(HttpClient);

  // ── POST /api/query/execute ──────────────────────────────
  // Corpo: { sessionId: string; sql: string; engine: 'bigquery'|'redshift' }
  // Resposta: QueryResult
  // --------------------------------------------------------
  execute(sessionId: string, sql: string): Observable<QueryResult> {
    // ── MOCK ────────────────────────────────────────────────
    return of(MOCK_RESULT).pipe(delay(2300));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.post<QueryResult>(`${API}/query/execute`, {
    //   sessionId,
    //   sql,
    //   engine: 'bigquery',
    // });
  }

  // ── GET /api/query/results/:executionId ─────────────────
  // Query params opcionais: ?format=csv&page=1&pageSize=50
  // Resposta: QueryResult (paginado)
  // --------------------------------------------------------
  getResults(executionId: string, format?: 'json' | 'csv'): Observable<QueryResult> {
    // ── MOCK ────────────────────────────────────────────────
    return of(MOCK_RESULT).pipe(delay(300));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.get<QueryResult>(`${API}/query/results/${executionId}`, {
    //   params: format ? { format } : {},
    // });
  }

  // ── DELETE /api/query/cancel/:sessionId ─────────────────
  // Resposta: { cancelled: boolean }
  // --------------------------------------------------------
  cancel(sessionId: string): Observable<{ cancelled: boolean }> {
    // ── MOCK ────────────────────────────────────────────────
    return of({ cancelled: true }).pipe(delay(200));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.delete<{ cancelled: boolean }>(`${API}/query/cancel/${sessionId}`);
  }

  // ── GET /api/queries/history ────────────────────────────
  // Query params: ?userId=&limit=50
  // Resposta: HistoryEntry[]
  // --------------------------------------------------------
  getHistory(userId: string, limit = 50): Observable<HistoryEntry[]> {
    // ── MOCK ────────────────────────────────────────────────
    return of(MOCK_HISTORY).pipe(delay(400));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.get<HistoryEntry[]>(`${API}/queries/history`, {
    //   params: { userId, limit: String(limit) },
    // });
  }
}

// ─────────────────────────────────────────────────────────────
//  MOCK DATA
// ─────────────────────────────────────────────────────────────

export const MOCK_RESULT: QueryResult = {
  executionId: 'exec_7b2c',
  rowCount: 8,
  durationMs: 2300,
  columns: ['product_name', 'q2_revenue', 'q3_revenue', 'pct_change'],
  rows: [
    { product_name: 'Notebook Pro X15',    q2_revenue: 842000, q3_revenue: 506000, pct_change: -39.9 },
    { product_name: 'Monitor UltraWide 34"', q2_revenue: 621500, q3_revenue: 414200, pct_change: -33.3 },
    { product_name: 'Headset Gamer RGB',   q2_revenue: 310000, q3_revenue: 217000, pct_change: -30.0 },
    { product_name: 'Teclado Mecânico Pro', q2_revenue: 198000, q3_revenue: 140000, pct_change: -29.3 },
    { product_name: 'Webcam 4K Ultra',     q2_revenue: 155000, q3_revenue: 112000, pct_change: -27.7 },
  ],
  hasMore: true,
};

const MOCK_HISTORY: HistoryEntry[] = [
  { executionId: 'exec_7b2c', question: 'Queda de vendas Q3 vs Q2 por produto', engine: 'bigquery', rowCount: 8,  durationMs: 2300, timestamp: '09:16' },
  { executionId: 'exec_6a1d', question: 'Top 10 clientes por receita',           engine: 'bigquery', rowCount: 10, durationMs: 1800, timestamp: 'ontem' },
  { executionId: 'exec_5c9e', question: 'Churn rate do último mês',              engine: 'redshift', rowCount: 1,  durationMs: 900,  timestamp: 'seg' },
];
