// ============================================================
// navbar.component.ts — Header v6: limpo mas com presença
// ============================================================
import { Component, input, output, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule, LUCIDE_ICONS, LucideIconProvider, Building2, BellDot } from 'lucide-angular';
import type { DbEngine } from '../../models/copilot.models';
import { ThemeService } from '../../services/theme.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  providers: [
    { provide: LUCIDE_ICONS, multi: true, useValue: new LucideIconProvider({ Building2, BellDot }) },
  ],
  template: `
    <header class="topnav" role="banner">
      <div class="nav-topline" aria-hidden="true"></div>
      <div class="nav-sweep"  aria-hidden="true"></div>

      <!-- Hamburger — mobile/tablet only -->
      <button class="menu-btn" type="button"
              (click)="menuToggle.emit()"
              [attr.aria-expanded]="sidebarOpen()"
              aria-label="Open navigation menu"
              aria-controls="main-sidebar">
        <span class="menu-bar" [class.open]="sidebarOpen()"></span>
      </button>

      <!-- ═══ LEFT: Brand ═══ -->
      <div class="nav-brand" role="img" aria-label="Bob — Corporate Data Copilot">
        <div class="brand-logo" aria-hidden="true">
          <img src="assets/bob-logo.png" alt="" class="brand-logo-img"/>
          <div class="logo-ring"></div>
        </div>
        <div class="brand-text">
          <div class="brand-name">Bob</div>
          <div class="brand-sub">Corporate Data Copilot</div>
        </div>
      </div>

      <!-- ═══ CENTER: 3 compact metrics ═══ -->
      <div class="nav-metrics" role="region" aria-label="System status">

        <!-- AI Status -->
        <div class="metric-tile" role="status" aria-label="AI active">
          <div class="tile-icon green" aria-hidden="true">
            <span class="ai-dot"></span>
            <span class="ai-ring"></span>
          </div>
          <div class="tile-body">
            <div class="tile-label">AI STATUS</div>
            <div class="tile-val">ACTIVE</div>
          </div>
          <div class="wave-bars" aria-hidden="true">
            <div class="wbar" *ngFor="let b of bars" [style.height.px]="b"></div>
          </div>
        </div>

        <!-- Latency -->
        <div class="metric-tile" role="status" [attr.aria-label]="'Latency: ' + latency + 'ms'">
          <div class="tile-body">
            <div class="tile-label">LATENCY</div>
            <div class="tile-val mono">{{ latency }}<span class="tile-unit">ms</span></div>
          </div>
        </div>

      </div>

              <!-- Theme Toggle -->
        <button class="theme-toggle" type="button"
                [class.light-active]="theme.theme() === 'light'"
                (click)="theme.toggle()"
                [attr.aria-label]="theme.theme() === 'dark' ? 'Enable light mode' : 'Enable dark mode'"
                [attr.aria-pressed]="theme.theme() === 'light'">
          <span class="tt-track" aria-hidden="true">
            <span class="tt-star tt-s1"></span>
            <span class="tt-star tt-s2"></span>
            <span class="tt-star tt-s3"></span>
            <span class="tt-ray tt-r1"></span>
            <span class="tt-ray tt-r2"></span>
            <span class="tt-ray tt-r3"></span>
            <span class="tt-ray tt-r4"></span>
          </span>
          <span class="tt-thumb" aria-hidden="true">
            <span class="tt-icon tt-moon">
              <svg viewBox="0 0 18 18" fill="none">
                <path d="M14.5 10.5A7 7 0 0 1 7.5 3.5a7 7 0 0 0 0 11 7 7 0 0 0 7-3z" fill="currentColor"/>
              </svg>
            </span>
            <span class="tt-icon tt-sun">
              <svg viewBox="0 0 18 18" fill="none">
                <circle cx="9" cy="9" r="4" fill="currentColor"/>
                <g stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
                  <line x1="9" y1="1"  x2="9"  y2="3.2"/>
                  <line x1="9" y1="14.8" x2="9" y2="17"/>
                  <line x1="1"  y1="9"  x2="3.2" y2="9"/>
                  <line x1="14.8" y1="9" x2="17" y2="9"/>
                  <line x1="3.2" y1="3.2" x2="4.8" y2="4.8"/>
                  <line x1="13.2" y1="13.2" x2="14.8" y2="14.8"/>
                  <line x1="14.8" y1="3.2" x2="13.2" y2="4.8"/>
                  <line x1="4.8" y1="13.2" x2="3.2" y2="14.8"/>
                </g>
              </svg>
            </span>
          </span>
        </button>

      <!-- ═══ RIGHT: Workspace · Notif · Toggle · User ═══ -->
      <div class="nav-right">

        <div class="workspace-chip" role="note" aria-label="Workspace: acme-corp-prod" tabindex="0">
          <lucide-icon name="building-2" [size]="12" [strokeWidth]="2" aria-hidden="true"></lucide-icon>
          acme-corp-prod
        </div>

        <!-- User pill -->
        <button class="user-pill" type="button"
                aria-label="User menu: Alex Rodrigues, Senior Analyst"
                aria-haspopup="true">
          <div class="user-avatar" aria-hidden="true">
            <span>AR</span>
            <div class="avatar-ring"></div>
          </div>
          <div class="user-info">
            <div class="user-name">Alex Rodrigues</div>
            <div class="user-role">Senior Analyst</div>
          </div>
        </button>

      </div>
    </header>
  `,
  styles: [`
    /* ════════════════════════════════════════
       TOPNAV
    ════════════════════════════════════════ */
    .topnav {
      height: 72px;
      background: linear-gradient(180deg, #10152a 0%, #0c0f1e 100%);
      display: flex;
      align-items: center;
      padding: 0 28px;
      gap: 24px;
      flex-shrink: 0;
      border-bottom: 1px solid rgba(255,255,255,0.08);
      position: relative;
      overflow: hidden;
      box-shadow: 0 4px 28px rgba(0,0,0,0.5), 0 1px 0 rgba(255,255,255,0.04);
      transition: background 0.28s, border-color 0.28s, box-shadow 0.28s;
    }
    :host-context([data-theme="light"]) .topnav {
      background: #ffffff;
      border-bottom-color: rgba(0,0,0,0.10);
      box-shadow: 0 1px 0 rgba(0,0,0,0.10), 0 4px 20px rgba(0,0,0,0.07);
    }

    /* Linha topo gradiente animada */
    .nav-topline {
      position: absolute; top: 0; left: 0; right: 0; height: 2.5px;
      background: linear-gradient(90deg,
        #4f9eff 0%, #b87dff 25%, #00e5ff 50%, #00e676 75%, #ffab00 100%
      );
      background-size: 300% 100%;
      animation: toplineShift 6s ease infinite;
    }
    @keyframes toplineShift {
      0%,100% { background-position: 0% 0%; }
      50%      { background-position: 100% 0%; }
    }

    /* Sweep decorativo */
    .nav-sweep {
      position: absolute; top: 0; bottom: 0; width: 120px;
      background: linear-gradient(90deg, transparent, rgba(79,158,255,0.04), transparent);
      animation: sweepMove 8s linear infinite;
      pointer-events: none;
    }
    @keyframes sweepMove { from { left: -120px; } to { left: 110%; } }

    /* ── Hambúrguer ── */
    .menu-btn {
      display: none;
      flex-direction: column; justify-content: center; align-items: center;
      width: 42px; height: 42px;
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 11px;
      cursor: pointer; flex-shrink: 0; z-index: 1;
      gap: 5px; outline: none; padding: 0;
      transition: background 0.18s, border-color 0.18s;
    }
    .menu-btn:focus-visible { outline: 2px solid #6480ff; outline-offset: 2px; }
    .menu-btn:hover { background: rgba(255,255,255,0.10); border-color: rgba(100,128,255,0.35); }
    .menu-bar, .menu-bar::before, .menu-bar::after {
      content: ''; display: block;
      width: 18px; height: 2px;
      background: rgba(255,255,255,0.65);
      border-radius: 2px;
      transition: transform 0.22s, opacity 0.22s;
      position: relative;
    }
    .menu-bar::before { top: -5px; }
    .menu-bar::after  { top: 3px; }
    .menu-bar.open { background: transparent; }
    .menu-bar.open::before { transform: rotate(45deg) translate(3px, 4px); background: #6480ff; }
    .menu-bar.open::after  { transform: rotate(-45deg) translate(3px, -4px); background: #6480ff; }

    :host-context([data-theme="light"]) .menu-bar,
    :host-context([data-theme="light"]) .menu-bar::before,
    :host-context([data-theme="light"]) .menu-bar::after { background: #1e293b; }
    :host-context([data-theme="light"]) .menu-btn {
      background: #c8d3e8; border-color: rgba(0,0,0,0.16);
    }
    :host-context([data-theme="light"]) .menu-btn:hover {
      background: #b8c6e0;
    }

    @media (max-width: 1023px) {
      .menu-btn { display: flex; }
      .nav-metrics { display: none; }
      .brand-badge { display: none; }
    }
    @media (max-width: 639px) {
      .topnav { padding: 0 14px; gap: 10px; }
      .workspace-chip { display: none; }
      .icon-btn { display: none; }
      .user-role { display: none; }
      .brand-sub { display: none; }
    }

    /* ════════════════════════════════════════
       BRAND
    ════════════════════════════════════════ */
    .nav-brand {
      display: flex; align-items: center; gap: 13px;
      flex-shrink: 0; z-index: 1;
    }

    .brand-logo {
      position: relative;
      width: 52px; height: 52px;
      background: #e8eaf0;
      border: 2px solid rgba(100,128,255,0.40);
      border-radius: 14px;
      display: flex; align-items: center; justify-content: center;
      box-shadow:
        0 0 24px rgba(100,128,255,0.30),
        0 0 48px rgba(168,85,247,0.12),
        inset 0 1px 0 rgba(255,255,255,0.5);
    }
    .brand-logo-img {
      width: 44px; height: 44px;
      object-fit: contain; position: relative; z-index: 1;
    }
    .logo-ring {
      position: absolute; inset: -7px; border-radius: 20px;
      border: 1.5px solid rgba(100,128,255,0.35);
      animation: ringPulse 3s ease-out infinite;
    }
    @keyframes ringPulse {
      0%   { transform: scale(1); opacity: 0.7; }
      100% { transform: scale(1.3); opacity: 0; }
    }

    .brand-text { display: flex; flex-direction: column; gap: 2px; }
    .brand-name {
      font-size: 22px; font-weight: 900;
      letter-spacing: -0.4px; line-height: 1;
      background: linear-gradient(110deg, #7c9cff 0%, #c084fc 60%, #818cf8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .brand-sub {
      font-size: 10.5px; font-weight: 400;
      color: rgba(255,255,255,0.4);
      letter-spacing: 0.02em;
    }
    :host-context([data-theme="light"]) .brand-sub { color: #475569; }

    .brand-badge {
      display: flex; align-items: center; gap: 5px;
      padding: 4px 11px; border-radius: 999px;
      background: rgba(100,128,255,0.10);
      border: 1px solid rgba(100,128,255,0.28);
      font-size: 9px; font-weight: 800;
      color: #93a8ff; letter-spacing: 1.5px;
      flex-shrink: 0;
    }
    :host-context([data-theme="light"]) .brand-badge {
      background: rgba(30,64,175,0.08);
      border-color: rgba(30,64,175,0.25);
      color: #1e40af;
    }
    .badge-pulse {
      width: 5px; height: 5px; border-radius: 50%;
      background: #6480ff; box-shadow: 0 0 8px #6480ff;
      animation: blink 2s infinite;
      flex-shrink: 0;
    }
    :host-context([data-theme="light"]) .badge-pulse {
      background: #1e40af; box-shadow: 0 0 6px rgba(30,64,175,0.5);
    }
    @keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0.25; } }

    /* ════════════════════════════════════════
       METRICS CENTER
    ════════════════════════════════════════ */
    .nav-metrics {
      display: flex; align-items: center; gap: 8px;
      flex: 1; justify-content: center; z-index: 1;
    }

    .metric-tile {
      display: flex; align-items: center; gap: 11px;
      padding: 9px 16px; border-radius: 12px;
      border: 1px solid rgba(255,255,255,0.08);
      background: rgba(255,255,255,0.04);
      backdrop-filter: blur(8px);
      transition: border-color 0.2s, background 0.2s, transform 0.2s;
      position: relative; overflow: hidden;
      flex-shrink: 0;
    }
    .metric-tile::before {
      content: '';
      position: absolute; inset: 0;
      background: linear-gradient(135deg, rgba(255,255,255,0.03) 0%, transparent 55%);
      pointer-events: none;
    }
    .metric-tile:hover {
      border-color: rgba(255,255,255,0.15);
      background: rgba(255,255,255,0.07);
      transform: translateY(-1px);
    }

    :host-context([data-theme="light"]) .metric-tile {
      border-color: rgba(0,0,0,0.14);
      background: #ffffff;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    :host-context([data-theme="light"]) .metric-tile:hover {
      border-color: rgba(0,0,0,0.22);
      background: #eef2fb;
    }

    /* tile icon (IA dot) */
    .tile-icon {
      position: relative; width: 22px; height: 22px;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
    }
    .ai-dot {
      width: 9px; height: 9px; border-radius: 50%;
      background: #00e676; box-shadow: 0 0 10px #00e676;
      animation: blink 1.8s infinite;
    }
    .ai-ring {
      position: absolute; inset: -4px; border-radius: 50%;
      border: 1.5px solid rgba(0,230,118,0.4);
      animation: ringCirc 2s ease-out infinite;
    }
    @keyframes ringCirc { 0% { transform:scale(0.55); opacity:1; } 100% { transform:scale(1.8); opacity:0; } }
    :host-context([data-theme="light"]) .ai-dot {
      background: #15803d; box-shadow: 0 0 7px rgba(21,128,61,0.55);
    }
    :host-context([data-theme="light"]) .ai-ring { border-color: rgba(21,128,61,0.4); }

    .tile-body { display: flex; flex-direction: column; gap: 1px; }
    .tile-label {
      font-size: 9px; font-weight: 700; letter-spacing: 0.9px;
      text-transform: uppercase; color: rgba(255,255,255,0.4);
    }
    :host-context([data-theme="light"]) .tile-label { color: #475569; }

    .tile-val {
      font-size: 15px; font-weight: 800; line-height: 1;
      color: #ffffff;
    }
    :host-context([data-theme="light"]) .tile-val { color: #0f172a; }
    .tile-val.mono { font-family: "JetBrains Mono", monospace; }
    .tile-unit { font-size: 10px; font-weight: 600; opacity: 0.6; margin-left: 1px; }

    /* wave bars */
    .wave-bars { display: flex; align-items: center; gap: 2px; height: 16px; }
    .wbar {
      width: 2.5px; border-radius: 2px;
      background: #00e676; min-height: 2px;
      animation: waveUp 1s ease-in-out infinite alternate;
    }
    .wbar:nth-child(even) { animation-delay: 0.15s; }
    .wbar:nth-child(3n)   { animation-delay: 0.28s; }
    @keyframes waveUp { 0% { transform:scaleY(0.25); opacity:0.5; } 100% { transform:scaleY(1); opacity:1; } }
    :host-context([data-theme="light"]) .wbar { background: #15803d; }

    /* ════════════════════════════════════════
       RIGHT
    ════════════════════════════════════════ */
    .nav-right {
      display: flex; align-items: center; gap: 9px;
      flex-shrink: 0; z-index: 1;
    }

    /* Workspace chip */
    .workspace-chip {
      display: flex; align-items: center; gap: 6px;
      padding: 7px 14px; border-radius: 9px;
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.09);
      font-size: 11.5px; color: rgba(255,255,255,0.62);
      font-weight: 500; cursor: pointer;
      transition: all 0.18s;
    }
    .workspace-chip:hover { color: #fff; border-color: rgba(255,255,255,0.18); background: rgba(255,255,255,0.08); }
    .workspace-chip:focus-visible { outline: 2px solid #4f9eff; outline-offset: 2px; border-radius: 8px; }
    :host-context([data-theme="light"]) .workspace-chip {
      background: #c8d3e8; border-color: rgba(0,0,0,0.18); color: #0f172a;
    }
    :host-context([data-theme="light"]) .workspace-chip:hover {
      background: #b8c6e0; border-color: rgba(0,0,0,0.28);
    }

    /* Icon button (sino) */
    .icon-btn {
      width: 40px; height: 40px; border-radius: 11px;
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.09);
      color: rgba(255,255,255,0.5);
      display: flex; align-items: center; justify-content: center;
      cursor: pointer; transition: all 0.18s; position: relative;
      outline: none;
    }
    .icon-btn:hover { color: #fff; border-color: rgba(184,125,255,0.45); background: rgba(184,125,255,0.1); }
    .icon-btn:focus-visible { outline: 2px solid #b87dff; outline-offset: 2px; }
    :host-context([data-theme="light"]) .icon-btn {
      background: #c8d3e8; border-color: rgba(0,0,0,0.18); color: #1e293b;
    }
    :host-context([data-theme="light"]) .icon-btn:hover {
      background: #b8c6e0; border-color: rgba(0,0,0,0.28); color: #0f172a;
    }

    /* notif dot */
    .notif-dot {
      position: absolute; top: 7px; right: 7px;
      width: 7px; height: 7px; border-radius: 50%;
      background: #ff4d9e; box-shadow: 0 0 8px #ff4d9e;
      border: 1.5px solid #0c0f1e;
    }
    :host-context([data-theme="light"]) .notif-dot { border-color: #ffffff; }

    /* ════════════════════════════════════════
       THEME TOGGLE
    ════════════════════════════════════════ */
    .theme-toggle {
      position: relative;
      width: 62px; height: 32px;
      border-radius: 999px; border: none;
      cursor: pointer; padding: 0; outline: none; flex-shrink: 0;
      background: linear-gradient(135deg, #0c0e1f 0%, #1a1440 50%, #0f172a 100%);
      box-shadow:
        0 0 0 1.5px rgba(100,128,255,0.38),
        0 0 14px rgba(100,128,255,0.20),
        inset 0 1px 0 rgba(255,255,255,0.07);
      transition: background 0.42s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.3s;
      overflow: hidden;
    }
    .theme-toggle:focus-visible { box-shadow: 0 0 0 3px rgba(100,128,255,0.5); }
    .theme-toggle:hover {
      box-shadow: 0 0 0 1.5px rgba(100,128,255,0.62), 0 0 18px rgba(100,128,255,0.32), inset 0 1px 0 rgba(255,255,255,0.09);
    }
    .theme-toggle.light-active {
      background: linear-gradient(135deg, #7dd3fc 0%, #fde68a 50%, #fbbf24 100%);
      box-shadow: 0 0 0 1.5px rgba(251,191,36,0.5), 0 0 14px rgba(251,191,36,0.32), inset 0 1px 0 rgba(255,255,255,0.28);
    }
    .theme-toggle.light-active:hover {
      box-shadow: 0 0 0 1.5px rgba(251,191,36,0.75), 0 0 22px rgba(251,191,36,0.48), inset 0 1px 0 rgba(255,255,255,0.28);
    }

    .tt-track { position: absolute; inset: 0; border-radius: 999px; overflow: hidden; pointer-events: none; }
    .tt-star { position: absolute; border-radius: 50%; background: #fff; transition: opacity 0.35s; }
    .tt-s1 { width: 3px; height: 3px; top: 7px;  right: 13px; opacity: 0.85; animation: starTwinkle 2s ease-in-out infinite alternate; }
    .tt-s2 { width: 2px; height: 2px; top: 15px; right: 9px;  opacity: 0.5;  animation: starTwinkle 1.5s 0.4s ease-in-out infinite alternate; }
    .tt-s3 { width: 2px; height: 2px; top: 9px;  right: 21px; opacity: 0.7;  animation: starTwinkle 1.8s 0.8s ease-in-out infinite alternate; }
    @keyframes starTwinkle { 0% { opacity:0.3; transform:scale(0.8); } 100% { opacity:0.9; transform:scale(1.2); } }
    .light-active .tt-star { opacity: 0 !important; }

    .tt-ray { position: absolute; background: rgba(255,255,255,0.55); border-radius: 2px; opacity: 0; transition: opacity 0.35s; }
    .tt-r1 { width: 9px; height: 2px; top: 8px;  left: 5px;  transform: rotate(45deg); }
    .tt-r2 { width: 7px; height: 2px; top: 18px; left: 6px;  transform: rotate(-20deg); }
    .tt-r3 { width: 5px; height: 2px; top: 4px;  left: 13px; transform: rotate(-60deg); }
    .tt-r4 { width: 6px; height: 2px; top: 15px; left: 4px;  transform: rotate(70deg); }
    .light-active .tt-ray { opacity: 1; }

    .tt-thumb {
      position: absolute; top: 3px; left: 3px;
      width: 26px; height: 26px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      background: linear-gradient(135deg, #1e2a4a 0%, #2d3a6b 100%);
      box-shadow: 0 2px 7px rgba(0,0,0,0.5), 0 0 9px rgba(100,128,255,0.25), inset 0 1px 0 rgba(255,255,255,0.1);
      transition: transform 0.42s cubic-bezier(0.34,1.56,0.64,1), background 0.35s, box-shadow 0.35s;
    }
    .light-active .tt-thumb {
      transform: translateX(30px);
      background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
      box-shadow: 0 2px 6px rgba(0,0,0,0.15), 0 0 12px rgba(251,191,36,0.55), inset 0 1px 0 rgba(255,255,255,0.4);
    }

    .tt-icon { position: absolute; width: 13px; height: 13px; display: flex; align-items: center; justify-content: center; transition: opacity 0.25s, transform 0.35s; }
    .tt-moon { color: #a5b4fc; opacity: 1; transform: scale(1); }
    .tt-sun  { color: #fff;    opacity: 0; transform: rotate(-90deg) scale(0.5); }
    .light-active .tt-moon { opacity: 0; transform: rotate(90deg) scale(0.5); }
    .light-active .tt-sun  { opacity: 1; transform: rotate(0deg) scale(1); }

    /* ════════════════════════════════════════
       USER PILL
    ════════════════════════════════════════ */
    .user-pill {
      display: flex; align-items: center; gap: 10px;
      padding: 7px 14px 7px 7px; border-radius: 13px;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.09);
      cursor: pointer; transition: all 0.18s;
      font-family: inherit; text-align: left; outline: none;
    }
    .user-pill:hover { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.16); }
    .user-pill:focus-visible { outline: 2px solid #b87dff; outline-offset: 2px; }
    :host-context([data-theme="light"]) .user-pill {
      background: #c8d3e8; border-color: rgba(0,0,0,0.18);
    }
    :host-context([data-theme="light"]) .user-pill:hover {
      background: #b8c6e0; border-color: rgba(0,0,0,0.28);
    }

    .user-avatar {
      width: 38px; height: 38px; border-radius: 50%;
      background: linear-gradient(135deg, #5b21b6, #9333ea);
      display: flex; align-items: center; justify-content: center;
      font-size: 12px; font-weight: 800; color: #fff;
      box-shadow: 0 0 14px rgba(147,51,234,0.4);
      position: relative; flex-shrink: 0;
    }
    .avatar-ring {
      position: absolute; inset: -3px; border-radius: 50%;
      border: 1.5px solid transparent;
      border-top-color: rgba(167,139,250,0.65);
      border-right-color: rgba(167,139,250,0.25);
      animation: spinRing 3s linear infinite;
    }
    @keyframes spinRing { to { transform: rotate(360deg); } }

    .user-info { display: flex; flex-direction: column; gap: 1px; }
    .user-name { font-size: 13px; font-weight: 700; color: #f1f5f9; }
    .user-role { font-size: 10px; color: rgba(255,255,255,0.45); }
    :host-context([data-theme="light"]) .user-name { color: #0f172a; }
    :host-context([data-theme="light"]) .user-role { color: #1e293b; }
  `]
})
export class NavbarComponent implements OnInit, OnDestroy {
  engine      = input<DbEngine>('aws');
  sidebarOpen = input<boolean>(false);
  menuToggle  = output<void>();

  bars: number[] = [5, 9, 6, 11, 7, 10, 5, 12, 6, 9, 5, 11];
  latency = 284;
  private interval?: ReturnType<typeof setInterval>;

  readonly theme = inject(ThemeService);

  ngOnInit(): void {
    this.interval = setInterval(() => {
      this.bars = this.bars.map(() => Math.floor(Math.random() * 9) + 3);
      this.latency = Math.floor(Math.random() * 180) + 120;
    }, 900);
  }
  ngOnDestroy(): void { clearInterval(this.interval); }
}
