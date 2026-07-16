import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { delay, of, Observable } from 'rxjs';
import { AuditEntry } from '../models/copilot.models';

// ─────────────────────────────────────────────────────────────
// AuditService
//
// PARA ALTERNAR ENTRE MOCK E REAL:
//   → Mock  : bloco `of(MOCK_*).pipe(delay(ms))`  ← ATIVO
//   → Real  : descomente `this.http.get(...)` e comente o MOCK
// ─────────────────────────────────────────────────────────────

const API = '/api';

@Injectable({ providedIn: 'root' })
export class AuditService {
  // REAL → descomente:
  // private http = inject(HttpClient);

  // ── GET /api/audit/session/:sessionId ───────────────────
  // Resposta: AuditEntry[] — log completo da sessão
  // --------------------------------------------------------
  getSession(sessionId: string): Observable<AuditEntry[]> {
    // ── MOCK ────────────────────────────────────────────────
    return of(MOCK_AUDIT).pipe(delay(300));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.get<AuditEntry[]>(`${API}/audit/session/${sessionId}`);
  }
}

// ─────────────────────────────────────────────────────────────
//  MOCK DATA
// ─────────────────────────────────────────────────────────────

const MOCK_AUDIT: AuditEntry[] = [
  { time: '09:15', action: 'Pergunta recebida', tag: 'NLU' },
  { time: '09:15', action: 'Catálogo consultado → 2 tabelas', tag: 'CATALOG' },
  { time: '09:15', action: 'SQL gerado (38 linhas)', tag: 'SQL' },
  { time: '09:15', action: 'Validação: sem operações destrutivas', tag: 'SAFE' },
  { time: '09:15', action: 'Custo estimado: $0.023 / 4.7 GB', tag: 'COST' },
  { time: '09:16', action: 'Execução aprovada pelo usuário', tag: 'EXEC' },
  { time: '09:16', action: 'Query concluída em 2.3s — 8 linhas', tag: 'RESULT' },
  { time: '09:16', action: 'Insights gerados pelo Bob (3)', tag: 'AI' },
];
