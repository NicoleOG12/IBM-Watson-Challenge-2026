import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { delay, of, Observable } from 'rxjs';
import { ChatMessage, Insight, PipelineStep, SqlPreview, QueryResult } from '../models/copilot.models';

// ─────────────────────────────────────────────────────────────
// CopilotService
//
// PARA ALTERNAR ENTRE MOCK E REAL:
//   → Mock  : retorna `of(MOCK_DATA).pipe(delay(ms))`   ← ATIVO
//   → Real  : descomente o bloco `return this.http.post(...)` e
//             comente o bloco `return of(...).pipe(delay(...))`
// ─────────────────────────────────────────────────────────────

const API = '/api';   // ← ajuste a base URL para produção (environment.ts)

@Injectable({ providedIn: 'root' })
export class CopilotService {
  // MOCK → sem injeção de HttpClient necessária
  // REAL → descomente a linha abaixo:
  // private http = inject(HttpClient);

  // ── POST /api/copilot/ask ────────────────────────────────
  // Corpo: { question: string; userId: string; sessionId: string; dbEngine: 'bigquery'|'redshift' }
  // Resposta: stream de eventos SSE ou polling de status
  // --------------------------------------------------------
  ask(question: string): Observable<{ sessionId: string }> {
    // ── MOCK ────────────────────────────────────────────────
    return of({ sessionId: 'sess_9f3a' }).pipe(delay(400));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.post<{ sessionId: string }>(`${API}/copilot/ask`, {
    //   question,
    //   userId: 'alex.rodrigues@acme.com',
    //   sessionId: crypto.randomUUID(),
    //   dbEngine: 'bigquery',
    // });
  }

  // ── POST /api/copilot/interpret ──────────────────────────
  // Corpo: { question: string }
  // Resposta: { intent: string; entities: Record<string, string>; confidence: number }
  // --------------------------------------------------------
  interpret(question: string): Observable<PipelineStep[]> {
    // ── MOCK ────────────────────────────────────────────────
    return of(MOCK_PIPELINE_STEPS).pipe(delay(800));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.post<PipelineStep[]>(`${API}/copilot/interpret`, { question });
  }

  // ── GET /api/copilot/next-steps?executionId= ────────────
  // Resposta: { suggestions: string[] }
  // --------------------------------------------------------
  getNextSteps(executionId: string): Observable<string[]> {
    // ── MOCK ────────────────────────────────────────────────
    return of(MOCK_NEXT_STEPS).pipe(delay(600));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.get<string[]>(`${API}/copilot/next-steps`, {
    //   params: { executionId },
    // });
  }
}

// ─────────────────────────────────────────────────────────────
//  MOCK DATA — remover quando migrar para endpoints reais
// ─────────────────────────────────────────────────────────────

const MOCK_PIPELINE_STEPS: PipelineStep[] = [
  { label: 'Interpretação NLU',   status: 'done', endpoint: 'POST /api/copilot/interpret' },
  { label: 'Catálogo resolvido',  status: 'done', endpoint: 'GET /api/catalog/resolve' },
  { label: 'SQL gerado',          status: 'done', endpoint: 'POST /api/sql/generate' },
  { label: 'Custo estimado',      status: 'warn', endpoint: 'POST /api/sql/estimate-cost' },
  { label: 'Aguardando execução', status: 'active', endpoint: 'POST /api/query/execute' },
];

const MOCK_NEXT_STEPS: string[] = [
  'Qual foi o impacto financeiro total dessa queda no Q3?',
  'Quais regiões foram mais afetadas pela queda do Notebook Pro X15?',
  'Compare com o mesmo período do ano anterior (Q3 2023 vs Q3 2024)',
  'Mostre os produtos com maior crescimento no mesmo período',
];
