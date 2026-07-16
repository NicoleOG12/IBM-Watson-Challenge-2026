import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { delay, of, Observable } from 'rxjs';
import { SqlPreview, CostEstimate, SqlValidation } from '../models/copilot.models';

// ─────────────────────────────────────────────────────────────
// SqlService
//
// PARA ALTERNAR ENTRE MOCK E REAL:
//   → Mock  : bloco `of(MOCK_*).pipe(delay(ms))`  ← ATIVO
//   → Real  : descomente `this.http.*` e comente o bloco MOCK
// ─────────────────────────────────────────────────────────────

const API = '/api';

@Injectable({ providedIn: 'root' })
export class SqlService {
  // REAL → descomente:
  // private http = inject(HttpClient);

  // ── POST /api/sql/generate ───────────────────────────────
  // Corpo: { intent: string; tables: string[]; question: string }
  // Resposta: { sql: string; sessionId: string }
  // --------------------------------------------------------
  generate(question: string): Observable<SqlPreview> {
    // ── MOCK ────────────────────────────────────────────────
    return of(MOCK_SQL_PREVIEW).pipe(delay(900));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.post<SqlPreview>(`${API}/sql/generate`, {
    //   intent: 'sales_drop_comparison',
    //   tables: ['acme-prod.sales.transactions', 'acme-prod.products.catalog'],
    //   question,
    // });
  }

  // ── POST /api/sql/validate ───────────────────────────────
  // Corpo: { sql: string }
  // Resposta: { safe: boolean; warnings: string[] }
  // --------------------------------------------------------
  validate(sql: string): Observable<SqlValidation> {
    // ── MOCK ────────────────────────────────────────────────
    return of({ safe: true, warnings: [] }).pipe(delay(300));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.post<SqlValidation>(`${API}/sql/validate`, { sql });
  }

  // ── POST /api/sql/estimate-cost ─────────────────────────
  // Corpo: { sql: string; engine: 'bigquery'|'redshift' }
  // Resposta: CostEstimate
  // --------------------------------------------------------
  estimateCost(sql: string): Observable<CostEstimate> {
    // ── MOCK ────────────────────────────────────────────────
    return of(MOCK_COST).pipe(delay(500));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.post<CostEstimate>(`${API}/sql/estimate-cost`, {
    //   sql,
    //   engine: 'bigquery',
    // });
  }

  // ── PUT /api/sql/override ────────────────────────────────
  // Corpo: { sessionId: string; sql: string }
  // Resposta: SqlPreview atualizado
  // --------------------------------------------------------
  override(sessionId: string, sql: string): Observable<SqlPreview> {
    // ── MOCK ────────────────────────────────────────────────
    return of({ ...MOCK_SQL_PREVIEW, sql }).pipe(delay(300));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.put<SqlPreview>(`${API}/sql/override`, { sessionId, sql });
  }
}

// ─────────────────────────────────────────────────────────────
//  MOCK DATA
// ─────────────────────────────────────────────────────────────

const MOCK_COST: CostEstimate = {
  bytesScanned: '~4.7 GB',
  estimatedCost: '$0.023',
  table: 'acme-prod.sales.transactions',
  engine: 'bigquery',
};

export const MOCK_SQL_PREVIEW: SqlPreview = {
  sessionId: 'sess_9f3a',
  generatedAt: '09:15:22',
  table: 'acme-prod.sales.transactions',
  validation: { safe: true, warnings: [] },
  cost: MOCK_COST,
  sql: `WITH quarterly_sales AS (
  SELECT
    product_id,
    product_name,
    SUM(CASE WHEN quarter = 'Q2' THEN revenue END) AS q2_revenue,
    SUM(CASE WHEN quarter = 'Q3' THEN revenue END) AS q3_revenue
  FROM \`acme-prod.sales.transactions\`
  WHERE year = 2024
    AND quarter IN ('Q2', 'Q3')
  GROUP BY 1, 2
)
SELECT
  product_name,
  q2_revenue,
  q3_revenue,
  ROUND((q3_revenue - q2_revenue) / q2_revenue * 100, 2) AS pct_change
FROM quarterly_sales
WHERE (q3_revenue - q2_revenue) / q2_revenue * 100 < -20
ORDER BY pct_change ASC
LIMIT 50;`,
};
