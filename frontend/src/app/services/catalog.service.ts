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
    id: 'cliente_parquet',
    fullName: 'cliente_parquet',
    engine: 'aws',
    description: 'Cadastro completo de clientes com dados pessoais e de contato.',
    totalColumns: 13,
    columns: [
      { name: 'id_identificador', type: 'STRING' },
      { name: 'nm_nome',          type: 'STRING' },
      { name: 'ds_sobrenome',     type: 'STRING' },
      { name: 'nu_cpf',           type: 'STRING' },
      { name: 'dt_nascimento',    type: 'STRING' },
    ],
  },
  {
    id: 'loja_parquet',
    fullName: 'loja_parquet',
    engine: 'aws',
    description: 'Cadastro das filiais/lojas com localização e status de operação.',
    totalColumns: 9,
    columns: [
      { name: 'id_identificador', type: 'STRING'  },
      { name: 'nm_filial',        type: 'STRING'  },
      { name: 'nu_cnpj',          type: 'STRING'  },
      { name: 'ct_cidade',        type: 'STRING'  },
      { name: 'fl_status',        type: 'BOOLEAN' },
    ],
  },
  {
    id: 'produtos_parquet',
    fullName: 'produtos_parquet',
    engine: 'aws',
    description: 'Catálogo de produtos com preço, categoria e estoque disponível.',
    totalColumns: 6,
    columns: [
      { name: 'id_identificador',  type: 'STRING' },
      { name: 'nm_nome',           type: 'STRING' },
      { name: 'nm_categoria',      type: 'STRING' },
      { name: 'vl_preco_unitario', type: 'DOUBLE' },
      { name: 'qt_estoque',        type: 'BIGINT' },
    ],
  },
  {
    id: 'venda_parquet',
    fullName: 'venda_parquet',
    engine: 'aws',
    description: 'Registros de vendas realizadas, com dados desnormalizados de cliente, loja e produto.',
    totalColumns: 12,
    columns: [
      { name: 'id_venda',       type: 'STRING' },
      { name: 'id_loja',        type: 'STRING' },
      { name: 'id_cliente',     type: 'STRING' },
      { name: 'id_produto',     type: 'STRING' },
      { name: 'qt_quantidade',  type: 'BIGINT' },
    ],
  },
  {
    id: 'dataset_completo_parquet',
    fullName: 'dataset_completo_parquet',
    engine: 'aws',
    description: 'Visão consolidada com arrays de lojas, produtos, clientes e vendas em uma única linha.',
    totalColumns: 4,
    columns: [
      { name: 'lojas',    type: 'ARRAY<STRUCT>' },
      { name: 'produtos', type: 'ARRAY<STRUCT>' },
      { name: 'clientes', type: 'ARRAY<STRUCT>' },
      { name: 'vendas',   type: 'ARRAY<STRUCT>' },
    ],
  },
];
