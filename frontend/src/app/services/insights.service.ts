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
    text: 'Notebook Pro X15 showed the largest drop (−39.9%). This coincides with the launch of competitor ModelX in August 2024. A pricing analysis is recommended.',
  },
  {
    type: 'info',
    icon: 'ℹ',
    text: 'The 3 products with the largest drops belong to the Premium Peripherals category, suggesting a category trend rather than isolated products.',
  },
  {
    type: 'positive',
    icon: '↑',
    text: 'Despite the revenue drops, unit sales volume for the affected products grew 8% — the revenue decline may be explained by aggressive Q3 promotions.',
  },
];
