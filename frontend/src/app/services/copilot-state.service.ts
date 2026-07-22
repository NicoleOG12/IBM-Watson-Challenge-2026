// ============================================================
// copilot-state.service.ts — Shared pipeline response cache
//
// Since the backend runs the full NL→SQL→Execute→Insights
// pipeline in a single POST /query call, this service caches
// the QueryResponse so each step of the frontend flow can
// read the data it needs without re-calling the backend.
// ============================================================
import { Injectable, signal } from '@angular/core';

export interface BackendQueryResponse {
  query_id:               string;
  user_id:                string;
  natural_language_query: string;
  status:                 string;
  timestamp:              string;
  cost_estimate?: {
    bytes_scanned:       number;
    estimated_cost_usd:  number;
    table_count:         number;
    has_filter:          boolean;
    is_mock:             boolean;
  };
  next_steps?: string[];
  matched_query?: unknown;
  result?: {
    sql:         string;
    explanation: string;
    error?:      string;
    data: {
      columns:        string[];
      rows:           Record<string, unknown>[];
      row_count:      number;
      execution_mode: string;
      metadata?: {
        execution_time_ms: number;
        bytes_processed:   number;
        engine:            string;
        row_count:         number;
      };
    };
    insights: {
      summary:      string;
      key_insights: Array<{ message: string; category: string }>;
      trends:       Array<{ message: string; category: string }>;
      anomalies:    Array<{ message: string; category: string }>;
    };
  };
}

@Injectable({ providedIn: 'root' })
export class CopilotStateService {
  /** Last successful pipeline response from the backend. */
  readonly lastResponse = signal<BackendQueryResponse | null>(null);

  set(response: BackendQueryResponse): void {
    this.lastResponse.set(response);
  }

  clear(): void {
    this.lastResponse.set(null);
  }
}
