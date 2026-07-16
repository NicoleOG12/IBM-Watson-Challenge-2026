// ============================================================
// right-panel.component.ts
// Tabs: Catálogo | Histórico | Auditoria
// ============================================================
import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CatalogService } from '../../services/catalog.service';
import { QueryService } from '../../services/query.service';
import { AuditService } from '../../services/audit.service';
import { QuestionsService } from '../../services/questions.service';
import type { CatalogTable, HistoryEntry, AuditEntry, SavedQuestion } from '../../models/copilot.models';

type PanelTab = 'catalog' | 'history' | 'audit';

@Component({
  selector: 'app-right-panel',
  standalone: true,
  imports: [CommonModule],
  template: `
    <aside class="panel">
      <!-- ── Tab bar ── -->
      <div class="tab-row">
        <!-- Tab Catálogo: GET /api/catalog/resolve?intent= + GET /api/catalog/tables/:id -->
        <button class="tab" [class.active]="activeTab === 'catalog'" (click)="activeTab = 'catalog'">Catálogo</button>
        <!-- Tab Histórico: GET /api/queries/history?userId=&limit=50 -->
        <button class="tab" [class.active]="activeTab === 'history'" (click)="setTab('history')">Histórico</button>
        <!-- Tab Auditoria: GET /api/audit/session/:sessionId -->
        <button class="tab" [class.active]="activeTab === 'audit'"   (click)="setTab('audit')">Auditoria</button>
      </div>

      <!-- ═══════════════════════════════════════════════
           CATÁLOGO
           GET /api/catalog/resolve?intent=
           GET /api/catalog/tables/:tableId
      ═══════════════════════════════════════════════ -->
      <div class="tab-content" *ngIf="activeTab === 'catalog'">
        <div class="panel-section-title">Tabelas identificadas</div>

        <div class="cat-table" *ngFor="let t of tables">
          <div class="ct-header">
            <span class="ct-name" [title]="t.fullName">{{ t.fullName }}</span>
            <span class="ct-engine">{{ t.engine }}</span>
          </div>
          <div class="ct-row" *ngFor="let col of t.columns">
            <span class="ct-col">{{ col.name }}</span>
            <span class="ct-type">{{ col.type }}</span>
          </div>
          <div class="ct-more" *ngIf="t.totalColumns > t.columns.length">
            + {{ t.totalColumns - t.columns.length }} colunas…
          </div>
        </div>

        <div class="panel-section-title">Pergunta similar salva</div>
        <!-- GET /api/questions/saved?similar=true&intent=sales_drop -->
        <div class="saved-q" *ngFor="let q of savedQuestions">
          <div class="sq-title">{{ q.question }}</div>
          <div class="sq-desc">SQL validado · contexto: análise de queda/crescimento por SKU</div>
          <div class="sq-tags">
            <span class="tag tag-green" *ngIf="q.validated">✓ SQL validado</span>
            <span class="tag tag-blue" *ngFor="let tag of q.tags">{{ tag }}</span>
          </div>
        </div>
      </div>

      <!-- ═══════════════════════════════════════════════
           HISTÓRICO
           GET /api/queries/history?userId=&limit=50
      ═══════════════════════════════════════════════ -->
      <div class="tab-content" *ngIf="activeTab === 'history'">
        <div class="panel-section-title">Últimas consultas</div>
        <div class="history-item" *ngFor="let h of history">
          <div class="hi-q">{{ h.question }}</div>
          <div class="hi-meta">
            <span class="hi-db">{{ h.engine }}</span>
            <span>{{ h.rowCount }} linhas</span>
            <span>{{ h.durationMs }}ms</span>
            <span>{{ h.timestamp }}</span>
          </div>
        </div>
        <div class="empty-state" *ngIf="history.length === 0">Nenhum histórico ainda.</div>
      </div>

      <!-- ═══════════════════════════════════════════════
           AUDITORIA
           GET /api/audit/session/:sessionId
      ═══════════════════════════════════════════════ -->
      <div class="tab-content" *ngIf="activeTab === 'audit'">
        <div class="panel-section-title">Log da sessão</div>
        <div class="audit-entry" *ngFor="let a of auditLog">
          <span class="ae-time">{{ a.time }}</span>
          <span class="ae-action">{{ a.action }}</span>
          <span class="ae-tag" *ngIf="a.tag">{{ a.tag }}</span>
        </div>
        <div class="empty-state" *ngIf="auditLog.length === 0">Sem entradas de auditoria.</div>
      </div>
    </aside>
  `,
  styles: [`
    .panel {
      width: 280px;
      background: #fff;
      border-left: 1px solid #e5e7eb;
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
      overflow-y: auto;
      height: 100%;
    }
    .tab-row {
      display: flex;
      border-bottom: 1px solid #e5e7eb;
      flex-shrink: 0;
    }
    .tab {
      flex: 1; padding: 10px 4px;
      font-size: 11px; color: #57606a;
      border: none; background: transparent;
      cursor: pointer; font-family: inherit;
      border-bottom: 2px solid transparent;
      text-align: center; transition: color 0.15s;
    }
    .tab.active { color: #3b82d4; border-bottom-color: #3b82d4; font-weight: 600; }
    .tab-content { padding: 12px; flex: 1; }

    /* catalog */
    .cat-table {
      border: 1px solid #e5e7eb; border-radius: 6px;
      overflow: hidden; margin-bottom: 8px;
    }
    .ct-header {
      background: #f7f8fa; padding: 6px 10px;
      font-size: 11px; font-weight: 600; color: #1f2328;
      border-bottom: 1px solid #e5e7eb;
      display: flex; justify-content: space-between; align-items: center;
    }
    .ct-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 170px; }
    .ct-engine {
      font-size: 9px; background: #eff4ff;
      color: #3b82d4; padding: 1px 5px; border-radius: 3px;
    }
    .ct-row {
      padding: 5px 10px; font-size: 11px;
      border-bottom: 1px solid #f0f2f5;
      display: flex; gap: 6px; align-items: center;
    }
    .ct-row:last-of-type { border-bottom: none; }
    .ct-col { color: #57606a; flex: 1; }
    .ct-type {
      font-size: 9px; color: #7c5cd8;
      background: #f5f0ff; padding: 1px 4px; border-radius: 3px;
    }
    .ct-more {
      padding: 5px 10px; font-size: 10px;
      color: #3b82d4; cursor: pointer;
      border-top: 1px solid #f0f2f5;
    }

    /* saved question */
    .saved-q {
      font-size: 11px; background: #f7f8fa;
      border: 1px solid #e5e7eb; border-radius: 6px;
      padding: 8px 10px; color: #57606a;
    }
    .sq-title { font-weight: 600; color: #1f2328; margin-bottom: 3px; }
    .sq-desc  { margin-bottom: 6px; }
    .sq-tags  { display: flex; gap: 5px; flex-wrap: wrap; }
    .tag { font-size: 9px; padding: 1px 5px; border-radius: 3px; font-weight: 600; }
    .tag-green  { background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; }
    .tag-blue   { background: #eff4ff; border: 1px solid #bfdbfe; color: #1d4ed8; }

    /* history */
    .history-item {
      padding: 8px 0; border-bottom: 1px solid #f0f2f5;
      cursor: pointer; font-size: 12px;
    }
    .history-item:last-child { border-bottom: none; }
    .hi-q { color: #1f2328; font-weight: 500; margin-bottom: 2px; }
    .hi-meta {
      font-size: 10px; color: #57606a;
      display: flex; gap: 8px;
    }
    .hi-db { color: #3b82d4; }

    /* audit */
    .audit-entry {
      font-size: 10px; color: #57606a;
      padding: 5px 0; border-bottom: 1px solid #f0f2f5;
      display: flex; gap: 6px; align-items: flex-start; flex-wrap: wrap;
    }
    .ae-time { flex-shrink: 0; width: 42px; }
    .ae-action { color: #1f2328; flex: 1; }
    .ae-tag {
      font-size: 9px; background: #f7f8fa;
      border: 1px solid #e5e7eb; border-radius: 3px;
      padding: 0 4px; color: #57606a; flex-shrink: 0;
    }

    .empty-state { font-size: 12px; color: #57606a; padding: 8px 0; }
  `],
})
export class RightPanelComponent implements OnInit {
  private catalogSvc    = inject(CatalogService);
  private querySvc      = inject(QueryService);
  private auditSvc      = inject(AuditService);
  private questionsSvc  = inject(QuestionsService);

  activeTab: PanelTab = 'catalog';

  tables:        CatalogTable[]  = [];
  history:       HistoryEntry[]  = [];
  auditLog:      AuditEntry[]    = [];
  savedQuestions: SavedQuestion[] = [];

  ngOnInit(): void {
    // ── Catálogo: GET /api/catalog/resolve?intent=sales_drop ────
    this.catalogSvc.resolveByIntent('sales_drop').subscribe(t => this.tables = t);

    // ── Perguntas similares: GET /api/questions/saved?similar=true ──
    this.questionsSvc.getSimilar('sales_drop').subscribe(q => this.savedQuestions = q);
  }

  setTab(tab: PanelTab): void {
    this.activeTab = tab;
    if (tab === 'history' && this.history.length === 0) {
      // GET /api/queries/history?userId=alex.rodrigues@acme.com&limit=50
      this.querySvc.getHistory('alex.rodrigues@acme.com').subscribe(h => this.history = h);
    }
    if (tab === 'audit' && this.auditLog.length === 0) {
      // GET /api/audit/session/:sessionId
      this.auditSvc.getSession('sess_9f3a').subscribe(a => this.auditLog = a);
    }
  }
}
