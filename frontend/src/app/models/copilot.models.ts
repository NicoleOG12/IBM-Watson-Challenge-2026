// ============================================================
// copilot.models.ts — Interfaces compartilhadas da aplicação
// ============================================================

export type DbEngine = 'bigquery' | 'redshift';
export type StepStatus = 'pending' | 'active' | 'done' | 'warn' | 'error';
export type OutputType = 'executive_summary' | 'dashboard' | 'logbook';
export type ActionType = 'jira_ticket' | 'send_email' | 'create_record';

export interface PipelineStep {
  label: string;
  status: StepStatus;
  endpoint?: string; // endpoint que dispara ou produz este passo
}

export interface CostEstimate {
  bytesScanned: string;
  estimatedCost: string;
  table: string;
  engine: DbEngine;
}

export interface SqlValidation {
  safe: boolean;
  warnings: string[]; // ex: ['contains DELETE']
}

export interface SqlPreview {
  sql: string;
  validation: SqlValidation;
  cost: CostEstimate;
  table: string;
  generatedAt: string;
  sessionId: string;
  /** Plain-language summary of what the generated SQL does (no chain-of-thought). */
  explanation?: string;
}

export interface QueryResult {
  executionId: string;
  rowCount: number;
  durationMs: number;
  columns: string[];
  rows: Record<string, unknown>[];
  hasMore: boolean;
}

export interface Insight {
  type: 'positive' | 'warning' | 'info';
  icon: string;
  text: string;
}

export interface CatalogColumn {
  name: string;
  type: string;
}

export interface CatalogTable {
  id: string;
  fullName: string;
  engine: DbEngine;
  columns: CatalogColumn[];
  totalColumns: number;
}

export interface SavedQuestion {
  id: string;
  question: string;
  sql: string;
  tags: string[];
  intent: string;
  validated: boolean;
}

export interface HistoryEntry {
  executionId: string;
  question: string;
  engine: DbEngine;
  rowCount: number;
  durationMs: number;
  timestamp: string;
}

export interface AuditEntry {
  time: string;
  action: string;
  tag?: string;
}

export type MessageRole = 'user' | 'bob';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  time: string;
  // tipos de conteúdo possíveis num balão
  text?: string;
  steps?: PipelineStep[];
  sqlPreview?: SqlPreview;
  results?: QueryResult;
  insights?: Insight[];
  showOutputSelector?: boolean;
  nextSteps?: string[];
}
