// ============================================================
// navbar.component.ts — Neon Dark v4
// Header alto (72px), rico em cores, texto legível
// ============================================================
import { Component, input, output, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule, LUCIDE_ICONS, LucideIconProvider, Building2, BellDot } from 'lucide-angular';
import type { DbEngine } from '../../models/copilot.models';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  providers: [
    { provide: LUCIDE_ICONS, multi: true, useValue: new LucideIconProvider({ Building2, BellDot }) },
  ],
  template: `
    <header class="topnav" role="banner">
      <!-- Decorativos — ocultos de leitores de tela -->
      <div class="nav-sweep"   aria-hidden="true"></div>
      <div class="nav-topline" aria-hidden="true"></div>

      <!-- Botão hambúrguer — só mobile/tablet -->
      <button class="menu-btn"
              type="button"
              (click)="menuToggle.emit()"
              [attr.aria-expanded]="sidebarOpen()"
              aria-label="Abrir menu de navegação"
              aria-controls="main-sidebar">
        <span class="menu-bar" [class.open]="sidebarOpen()"></span>
      </button>

      <!-- ═══ LEFT: Brand ═══ -->
      <div class="nav-brand" role="img" aria-label="Bob — Corporate Data Copilot">
        <div class="brand-logo" aria-hidden="true">
          <img src="assets/bob-logo.png" alt="" class="brand-logo-img"/>
          <div class="logo-pulse"></div>
          <div class="logo-pulse logo-pulse-2"></div>
        </div>
        <div class="brand-sep" aria-hidden="true"></div>
        <div class="brand-info">
          <div class="brand-name">Bob</div>
          <div class="brand-tagline">Corporate Data Copilot</div>
        </div>
        <div class="brand-badge" aria-label="Plano Enterprise ativo">
          <span class="badge-dot" aria-hidden="true"></span>
          ENTERPRISE
        </div>
      </div>

      <!-- ═══ CENTER: Métricas vivas ═══ -->
      <div class="nav-metrics" role="region" aria-label="Métricas do sistema">
        <div class="metric-card green" role="status" aria-label="Status da IA: ativa">
          <div class="metric-icon-wrap" aria-hidden="true">
            <div class="ai-dot"></div>
            <div class="ai-ripple"></div>
          </div>
          <div class="metric-content">
            <div class="metric-label" aria-hidden="true">IA STATUS</div>
            <div class="metric-val">ATIVA</div>
          </div>
          <div class="metric-bars" aria-hidden="true">
            <div class="mbar" *ngFor="let b of bars" [style.height.px]="b"></div>
          </div>
        </div>

        <div class="metric-card blue" role="status" [attr.aria-label]="'Consultas hoje: ' + queryCount">
          <div class="metric-content">
            <div class="metric-label" aria-hidden="true">CONSULTAS HOJE</div>
            <div class="metric-val mono" aria-live="polite">{{ queryCount }}</div>
          </div>
        </div>

        <div class="metric-card purple" role="status" [attr.aria-label]="'Latência: ' + latency + ' milissegundos'">
          <div class="metric-content">
            <div class="metric-label" aria-hidden="true">LATÊNCIA</div>
            <div class="metric-val mono" aria-live="polite">{{ latency }}<span class="metric-unit" aria-hidden="true">ms</span></div>
          </div>
        </div>

        <div class="metric-card amber" role="status" [attr.aria-label]="'Motor de banco: ' + engine()">
          <div class="metric-content">
            <div class="metric-label" aria-hidden="true">MOTOR</div>
            <div class="metric-val">{{ engine() | uppercase }}</div>
          </div>
        </div>
      </div>

      <!-- ═══ RIGHT: User ═══ -->
      <div class="nav-right">
        <div class="workspace-tag" role="note" aria-label="Workspace: acme-corp-prod" tabindex="0">
          <lucide-icon name="building-2" [size]="13" [strokeWidth]="1.75" aria-hidden="true"></lucide-icon>
          acme-corp-prod
        </div>

        <button class="icon-action" aria-label="Notificações — 1 nova notificação" type="button">
          <lucide-icon name="bell-dot" [size]="16" [strokeWidth]="1.75" aria-hidden="true"></lucide-icon>
          <span class="action-badge" aria-hidden="true"></span>
        </button>

        <button class="user-pill" type="button" aria-label="Menu do usuário: Alex Rodrigues, Analista Sênior" aria-haspopup="true">
          <div class="user-avatar" aria-hidden="true">
            <span>AR</span>
            <div class="avatar-spin-ring"></div>
          </div>
          <div class="user-info">
            <div class="user-name">Alex Rodrigues</div>
            <div class="user-role">Analista Sênior</div>
          </div>
        </button>
      </div>
    </header>
  `,
  styles: [`
    .topnav {
      height: 80px;
      background: linear-gradient(180deg, rgba(19,23,38,0) 0%, #0e1220 100%);
      display: flex;
      align-items: center;
      padding: 0 36px;
      gap: 28px;
      flex-shrink: 0;
      border-bottom: 1px solid rgba(255,255,255,0.1);
      position: relative;
      overflow: hidden;
      box-shadow: 0 4px 32px rgba(0,0,0,0.55);
    }

    /* ── Hambúrguer: oculto por padrão, visível em mobile/tablet ── */
    .menu-btn {
      display: none;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      width: 44px; height: 44px;
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 12px;
      cursor: pointer;
      flex-shrink: 0;
      z-index: 1;
      gap: 5px;
      outline: none;
      transition: background 0.18s;
      padding: 0;
    }
    .menu-btn:focus-visible { outline: 2px solid #6480ff; outline-offset: 2px; }
    .menu-btn:hover { background: rgba(255,255,255,0.09); border-color: rgba(100,128,255,0.4); }
    .menu-bar, .menu-bar::before, .menu-bar::after {
      content: '';
      display: block;
      width: 18px; height: 2px;
      background: rgba(255,255,255,0.7);
      border-radius: 2px;
      transition: transform 0.22s, opacity 0.22s;
      position: relative;
    }
    .menu-bar::before { top: -5px; }
    .menu-bar::after  { top: 3px; }
    .menu-bar.open { background: transparent; }
    .menu-bar.open::before { transform: rotate(45deg) translate(3px, 4px); background: #6480ff; }
    .menu-bar.open::after  { transform: rotate(-45deg) translate(3px, -4px); background: #6480ff; }

    /* Métricas e right ocultas em telas menores */
    @media (max-width: 1023px) {
      .menu-btn { display: flex; }
      .nav-metrics { display: none; }
      .brand-badge { display: none; }
    }
    @media (max-width: 639px) {
      .brand-tagline { display: none; }
      .brand-sep { display: none; }
      .workspace-tag { display: none; }
      .icon-action { display: none; }
      .nav-right { gap: 6px; }
      .user-name { font-size: 12px; }
      .user-role { display: none; }
      .user-pill { padding: 5px 8px 5px 5px; }
    }

    /* Linha colorida no topo */
    .nav-topline {
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 2px;
      background: linear-gradient(90deg,
        #4f9eff 0%, #b87dff 25%, #00e5ff 50%, #00e676 75%, #ffab00 100%
      );
      background-size: 200% 100%;
      animation: gradientShift 4s ease infinite;
    }
    @keyframes gradientShift {
      0%   { background-position: 0% 50%; }
      50%  { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
    }

    /* Sweep */
    .nav-sweep {
      position: absolute; top: 0; bottom: 0;
      width: 80px;
      background: linear-gradient(90deg, transparent, rgba(79,158,255,0.06), transparent);
      animation: scanMove 7s linear infinite;
      pointer-events: none;
    }
    @keyframes scanMove {
      from { left: -80px; }
      to   { left: 110%; }
    }

    /* ═══ BRAND ═══ */
    .nav-brand {
      display: flex; align-items: center; gap: 14px;
      flex-shrink: 0; z-index: 1;
    }

    .brand-logo {
      position: relative;
      width: 58px; height: 58px;
      background: #e8eaf0;
      border: 2px solid rgba(100,130,255,0.35);
      border-radius: 16px;
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 0 28px rgba(100,130,255,0.32), 0 0 56px rgba(168,85,247,0.16);
    }
    .brand-logo-img {
      width: 50px; height: 50px;
      object-fit: contain;
      position: relative; z-index: 1;
    }
    .logo-pulse {
      position: absolute; inset: -6px; border-radius: 20px;
      border: 1.5px solid rgba(100,130,255,0.4);
      animation: rippleBox 3s ease-out infinite;
    }
    .logo-pulse-2 {
      border-color: rgba(168,85,247,0.3);
      animation-delay: 1.5s;
    }
    @keyframes rippleBox {
      0%   { transform: scale(1); opacity: 0.7; }
      100% { transform: scale(1.3); opacity: 0; }
    }

    .brand-sep {
      width: 1px; height: 44px;
      background: linear-gradient(180deg, transparent, rgba(255,255,255,0.15), transparent);
    }

    .brand-info { display: flex; flex-direction: column; gap: 2px; }
    .brand-name {
      font-size: 24px; font-weight: 900; color: #ffffff;
      letter-spacing: -0.5px; line-height: 1;
      background: linear-gradient(90deg, #6480ff, #a855f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .brand-tagline {
      font-size: 12px; color: rgba(255,255,255,0.55);
      font-weight: 400; letter-spacing: 0.02em;
    }

    .brand-badge {
      display: flex; align-items: center; gap: 5px;
      padding: 4px 10px; border-radius: 999px;
      background: rgba(100,130,255,0.12);
      border: 1px solid rgba(100,130,255,0.3);
      font-size: 9px; font-weight: 800;
      color: #8098ff; letter-spacing: 1.5px;
    }
    .badge-dot {
      width: 5px; height: 5px; border-radius: 50%;
      background: #6480ff;
      box-shadow: 0 0 8px #6480ff;
      animation: pulseGlow 2s infinite;
    }
    @keyframes pulseGlow {
      0%,100% { opacity: 1; } 50% { opacity: 0.3; }
    }

    /* ═══ METRICS ═══ */
    .nav-metrics {
      display: flex; align-items: center; gap: 8px;
      flex: 1; justify-content: center; z-index: 1;
    }

    .metric-card {
      display: flex; align-items: center; gap: 12px;
      padding: 10px 18px; border-radius: 14px;
      border: 1px solid;
      min-width: 130px;
      transition: transform 0.2s;
      position: relative; overflow: hidden;
    }
    .metric-card::before {
      content: ''; position: absolute; inset: 0;
      background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, transparent 60%);
      pointer-events: none;
    }
    .metric-card:hover { transform: translateY(-2px); }

    .metric-card.green {
      background: linear-gradient(135deg, rgba(0,230,118,0.12) 0%, rgba(0,230,118,0.04) 100%);
      border-color: rgba(0,230,118,0.3);
      box-shadow: 0 0 20px rgba(0,230,118,0.08);
    }
    .metric-card.blue {
      background: linear-gradient(135deg, rgba(79,158,255,0.12) 0%, rgba(79,158,255,0.04) 100%);
      border-color: rgba(79,158,255,0.3);
      box-shadow: 0 0 20px rgba(79,158,255,0.08);
    }
    .metric-card.purple {
      background: linear-gradient(135deg, rgba(184,125,255,0.12) 0%, rgba(184,125,255,0.04) 100%);
      border-color: rgba(184,125,255,0.3);
      box-shadow: 0 0 20px rgba(184,125,255,0.08);
    }
    .metric-card.amber {
      background: linear-gradient(135deg, rgba(255,171,0,0.12) 0%, rgba(255,171,0,0.04) 100%);
      border-color: rgba(255,171,0,0.3);
      box-shadow: 0 0 20px rgba(255,171,0,0.08);
    }

    .metric-icon-wrap { position: relative; width: 24px; height: 24px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
    .ai-dot { width: 10px; height: 10px; border-radius: 50%; background: #00e676; box-shadow: 0 0 12px #00e676; animation: pulseGlow 1.8s infinite; }
    .ai-ripple { position: absolute; inset: -4px; border-radius: 50%; border: 2px solid rgba(0,230,118,0.4); animation: rippleCircle 2s ease-out infinite; }
    @keyframes rippleCircle {
      0%   { transform: scale(0.6); opacity: 1; }
      100% { transform: scale(1.8); opacity: 0; }
    }

    .metric-content { display: flex; flex-direction: column; gap: 2px; }
    .metric-label {
      font-size: 9px; font-weight: 700; letter-spacing: 1px;
      text-transform: uppercase; opacity: 0.85;
    }
    .metric-card.green  .metric-label { color: #00e676; }
    .metric-card.blue   .metric-label { color: #4f9eff; }
    .metric-card.purple .metric-label { color: #b87dff; }
    .metric-card.amber  .metric-label { color: #ffab00; }

    .metric-val {
      font-size: 17px; font-weight: 800; line-height: 1;
      color: #ffffff;
    }
    .metric-val.mono { font-family: "JetBrains Mono", monospace; }
    .metric-unit { font-size: 10px; font-weight: 600; opacity: 0.7; margin-left: 1px; }

    /* Wave bars */
    .metric-bars { display: flex; align-items: center; gap: 2px; height: 20px; }
    .mbar {
      width: 3px; border-radius: 2px;
      background: #00e676;
      min-height: 3px;
      animation: waveUp 1s ease-in-out infinite alternate;
    }
    .mbar:nth-child(2) { animation-delay: 0.1s; }
    .mbar:nth-child(3) { animation-delay: 0.2s; }
    .mbar:nth-child(4) { animation-delay: 0.15s; }
    .mbar:nth-child(5) { animation-delay: 0.25s; }
    .mbar:nth-child(6) { animation-delay: 0.05s; }
    @keyframes waveUp {
      0%   { transform: scaleY(0.25); opacity: 0.5; }
      100% { transform: scaleY(1); opacity: 1; }
    }

    /* ═══ RIGHT ═══ */
    .nav-right {
      display: flex; align-items: center; gap: 10px;
      flex-shrink: 0; z-index: 1;
    }

    .workspace-tag {
      display: flex; align-items: center; gap: 6px;
      padding: 9px 16px; border-radius: 10px;
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.1);
      font-size: 11.5px; color: rgba(255,255,255,0.7);
      font-weight: 500; transition: all 0.2s;
      cursor: pointer;
    }
    .workspace-tag:hover { color: #fff; border-color: rgba(255,255,255,0.2); background: rgba(255,255,255,0.08); }

    .icon-action {
      width: 42px; height: 42px; border-radius: 12px;
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.1);
      color: rgba(255,255,255,0.5);
      display: flex; align-items: center; justify-content: center;
      cursor: pointer; transition: all 0.2s; position: relative;
    }
    .icon-action:hover { color: #fff; border-color: rgba(184,125,255,0.5); background: rgba(184,125,255,0.1); }
    .action-badge {
      position: absolute; top: 6px; right: 6px;
      width: 7px; height: 7px; border-radius: 50%;
      background: #ff4d9e; box-shadow: 0 0 8px #ff4d9e;
      border: 1.5px solid #0e1220;
    }

    .user-pill {
      display: flex; align-items: center; gap: 10px;
      padding: 8px 16px 8px 8px; border-radius: 14px;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.1);
      cursor: pointer; transition: all 0.2s;
      font-family: inherit; text-align: left;
    }
    .user-pill:hover { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.18); }
    .user-pill:focus-visible {
      outline: 2px solid #b87dff;
      outline-offset: 2px;
    }

    .icon-action:focus-visible {
      outline: 2px solid #b87dff;
      outline-offset: 2px;
    }

    .workspace-tag:focus-visible {
      outline: 2px solid #4f9eff;
      outline-offset: 2px;
      border-radius: 9px;
    }

    .user-avatar {
      width: 40px; height: 40px; border-radius: 50%;
      background: linear-gradient(135deg, #7c3aed, #b87dff);
      display: flex; align-items: center; justify-content: center;
      font-size: 12px; font-weight: 800; color: #fff;
      box-shadow: 0 0 16px rgba(184,125,255,0.35);
      position: relative; flex-shrink: 0;
    }
    .avatar-spin-ring {
      position: absolute; inset: -4px; border-radius: 50%;
      border: 1.5px solid transparent;
      border-top-color: rgba(184,125,255,0.7);
      border-right-color: rgba(184,125,255,0.3);
      animation: orbitSpin 3s linear infinite;
    }
    @keyframes orbitSpin { to { transform: rotate(360deg); } }

    .user-info { display: flex; flex-direction: column; gap: 1px; }
    .user-name { font-size: 13px; font-weight: 700; color: #fff; }
    .user-role { font-size: 10px; color: rgba(255,255,255,0.5); }
  `]
})
export class NavbarComponent implements OnInit, OnDestroy {
  engine      = input<DbEngine>('bigquery');
  sidebarOpen = input<boolean>(false);
  menuToggle  = output<void>();
  bars: number[] = [8, 14, 10, 18, 12, 16, 9, 20, 11, 15, 8, 17];
  queryCount = 47;
  latency = 284;
  private interval?: ReturnType<typeof setInterval>;

  ngOnInit(): void {
    this.interval = setInterval(() => {
      this.bars = this.bars.map(() => Math.floor(Math.random() * 16) + 4);
      if (Math.random() > 0.6) this.queryCount++;
      this.latency = Math.floor(Math.random() * 180) + 150;
    }, 900);
  }
  ngOnDestroy(): void { clearInterval(this.interval); }
}
