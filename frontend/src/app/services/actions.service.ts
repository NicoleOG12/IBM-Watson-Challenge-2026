import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { delay, of, Observable } from 'rxjs';
import { ActionType } from '../models/copilot.models';

// ─────────────────────────────────────────────────────────────
// ActionsService
//
// PARA ALTERNAR ENTRE MOCK E REAL:
//   → Mock  : bloco `of(MOCK_*).pipe(delay(ms))`  ← ATIVO
//   → Real  : descomente `this.http.post(...)` e comente o MOCK
// ─────────────────────────────────────────────────────────────

const API = '/api';

export interface ActionResult {
  triggered: boolean;
  externalId?: string;
  message: string;
}

@Injectable({ providedIn: 'root' })
export class ActionsService {
  // REAL → descomente:
  // private http = inject(HttpClient);

  // ── POST /api/actions/trigger ───────────────────────────
  // Corpo: { actionType: 'jira_ticket'|'send_email'|'create_record'; context: string }
  //   context = executionId da query que originou a ação
  // Resposta: ActionResult
  // --------------------------------------------------------
  trigger(actionType: ActionType, executionId: string): Observable<ActionResult> {
    // ── MOCK ────────────────────────────────────────────────
    return of({ triggered: true, externalId: 'JIRA-1234', message: 'Ação executada com sucesso (mock).' }).pipe(delay(600));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.post<ActionResult>(`${API}/actions/trigger`, {
    //   actionType,
    //   context: executionId,
    // });
  }
}
