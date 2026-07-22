// ============================================================
// right-panel.component.ts — Neon Dark v4
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

      <!-- ── Panel header ── -->
      <div class="panel-header">
        <div class="panel-title">
          <div class="panel-title-icon">
            <svg viewBox="0 0 16 16" fill="currentColor" width="12" height="12">
              <path d="M8 1a7 7 0 100 14A7 7 0 008 1zm.5 4v4.25l3 1.75-.5.87-3.5-2.03V5h1z"/>
            </svg>
          </div>
          Context
        </div>
        <div class="panel-header-right">
          <div class="panel-status-dot"></div>
          <span class="panel-status-label">live</span>
        </div>
      </div>

      <!-- ── Tabs ── -->
      <div class="tab-row">
        <button class="tab" [class.active]="activeTab === 'catalog'" (click)="activeTab = 'catalog'">
          <svg viewBox="0 0 16 16" fill="currentColor" width="10" height="10"><path d="M1 3h14v2H1zm0 4h14v2H1zm0 4h14v2H1z"/></svg>
          Catalog
        </button>
        <button class="tab" [class.active]="activeTab === 'history'" (click)="setTab('history')">
          <svg viewBox="0 0 16 16" fill="currentColor" width="10" height="10"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm.5 4v4.25l3 1.75-.5.87-3.5-2.03V5h1z"/></svg>
          History
        </button>
        <button class="tab" [class.active]="activeTab === 'audit'" (click)="setTab('audit')">
          <svg viewBox="0 0 16 16" fill="currentColor" width="10" height="10"><path d="M2 1h9l3 3v11H2V1zm5 5H4v1h3zm6 0H8v1h5zm-6 3H4v1h3zm6 0H8v1h5z"/></svg>
          Audit
        </button>
        <div class="tab-slider" [style.left]="tabSliderLeft"></div>
      </div>

      <!-- ══ CATALOG ══ -->
      <div class="tab-content" *ngIf="activeTab === 'catalog'">
        <div class="section-header">
          <span class="section-label">Identified tables</span>
          <span class="section-count">{{ tables.length }}</span>
        </div>

        <div class="cat-table" *ngFor="let t of tables">
          <div class="ct-header">
            <div class="ct-header-left">
              <div class="ct-engine-dot"></div>
              <span class="ct-name" [title]="t.fullName">{{ t.fullName }}</span>
            </div>
            <span class="ct-engine">{{ t.engine }}</span>
          </div>
          <div class="ct-description" *ngIf="t.description">{{ t.description }}</div>
          <div class="ct-row" *ngFor="let col of t.columns">
            <span class="ct-col">{{ col.name }}</span>
            <span class="ct-type">{{ col.type }}</span>
          </div>
          <div class="ct-more" *ngIf="t.totalColumns > t.columns.length">
            <svg viewBox="0 0 16 16" fill="currentColor" width="9" height="9"><path d="M8 1v14M1 8h14"/></svg>
            {{ t.totalColumns - t.columns.length }} more columns
          </div>
        </div>

        <div class="section-header" style="margin-top:14px;">
          <span class="section-label">Similar question</span>
        </div>
        <div class="saved-q" *ngFor="let q of savedQuestions">
          <div class="sq-title">{{ q.question }}</div>
          <div class="sq-meta">Validated SQL · drop/growth analysis by SKU</div>
          <div class="sq-tags">
            <span class="stag green" *ngIf="q.validated">✓ Validated</span>
            <span class="stag blue" *ngFor="let tag of q.tags">{{ tag }}</span>
          </div>
        </div>
      </div>

      <!-- ══ HISTORY ══ -->
      <div class="tab-content" *ngIf="activeTab === 'history'">
        <div class="section-header">
          <span class="section-label">Recent queries</span>
          <span class="section-count">{{ history.length }}</span>
        </div>
        <div class="history-item" *ngFor="let h of history; let i = index">
          <div class="hi-number">{{ i + 1 }}</div>
          <div class="hi-body">
            <div class="hi-q">{{ h.question }}</div>
            <div class="hi-meta">
              <span class="hi-db">{{ h.engine }}</span>
              <span class="hi-stat">{{ h.rowCount }} rows</span>
              <span class="hi-stat">{{ h.durationMs }}ms</span>
            </div>
          </div>
          <div class="hi-time">{{ h.timestamp }}</div>
        </div>
        <div class="empty-state" *ngIf="history.length === 0">
          <div class="empty-icon">⏱</div>
          <div>No history yet.</div>
        </div>
      </div>

      <!-- ══ AUDIT ══ -->
      <div class="tab-content" *ngIf="activeTab === 'audit'">
        <div class="section-header">
          <span class="section-label">Session log</span>
          <span class="section-count audit-live">● LIVE</span>
        </div>
        <div class="audit-entry" *ngFor="let a of auditLog">
          <div class="ae-timeline">
            <div class="ae-dot"></div>
            <div class="ae-line"></div>
          </div>
          <div class="ae-body">
            <div class="ae-time">{{ a.time }}</div>
            <div class="ae-action">{{ a.action }}</div>
            <span class="ae-tag" *ngIf="a.tag">{{ a.tag }}</span>
          </div>
        </div>
        <div class="empty-state" *ngIf="auditLog.length === 0">
          <div class="empty-icon">📋</div>
          <div>No audit entries.</div>
        </div>
      </div>
    </aside>
  `,
  styles: [`
    /* ── Panel container ── */
    .panel {
      width: 284px;
      background: #0d1018;
      border-left: 1px solid rgba(79,158,255,0.1);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
      overflow-y: auto;
      height: 100%;
      position: relative;
      transition: background 0.28s, border-color 0.28s;
    }
    :host-context([data-theme="light"]) .panel {
      background: #f0f2f7;
      border-left-color: rgba(0,0,0,0.12);
    }

    /* Linha de acento lateral multicolor */
    .panel::before {
      content: '';
      position: absolute;
      top: 0; right: 0;
      width: 1px;
      height: 100%;
      background: linear-gradient(180deg,
        #4f9eff 0%,
        #b87dff 33%,
        #00e5ff 66%,
        #00e676 100%);
      opacity: 0.15;
    }

    /* ── Panel header ── */
    .panel-header {
      padding: 14px 14px 10px;
      border-bottom: 1px solid rgba(79,158,255,0.08);
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
      background: rgba(79,158,255,0.03);
      transition: background 0.28s, border-color 0.28s;
    }
    :host-context([data-theme="light"]) .panel-header {
      border-bottom-color: rgba(0,0,0,0.12);
      background: #e4e8f2;
    }

    .panel-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 11.5px;
      font-weight: 700;
      color: rgba(240,244,255,0.45);
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    :host-context([data-theme="light"]) .panel-title { color: #374151; }

    .panel-title-icon {
      width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 6px;
      background: rgba(79,158,255,0.1);
      border: 1px solid rgba(79,158,255,0.22);
      color: #4f9eff;
      transition: background 0.2s;
    }
    .panel-title-icon:hover { background: rgba(79,158,255,0.18); }

    .panel-header-right {
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .panel-status-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #00e676;
      box-shadow: 0 0 7px #00e676;
      animation: livePulse 1.6s infinite;
    }
    @keyframes livePulse {
      0%,100% { opacity: 1; transform: scale(1); }
      50%      { opacity: 0.3; transform: scale(0.8); }
    }
    .panel-status-label {
      font-size: 9px;
      font-weight: 700;
      color: #00e676;
      text-transform: uppercase;
      letter-spacing: 0.8px;
    }

    /* ── Tabs ── */
    .tab-row {
      display: flex;
      border-bottom: 1px solid rgba(79,158,255,0.08);
      flex-shrink: 0;
      background: rgba(0,0,0,0.25);
      position: relative;
    }

    .tab {
      flex: 1;
      padding: 10px 4px;
      font-size: 10px;
      color: rgba(240,244,255,0.25);
      border: none;
      background: transparent;
      cursor: pointer;
      font-family: inherit;
      text-align: center;
      transition: color 0.2s;
      font-weight: 600;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 5px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      position: relative;
    }
    .tab::after {
      content: '';
      position: absolute;
      bottom: 0; left: 50%; right: 50%;
      height: 2px;
      border-radius: 2px 2px 0 0;
      transition: left 0.2s ease, right 0.2s ease;
    }
    .tab:hover { color: rgba(240,244,255,0.55); }
    .tab.active { color: #4f9eff; }
    .tab.active::after {
      left: 10%; right: 10%;
      background: linear-gradient(90deg, #4f9eff, #b87dff);
      box-shadow: 0 0 8px rgba(79,158,255,0.5);
    }
    :host-context([data-theme="light"]) .tab.active::after {
      background: linear-gradient(90deg, #1d4ed8, #6d28d9);
      box-shadow: none;
    }

    /* Slider indicator */
    .tab-slider {
      position: absolute;
      bottom: 0;
      width: 33.333%;
      height: 2px;
      background: linear-gradient(90deg, #4f9eff, #b87dff);
      border-radius: 2px 2px 0 0;
      box-shadow: 0 0 8px rgba(79,158,255,0.6);
      transition: left 0.25s cubic-bezier(0.4,0,0.2,1);
    }
    :host-context([data-theme="light"]) .tab-slider {
      background: linear-gradient(90deg, #1d4ed8, #6d28d9);
      box-shadow: none;
    }

    .tab-content { padding: 12px; flex: 1; }

    /* ── Section header ── */
    .section-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
      margin-top: 4px;
    }
    .section-label {
      font-size: 9px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1.2px;
      color: rgba(240,244,255,0.2);
    }
    .section-count {
      font-size: 9px;
      font-weight: 700;
      color: #4f9eff;
      background: rgba(79,158,255,0.08);
      border: 1px solid rgba(79,158,255,0.18);
      border-radius: 999px;
      padding: 1px 8px;
    }
    :host-context([data-theme="light"]) .section-count {
      color: #2563eb;
      background: rgba(37,99,235,0.10);
      border-color: rgba(37,99,235,0.28);
    }
    .audit-live {
      color: #00e676 !important;
      background: rgba(0,230,118,0.07) !important;
      border-color: rgba(0,230,118,0.18) !important;
      animation: livePulse 1.6s infinite;
    }

    /* ── Catalog table ── */
    .cat-table {
      border: 1px solid rgba(79,158,255,0.1);
      border-radius: 10px;
      overflow: hidden;
      margin-bottom: 8px;
      transition: border-color 0.2s, box-shadow 0.2s;
      background: rgba(255,255,255,0.012);
    }
    .cat-table:hover {
      border-color: rgba(79,158,255,0.22);
      box-shadow: 0 0 12px rgba(79,158,255,0.06);
    }

    .ct-header {
      background: rgba(79,158,255,0.05);
      padding: 7px 10px;
      border-bottom: 1px solid rgba(79,158,255,0.08);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 6px;
    }
    .ct-header-left { display: flex; align-items: center; gap: 6px; min-width: 0; }
    .ct-engine-dot {
      width: 6px; height: 6px;
      border-radius: 50%;
      background: #00e5ff;
      box-shadow: 0 0 6px rgba(0,229,255,0.6);
      flex-shrink: 0;
      animation: livePulse 2.5s infinite;
    }
    :host-context([data-theme="light"]) .ct-engine-dot {
      background: #0891b2;
      box-shadow: none;
    }
    .ct-name {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-family: "JetBrains Mono", monospace;
      font-size: 10px;
      color: rgba(240,244,255,0.7);
      font-weight: 600;
    }
    .ct-engine {
      font-size: 8px;
      background: rgba(0,229,255,0.08);
      color: #00e5ff;
      padding: 2px 6px;
      border-radius: 4px;
      border: 1px solid rgba(0,229,255,0.2);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.4px;
      flex-shrink: 0;
    }
    .ct-row {
      padding: 5px 10px;
      border-bottom: 1px solid rgba(255,255,255,0.025);
      display: flex;
      gap: 6px;
      align-items: center;
      transition: background 0.15s;
    }
    .ct-row:hover { background: rgba(79,158,255,0.04); }
    .ct-row:last-of-type { border-bottom: none; }
    .ct-col {
      color: rgba(240,244,255,0.6);
      flex: 1;
      font-family: "JetBrains Mono", monospace;
      font-size: 10px;
    }
    .ct-type {
      font-size: 9px;
      color: #b87dff;
      background: rgba(184,125,255,0.08);
      padding: 1px 5px;
      border-radius: 4px;
      border: 1px solid rgba(184,125,255,0.18);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.3px;
    }
    :host-context([data-theme="light"]) .ct-type {
      color: #7c3aed;
      background: rgba(124,58,237,0.10);
      border-color: rgba(124,58,237,0.28);
    }
    .ct-more {
      padding: 5px 10px;
      font-size: 10px;
      color: rgba(79,158,255,0.55);
      cursor: pointer;
      border-top: 1px solid rgba(255,255,255,0.025);
      transition: background 0.15s, color 0.15s;
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .ct-more:hover { background: rgba(79,158,255,0.05); color: #4f9eff; }
    .ct-description {
      padding: 4px 10px 6px;
      font-size: 10px;
      color: rgba(240,244,255,0.38);
      line-height: 1.4;
      border-bottom: 1px solid rgba(255,255,255,0.04);
    }
    :host-context([data-theme="light"]) .ct-description {
      color: rgba(20,30,50,0.45);
    }

    /* ── Saved question ── */
    .saved-q {
      font-size: 11px;
      background: rgba(255,255,255,0.012);
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 10px;
      padding: 10px 12px;
      transition: all 0.2s;
      cursor: pointer;
      margin-bottom: 6px;
    }
    .saved-q:hover {
      border-color: rgba(79,158,255,0.2);
      background: rgba(79,158,255,0.03);
      transform: translateX(2px);
    }
    .sq-title {
      font-weight: 700;
      color: rgba(240,244,255,0.65);
      margin-bottom: 4px;
      font-size: 11.5px;
      line-height: 1.4;
    }
    .sq-meta {
      margin-bottom: 8px;
      font-size: 10px;
      color: rgba(240,244,255,0.45);
    }
    .sq-tags { display: flex; gap: 5px; flex-wrap: wrap; }

    .stag {
      font-size: 9px;
      padding: 2px 7px;
      border-radius: 4px;
      font-weight: 700;
      letter-spacing: 0.3px;
    }
    .stag.green { background: rgba(0,230,118,0.08); border: 1px solid rgba(0,230,118,0.2); color: #00e676; }
    .stag.blue  { background: rgba(79,158,255,0.08); border: 1px solid rgba(79,158,255,0.2); color: #4f9eff; }

    /* ── History ── */
    .history-item {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      padding: 8px 0;
      border-bottom: 1px solid rgba(255,255,255,0.03);
      cursor: pointer;
      transition: padding-left 0.2s, background 0.15s;
      border-radius: 6px;
    }
    .history-item:last-child { border-bottom: none; }
    .history-item:hover {
      padding-left: 5px;
      background: rgba(79,158,255,0.03);
    }

    .hi-number {
      width: 20px;
      height: 20px;
      border-radius: 6px;
      background: rgba(79,158,255,0.08);
      border: 1px solid rgba(79,158,255,0.16);
      color: #4f9eff;
      font-size: 9px;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      margin-top: 2px;
      font-family: "JetBrains Mono", monospace;
    }
    .hi-body { flex: 1; min-width: 0; }
    .hi-q {
      color: rgba(240,244,255,0.65);
      font-weight: 600;
      margin-bottom: 4px;
      font-size: 11.5px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .hi-meta {
      display: flex;
      gap: 7px;
      font-size: 10px;
      font-family: "JetBrains Mono", monospace;
    }
    .hi-db   { color: #00e5ff; }
    :host-context([data-theme="light"]) .hi-db { color: #0369a1; }
    .hi-stat { color: rgba(240,244,255,0.2); }
    .hi-time {
      font-size: 9px;
      color: rgba(240,244,255,0.12);
      font-family: "JetBrains Mono", monospace;
      white-space: nowrap;
      margin-top: 2px;
    }

    /* ── Audit ── */
    .audit-entry {
      display: flex;
      gap: 8px;
      padding: 6px 0;
    }
    .ae-timeline {
      display: flex;
      flex-direction: column;
      align-items: center;
      flex-shrink: 0;
      padding-top: 4px;
    }
    .ae-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #b87dff;
      border: 1px solid rgba(184,125,255,0.4);
      box-shadow: 0 0 6px rgba(184,125,255,0.4);
      flex-shrink: 0;
    }
    :host-context([data-theme="light"]) .ae-dot {
      background: #7c3aed;
      border-color: rgba(124,58,237,0.4);
      box-shadow: none;
    }
    .ae-line {
      flex: 1;
      width: 1px;
      background: linear-gradient(180deg, rgba(184,125,255,0.15), transparent);
      min-height: 12px;
    }
    .ae-body { flex: 1; min-width: 0; padding-bottom: 8px; }
    .ae-time {
      font-size: 9px;
      color: rgba(184,125,255,0.55);
      font-family: "JetBrains Mono", monospace;
      margin-bottom: 2px;
    }
    .ae-action {
      font-size: 11px;
      color: rgba(240,244,255,0.65);
      line-height: 1.4;
    }
    .ae-tag {
      display: inline-flex;
      margin-top: 4px;
      font-size: 9px;
      background: rgba(184,125,255,0.07);
      border: 1px solid rgba(184,125,255,0.15);
      border-radius: 4px;
      padding: 1px 6px;
      color: #b87dff;
    }

    /* ── Empty state ── */
    .empty-state {
      text-align: center;
      padding: 28px 0;
      color: rgba(240,244,255,0.12);
      font-size: 12px;
    }
    .empty-icon {
      font-size: 26px;
      margin-bottom: 10px;
      opacity: 0.25;
    }

    /* ════════════════════════════
       LIGHT MODE — right-panel
    ════════════════════════════ */
    :host-context([data-theme="light"]) .tab-row {
      background: #e4e8f2;
      border-bottom-color: rgba(0,0,0,0.12);
    }
    :host-context([data-theme="light"]) .tab { color: #374151; }
    :host-context([data-theme="light"]) .tab:hover { color: #111827; }
    :host-context([data-theme="light"]) .tab.active { color: #1246b0; }

    :host-context([data-theme="light"]) .section-label { color: #374151; }
    :host-context([data-theme="light"]) .section-count {
      color: #1246b0;
      background: rgba(18,70,176,0.12);
      border-color: rgba(18,70,176,0.30);
    }
    :host-context([data-theme="light"]) .audit-live {
      color: #16a34a !important;
      background: rgba(6,95,70,0.12) !important;
      border-color: rgba(6,95,70,0.30) !important;
    }

    /* Catalog tables */
    :host-context([data-theme="light"]) .cat-table {
      background: #ffffff;
      border-color: rgba(0,0,0,0.16);
      box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    :host-context([data-theme="light"]) .cat-table:hover {
      border-color: rgba(18,70,176,0.32);
      box-shadow: 0 2px 10px rgba(18,70,176,0.12);
    }
    :host-context([data-theme="light"]) .ct-header {
      background: #e4e8f2;
      border-bottom-color: rgba(0,0,0,0.12);
    }
    :host-context([data-theme="light"]) .ct-name { color: #111827; }
    :host-context([data-theme="light"]) .ct-engine {
      color: #075985;
      background: rgba(7,89,133,0.12);
      border-color: rgba(7,89,133,0.30);
    }
    :host-context([data-theme="light"]) .ct-row { border-bottom-color: rgba(0,0,0,0.05); }
    :host-context([data-theme="light"]) .ct-row:hover { background: rgba(18,70,176,0.07); }
    :host-context([data-theme="light"]) .ct-col { color: #374151; }
    :host-context([data-theme="light"]) .ct-type {
      color: #5b21b6;
      background: rgba(91,33,182,0.12);
      border-color: rgba(91,33,182,0.30);
    }
    :host-context([data-theme="light"]) .ct-more {
      color: #1246b0;
      border-top-color: rgba(0,0,0,0.06);
    }
    :host-context([data-theme="light"]) .ct-more:hover {
      background: rgba(18,70,176,0.07);
      color: #1246b0;
    }

    /* Saved questions */
    :host-context([data-theme="light"]) .saved-q {
      background: #ffffff;
      border-color: rgba(0,0,0,0.09);
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    :host-context([data-theme="light"]) .saved-q:hover {
      border-color: rgba(18,70,176,0.30);
      background: #dbeafe;
    }
    :host-context([data-theme="light"]) .sq-title { color: #050810; }
    :host-context([data-theme="light"]) .sq-meta  { color: #374151; }
    :host-context([data-theme="light"]) .stag.green {
      background: rgba(6,95,70,0.12);
      border-color: rgba(6,95,70,0.30);
      color: #16a34a;
    }
    :host-context([data-theme="light"]) .stag.blue {
      background: rgba(18,70,176,0.12);
      border-color: rgba(18,70,176,0.30);
      color: #1246b0;
    }

    /* History */
    :host-context([data-theme="light"]) .history-item {
      border-bottom-color: rgba(0,0,0,0.06);
    }
    :host-context([data-theme="light"]) .history-item:hover { background: rgba(18,70,176,0.07); }
    :host-context([data-theme="light"]) .hi-q  { color: #111827; }
    :host-context([data-theme="light"]) .hi-db { color: #075985; }
    :host-context([data-theme="light"]) .hi-stat { color: #374151; }
    :host-context([data-theme="light"]) .hi-time { color: #4b5563; }
    :host-context([data-theme="light"]) .hi-number {
      background: rgba(18,70,176,0.12);
      border-color: rgba(18,70,176,0.30);
      color: #1246b0;
    }

    /* Audit */
    :host-context([data-theme="light"]) .ae-dot {
      background: #5b21b6;
      border-color: rgba(91,33,182,0.50);
      box-shadow: none;
    }
    :host-context([data-theme="light"]) .ae-line {
      background: linear-gradient(180deg, rgba(91,33,182,0.25), transparent);
    }
    :host-context([data-theme="light"]) .ae-time  { color: #5b21b6; }
    :host-context([data-theme="light"]) .ae-action { color: #111827; }
    :host-context([data-theme="light"]) .ae-tag {
      background: rgba(91,33,182,0.12);
      border-color: rgba(91,33,182,0.30);
      color: #5b21b6;
    }

    /* Empty state */
    :host-context([data-theme="light"]) .empty-state { color: #374151; }
  `],
})
export class RightPanelComponent implements OnInit {
  private catalogSvc    = inject(CatalogService);
  private querySvc      = inject(QueryService);
  private auditSvc      = inject(AuditService);
  private questionsSvc  = inject(QuestionsService);

  activeTab: PanelTab = 'catalog';

  get tabSliderLeft(): string {
    const i = ['catalog','history','audit'].indexOf(this.activeTab);
    return `${i * 33.333}%`;
  }

  tables:         CatalogTable[]  = [];
  history:        HistoryEntry[]  = [];
  auditLog:       AuditEntry[]    = [];
  savedQuestions: SavedQuestion[] = [];

  ngOnInit(): void {
    this.catalogSvc.resolveByIntent('sales_drop').subscribe(t => this.tables = t);
    this.questionsSvc.getSimilar('sales_drop').subscribe(q => this.savedQuestions = q);
  }

  setTab(tab: PanelTab): void {
    this.activeTab = tab;
    if (tab === 'history' && this.history.length === 0) {
      this.querySvc.getHistory('alex.rodrigues@acme.com').subscribe(h => this.history = h);
    }
    if (tab === 'audit' && this.auditLog.length === 0) {
      this.auditSvc.getSession('sess_9f3a').subscribe(a => this.auditLog = a);
    }
  }
}
