import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { delay, map, of, Observable } from 'rxjs';
import { SavedQuestion } from '../models/copilot.models';

// ─────────────────────────────────────────────────────────────
// QuestionsService
//
// getSaved()    → GET /api/queries/saved?user_id=
// getSuggested()→ stays mock (no backend endpoint yet)
// getSimilar()  → GET /api/queries/match?q=&user_id=
// save()        → POST /api/queries/save
// ─────────────────────────────────────────────────────────────

const API = '/api';
const DEMO_USER = 'alex.rodrigues@acme.com';

// Backend SavedQuery shape → frontend SavedQuestion shape
interface BackendSavedQuery {
  id:          string;
  user_id:     string;
  question:    string;
  sql:         string;
  tables_used: string[];
  tags:        string[];
  description: string | null;
  auto_saved:  boolean;
}

function toSavedQuestion(b: BackendSavedQuery): SavedQuestion {
  return {
    id:        b.id,
    question:  b.question,
    sql:       b.sql,
    tags:      b.tags,
    intent:    b.description ?? '',
    validated: true,
  };
}

@Injectable({ providedIn: 'root' })
export class QuestionsService {
  private http = inject(HttpClient);

  // ── GET /api/queries/saved?user_id= ─────────────────────
  getSaved(userId: string = DEMO_USER): Observable<SavedQuestion[]> {
    return this.http.get<BackendSavedQuery[]>(`${API}/queries/saved`, {
      params: { user_id: userId },
    }).pipe(map(list => list.map(toSavedQuestion)));
    // ── MOCK (fallback) ─────────────────────────────────────
    // return of(MOCK_SAVED).pipe(delay(400));
  }

  // ── stays mock — no backend endpoint yet ─────────────────
  getSuggested(userId: string): Observable<string[]> {
    return of(MOCK_SUGGESTED).pipe(delay(300));
  }

  // ── GET /api/queries/match?q=&user_id= ───────────────────
  // Returns matching saved queries by keyword overlap
  getSimilar(intent: string): Observable<SavedQuestion[]> {
    return this.http.get<BackendSavedQuery[]>(`${API}/queries/match`, {
      params: { q: intent, user_id: DEMO_USER },
    }).pipe(map(list => list.map(toSavedQuestion)));
    // ── MOCK (fallback) ─────────────────────────────────────
    // return of(MOCK_SAVED).pipe(delay(400));
  }

  // ── POST /api/queries/save ───────────────────────────────
  save(payload: Partial<SavedQuestion>): Observable<SavedQuestion> {
    return this.http.post<BackendSavedQuery>(`${API}/queries/save`, {
      user_id:     DEMO_USER,
      question:    payload.question ?? '',
      sql:         payload.sql ?? '',
      tags:        payload.tags ?? [],
      description: payload.intent ?? null,
    }).pipe(map(toSavedQuestion));
    // ── MOCK (fallback) ─────────────────────────────────────
    // return of({ ...MOCK_SAVED[0], ...payload } as SavedQuestion).pipe(delay(300));
  }
}

// ─────────────────────────────────────────────────────────────
//  MOCK DATA — kept as reference / fallback
// ─────────────────────────────────────────────────────────────

const MOCK_SAVED: SavedQuestion[] = [
  {
    id:        'q1',
    question:  'Sales variation by product',
    sql:       'SELECT product_name, ...',
    tags:      ['Sales Analytics'],
    intent:    'sales_drop',
    validated: true,
  },
];

const MOCK_SUGGESTED: string[] = [
  'Top 10 customers by revenue',
  'Average ticket by channel',
  'Churn rate this month',
  'Critical stock levels',
  'Current delinquency rate',
];
