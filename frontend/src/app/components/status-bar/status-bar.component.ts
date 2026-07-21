// ============================================================
// status-bar.component.ts — Neon Dark v4
// ============================================================
import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-status-bar',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="status-bar" role="contentinfo" aria-label="System status bar">

      <!-- Left: API status only -->
      <div class="sb-left">
        <div class="status-chip cyan" role="status" aria-label="Bob API: online">
          <span class="chip-dot" aria-hidden="true"></span>
          Bob API
          <span class="chip-detail" aria-hidden="true">online</span>
        </div>
        <div class="sb-vsep" aria-hidden="true"></div>
        <div class="mini-bar-wrap" aria-hidden="true">
          <div class="mini-bar" *ngFor="let b of bars; let i = index"
               [style.height.px]="b"
               [style.--bar-i]="i"></div>
        </div>
        <span class="engine-label" aria-hidden="true">SQL Engine</span>
      </div>

      <!-- Center: breadcrumb -->
      <div class="sb-center">
        <span class="path-seg" aria-hidden="true">acme-corp-prod</span>
        <span class="path-arrow" aria-hidden="true">›</span>
        <span class="path-seg active" aria-hidden="true">analytics_v2</span>
      </div>

      <!-- Right: session -->
      <div class="sb-right">
        <span class="info-pill session" aria-label="Session: sess_9f3a">
          <svg width="9" height="9" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
            <rect x="1" y="4" width="14" height="10" rx="1"/>
            <path d="M5 4V3a3 3 0 016 0v1"/>
          </svg>
          sess_9f3a
        </span>
        <span class="sb-vsep" aria-hidden="true"></span>
        <span class="info-user" aria-label="User: alex.rodrigues@acme.com">alex.rodrigues&#64;acme.com</span>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; }

    .status-bar {
      height: 32px;
      background: #08090f;
      border-top: 1px solid rgba(79,158,255,0.12);
      display: flex;
      align-items: center;
      padding: 0 16px;
      flex-shrink: 0;
      font-family: "JetBrains Mono", "Cascadia Code", monospace;
      font-size: 10px;
      position: relative;
      overflow: hidden;
      transition: background 0.28s, border-color 0.28s;
    }
    :host-context([data-theme="light"]) .status-bar {
      background: #e4e8f2;
      border-top-color: rgba(0,0,0,0.12);
    }

    /* Linha topo removida — evita repetição com o header */

    .sb-left, .sb-right {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .sb-center {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 5px;
    }

    /* ── Status chips ── */
    .status-chip {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.01em;
      transition: opacity 0.2s;
    }
    .status-chip:hover { opacity: 0.9; }

    .status-chip.green {
      color: #00e676;
      background: rgba(0,230,118,0.06);
      border: 1px solid rgba(0,230,118,0.15);
    }
    .status-chip.cyan {
      color: #00e5ff;
      background: rgba(0,229,255,0.06);
      border: 1px solid rgba(0,229,255,0.15);
    }
    .status-chip.amber {
      color: #ffab00;
      background: rgba(255,171,0,0.06);
      border: 1px solid rgba(255,171,0,0.15);
    }
    :host-context([data-theme="light"]) .status-chip.green {
      color: #16a34a; background: rgba(22,163,74,0.12); border-color: rgba(22,163,74,0.30);
    }
    :host-context([data-theme="light"]) .status-chip.cyan {
      color: #0891b2; background: rgba(8,145,178,0.12); border-color: rgba(8,145,178,0.30);
    }
    :host-context([data-theme="light"]) .status-chip.amber {
      color: #d97706; background: rgba(217,119,6,0.12); border-color: rgba(217,119,6,0.30);
    }

    .chip-dot {
      width: 5px;
      height: 5px;
      border-radius: 50%;
      flex-shrink: 0;
    }
    .status-chip.green .chip-dot  { background: #00e676; box-shadow: 0 0 5px #00e676; animation: chipBlink 2s infinite; }
    .status-chip.cyan  .chip-dot  { background: #00e5ff; box-shadow: 0 0 5px #00e5ff; animation: chipBlink 1.8s infinite; }
    .status-chip.amber .chip-dot  { background: #ffab00; box-shadow: 0 0 5px #ffab00; animation: chipBlink 3s infinite; }
    :host-context([data-theme="light"]) .status-chip.green .chip-dot { background: #16a34a; box-shadow: none; }
    :host-context([data-theme="light"]) .status-chip.cyan  .chip-dot { background: #0891b2; box-shadow: none; }
    :host-context([data-theme="light"]) .status-chip.amber .chip-dot { background: #d97706; box-shadow: none; }

    @keyframes chipBlink {
      0%,100% { opacity: 1; }
      50%      { opacity: 0.25; }
    }

    .chip-detail {
      font-size: 9px;
      opacity: 0.55;
      margin-left: 1px;
    }

    /* ── Vsep ── */
    .sb-vsep {
      width: 1px;
      height: 14px;
      background: rgba(255,255,255,0.07);
      margin: 0 5px;
    }
    :host-context([data-theme="light"]) .sb-vsep { background: rgba(0,0,0,0.22); }

    /* ── Mini bars ── */
    .mini-bar-wrap {
      display: flex;
      align-items: flex-end;
      gap: 1.5px;
      height: 14px;
    }
    .mini-bar {
      width: 2px;
      border-radius: 1px 1px 0 0;
      transition: height 0.3s ease;
      min-height: 2px;
    }
    .mini-bar:nth-child(odd)  { background: linear-gradient(180deg, #4f9eff, rgba(79,158,255,0.25)); }
    .mini-bar:nth-child(even) { background: linear-gradient(180deg, #b87dff, rgba(184,125,255,0.25)); }
    :host-context([data-theme="light"]) .mini-bar:nth-child(odd)  { background: linear-gradient(180deg, #2563eb, rgba(37,99,235,0.3)); }
    :host-context([data-theme="light"]) .mini-bar:nth-child(even) { background: linear-gradient(180deg, #7c3aed, rgba(124,58,237,0.3)); }

    .engine-label {
      font-size: 9px;
      color: rgba(79,158,255,0.5);
      text-transform: uppercase;
      letter-spacing: 0.8px;
    }
    :host-context([data-theme="light"]) .engine-label { color: #2563eb; }

    /* ── Breadcrumb ── */
    .path-seg {
      font-size: 10px;
      color: rgba(240,244,255,0.45);
    }
    :host-context([data-theme="light"]) .path-seg { color: #374151; }
    .path-seg.active {
      color: #4f9eff;
      font-weight: 700;
    }
    :host-context([data-theme="light"]) .path-seg.active { color: #1246b0; font-weight: 800; }
    .path-arrow {
      color: rgba(255,255,255,0.1);
      font-size: 12px;
    }
    :host-context([data-theme="light"]) .path-arrow { color: rgba(0,0,0,0.30); }

    /* ── Right ── */
    .info-pill {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 9.5px;
    }
    .info-pill.session {
      color: #b87dff;
      background: rgba(184,125,255,0.07);
      border: 1px solid rgba(184,125,255,0.18);
    }
    :host-context([data-theme="light"]) .info-pill.session {
      color: #7c3aed;
      background: rgba(124,58,237,0.10);
      border-color: rgba(124,58,237,0.28);
    }
    .info-user {
      color: rgba(240,244,255,0.45);
      font-size: 10px;
    }
    :host-context([data-theme="light"]) .info-user { color: #111827; }
  `],
})
export class StatusBarComponent implements OnInit, OnDestroy {
  bars: number[] = [3, 6, 4, 9, 5, 8, 3, 11, 4, 7, 5, 10, 3, 8, 4];

  private barsInterval?: ReturnType<typeof setInterval>;

  ngOnInit(): void {
    this.barsInterval = setInterval(() => {
      this.bars = this.bars.map(() => Math.floor(Math.random() * 10) + 2);
    }, 450);
  }

  ngOnDestroy(): void {
    clearInterval(this.barsInterval);
  }
}
