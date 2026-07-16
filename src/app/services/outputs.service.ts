import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { delay, of, Observable } from 'rxjs';
import { OutputType } from '../models/copilot.models';

// ─────────────────────────────────────────────────────────────
// OutputsService
//
// PARA ALTERNAR ENTRE MOCK E REAL:
//   → Mock  : bloco `of(MOCK_*).pipe(delay(ms))`  ← ATIVO
//   → Real  : descomente `this.http.*` e comente o bloco MOCK
// ─────────────────────────────────────────────────────────────

const API = '/api';

export interface GeneratedOutput {
  id: string;
  type: OutputType;
  url: string;
  createdAt: string;
}

@Injectable({ providedIn: 'root' })
export class OutputsService {
  // REAL → descomente:
  // private http = inject(HttpClient);

  // ── POST /api/outputs/generate ──────────────────────────
  // Corpo: { type: 'executive_summary'|'dashboard'|'logbook'; executionId: string }
  // Resposta: GeneratedOutput
  // --------------------------------------------------------
  generate(type: OutputType, executionId: string): Observable<GeneratedOutput> {
    // ── MOCK ────────────────────────────────────────────────
    return of({ id: 'out_001', type, url: '#', createdAt: new Date().toISOString() }).pipe(delay(800));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.post<GeneratedOutput>(`${API}/outputs/generate`, {
    //   type,
    //   executionId,
    // });
  }

  // ── GET /api/outputs?type=&userId= ──────────────────────
  // Resposta: GeneratedOutput[]
  // --------------------------------------------------------
  list(type: OutputType, userId: string): Observable<GeneratedOutput[]> {
    // ── MOCK ────────────────────────────────────────────────
    return of([]).pipe(delay(400));
    // ── REAL → descomente abaixo e comente o bloco MOCK ────
    // return this.http.get<GeneratedOutput[]>(`${API}/outputs`, {
    //   params: { type, userId },
    // });
  }
}
