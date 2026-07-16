import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { delay, of, Observable } from 'rxjs';
import { Insight } from '../models/copilot.models';

// ─────────────────────────────────────────────────────────────
// InsightsService
//
// PARA ALTERNAR ENTRE MOCK E REAL:
//   → Mock  : bloco `of(MOCK_INSIGHTS).pipe(delay(ms))`  ← ATIVO
//   → Real  : descomente `this.http.post(...)` e comente o MOCK
// ─────────────────────────────────────────────────────────────

const API = '/api';

@Injectable({ providedIn: 'root' })
export class InsightsService {
  // REAL → descomente:
  // private http = inject(HttpClient);

  // ── POST /api/insights/generate ─────────────────────────
  // Corpo: { executionId: string; context: string }
  // Resposta: { insights: Insight[] }
  // O IBM Bob analisa o resultado da query e gera insights
  // em linguagem de negócio (pt-BR)
  // --------------------------------------------------------
  generate(executionId: string): Observable<Insight[]> {
    // ── MOCK ────────────────────────────────────────────────
    return of(MOCK_INSIGHTS).pipe(delay(1200));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.post<Insight[]>(`${API}/insights/generate`, {
    //   executionId,
    //   context: 'sales_drop_q3_vs_q2',
    // });
  }
}

// ─────────────────────────────────────────────────────────────
//  MOCK DATA
// ─────────────────────────────────────────────────────────────

export const MOCK_INSIGHTS: Insight[] = [
  {
    type: 'warning',
    icon: '⚠',
    text: 'Notebook Pro X15 apresentou a maior queda (−39,9%). Coincide com o lançamento do concorrente ModelX em agosto/2024. Recomenda-se análise de precificação.',
  },
  {
    type: 'info',
    icon: 'ℹ',
    text: 'Os 3 produtos com maior queda pertencem à categoria Periféricos Premium, sugerindo tendência de categoria, não apenas produtos isolados.',
  },
  {
    type: 'positive',
    icon: '↑',
    text: 'Apesar das quedas, o volume de unidades vendidas dos produtos afetados cresceu 8% — queda de receita pode ser explicada por promoções agressivas no Q3.',
  },
];
