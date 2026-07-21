import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { delay, map, of, Observable } from 'rxjs';
import { AuditEntry } from '../models/copilot.models';

// ─────────────────────────────────────────────────────────────
// AuditService
//
// getSession() → GET /api/audit?user_id=&limit=
//   Maps backend AuditLog[] to frontend AuditEntry[] shape.
// ─────────────────────────────────────────────────────────────

const API = '/api';
const DEMO_USER = 'alex.rodrigues@acme.com';

interface BackendAuditLog {
  log_id:                 string;
  timestamp:              string;
  user_id:                string;
  natural_language_query: string;
  generated_sql:          string;
  status:                 string;
  execution_time_ms:      number;
  row_count:              number;
  error:                  string | null;
}

function toAuditEntry(log: BackendAuditLog): AuditEntry {
  const time = new Date(log.timestamp).toLocaleTimeString('pt-BR', {
    hour: '2-digit', minute: '2-digit',
  });
  return {
    time,
    action: log.status === 'success'
      ? `Query executada — ${log.row_count} linhas em ${log.execution_time_ms.toFixed(0)}ms`
      : `Query rejeitada: ${log.error ?? 'erro desconhecido'}`,
    tag: log.status === 'success' ? 'RESULT' : 'REJECT',
  };
}

@Injectable({ providedIn: 'root' })
export class AuditService {
  private http = inject(HttpClient);

  // ── GET /api/audit?user_id=&limit= ──────────────────────
  getSession(userId: string = DEMO_USER, limit = 20): Observable<AuditEntry[]> {
    return this.http.get<BackendAuditLog[]>(`${API}/audit`, {
      params: { user_id: userId, limit: String(limit) },
    }).pipe(map(logs => logs.map(toAuditEntry)));
    // ── MOCK (fallback) ─────────────────────────────────────
    // return of(MOCK_AUDIT).pipe(delay(300));
  }
}

// ─────────────────────────────────────────────────────────────
//  MOCK DATA — kept as reference / fallback
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
