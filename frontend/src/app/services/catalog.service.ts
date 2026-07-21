import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { delay, of, Observable } from 'rxjs';
import { CatalogTable } from '../models/copilot.models';

// ─────────────────────────────────────────────────────────────
// CatalogService
//
// PARA ALTERNAR ENTRE MOCK E REAL:
//   → Mock  : bloco `of(MOCK_*).pipe(delay(ms))`  ← ATIVO
//   → Real  : descomente `this.http.*` e comente o bloco MOCK
// ─────────────────────────────────────────────────────────────

const API = '/api';

@Injectable({ providedIn: 'root' })
export class CatalogService {
  // REAL → descomente:
  // private http = inject(HttpClient);

  // ── GET /api/catalog/tables ──────────────────────────────
  // Resposta: CatalogTable[]
  // --------------------------------------------------------
  listTables(): Observable<CatalogTable[]> {
    // ── MOCK ────────────────────────────────────────────────
    return of(MOCK_TABLES).pipe(delay(400));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.get<CatalogTable[]>(`${API}/catalog/tables`);
  }

  // ── GET /api/catalog/tables/:tableId ────────────────────
  // Resposta: CatalogTable (schema completo)
  // --------------------------------------------------------
  getTable(tableId: string): Observable<CatalogTable> {
    // ── MOCK ────────────────────────────────────────────────
    return of(MOCK_TABLES[0]).pipe(delay(300));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.get<CatalogTable>(`${API}/catalog/tables/${tableId}`);
  }

  // ── GET /api/catalog/resolve?intent= ────────────────────
  // Resposta: CatalogTable[] — tabelas relevantes para o intent
  // --------------------------------------------------------
  resolveByIntent(intent: string): Observable<CatalogTable[]> {
    // ── MOCK ────────────────────────────────────────────────
    return of(MOCK_TABLES).pipe(delay(500));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.get<CatalogTable[]>(`${API}/catalog/resolve`, {
    //   params: { intent },
    // });
  }
}

// ─────────────────────────────────────────────────────────────
//  MOCK DATA
// ─────────────────────────────────────────────────────────────

export const MOCK_TABLES: CatalogTable[] = [
  {
    id: 'acme-prod.sales.transactions',
    fullName: 'acme-prod.sales.transactions',
    engine: 'aws',
    totalColumns: 19,
    columns: [
      { name: 'product_id',   type: 'STRING'  },
      { name: 'product_name', type: 'STRING'  },
      { name: 'revenue',      type: 'FLOAT64' },
      { name: 'quarter',      type: 'STRING'  },
      { name: 'year',         type: 'INT64'   },
    ],
  },
  {
    id: 'acme-prod.products.catalog',
    fullName: 'acme-prod.products.catalog',
    engine: 'aws',
    totalColumns: 11,
    columns: [
      { name: 'product_id', type: 'STRING'  },
      { name: 'category',   type: 'STRING'  },
      { name: 'unit_cost',  type: 'FLOAT64' },
    ],
  },
];
