import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { delay, of, Observable } from 'rxjs';
import { SavedQuestion } from '../models/copilot.models';

// ─────────────────────────────────────────────────────────────
// QuestionsService
//
// PARA ALTERNAR ENTRE MOCK E REAL:
//   → Mock  : bloco `of(MOCK_*).pipe(delay(ms))`  ← ATIVO
//   → Real  : descomente `this.http.*` e comente o bloco MOCK
// ─────────────────────────────────────────────────────────────

const API = '/api';

@Injectable({ providedIn: 'root' })
export class QuestionsService {
  // REAL → descomente:
  // private http = inject(HttpClient);

  // ── GET /api/questions/saved?userId= ────────────────────
  // Resposta: SavedQuestion[]
  // --------------------------------------------------------
  getSaved(userId: string): Observable<SavedQuestion[]> {
    // ── MOCK ────────────────────────────────────────────────
    return of(MOCK_SAVED).pipe(delay(400));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.get<SavedQuestion[]>(`${API}/questions/saved`, {
    //   params: { userId },
    // });
  }

  // ── GET /api/questions/suggested?userId= ────────────────
  // Chips de pergunta rápida exibidos abaixo do chat
  // Resposta: string[]
  // --------------------------------------------------------
  getSuggested(userId: string): Observable<string[]> {
    // ── MOCK ────────────────────────────────────────────────
    return of(MOCK_SUGGESTED).pipe(delay(300));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.get<string[]>(`${API}/questions/suggested`, {
    //   params: { userId },
    // });
  }

  // ── GET /api/questions/saved?similar=true&intent= ───────
  // Resposta: SavedQuestion[] — perguntas similares no catálogo
  // --------------------------------------------------------
  getSimilar(intent: string): Observable<SavedQuestion[]> {
    // ── MOCK ────────────────────────────────────────────────
    return of(MOCK_SAVED).pipe(delay(400));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.get<SavedQuestion[]>(`${API}/questions/saved`, {
    //   params: { similar: 'true', intent },
    // });
  }

  // ── POST /api/questions/save ─────────────────────────────
  // Corpo: { question: string; sql: string; insights: string; tags: string[] }
  // Resposta: SavedQuestion
  // --------------------------------------------------------
  save(payload: Partial<SavedQuestion>): Observable<SavedQuestion> {
    // ── MOCK ────────────────────────────────────────────────
    return of({ ...MOCK_SAVED[0], ...payload } as SavedQuestion).pipe(delay(300));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.post<SavedQuestion>(`${API}/questions/save`, payload);
  }
}

// ─────────────────────────────────────────────────────────────
//  MOCK DATA
// ─────────────────────────────────────────────────────────────

const MOCK_SAVED: SavedQuestion[] = [
  {
    id: 'q1',
    question: 'Variação de vendas por produto',
    sql: 'SELECT product_name, ...',
    tags: ['Sales Analytics'],
    intent: 'sales_drop',
    validated: true,
  },
];

const MOCK_SUGGESTED: string[] = [
  'Top 10 clientes por receita',
  'Ticket médio por canal',
  'Churn rate do mês',
  'Estoque crítico',
  'Inadimplência atual',
];
