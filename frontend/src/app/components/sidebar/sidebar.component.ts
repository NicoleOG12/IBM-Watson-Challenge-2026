// ============================================================
// sidebar.component.ts — Neon Dark v4 · Lucide icons
// ============================================================
import { Component, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  LucideAngularModule,
  LUCIDE_ICONS,
  LucideIconProvider,
  BotMessageSquare,
  Database,
  History,
  Star,
  LayoutDashboard,
  FileText,
  NotebookText,
  Settings,
} from 'lucide-angular';

export type NavItem = 'chat' | 'catalog' | 'history' | 'saved-questions' | 'dashboards' | 'reports' | 'logs' | 'settings';

interface NavEntry {
  id: NavItem;
  label: string;
  icon: string;  // nome do ícone Lucide (kebab-case)
  color: 'blue' | 'cyan' | 'purple' | 'amber' | 'green' | 'pink';
  badge?: string;
  live?: boolean;
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  providers: [
    { provide: LUCIDE_ICONS, multi: true, useValue: new LucideIconProvider({ BotMessageSquare, Database, History, Star, LayoutDashboard, FileText, NotebookText, Settings }) },
  ],
  template: `
    <aside class="sidebar" role="navigation" aria-label="Main menu">

      <!-- Decorative — hidden from screen readers -->
      <div class="sb-accent-line" aria-hidden="true"></div>

      <!-- ── NAVIGATION ── -->
      <div class="sb-scroll">
        <nav aria-label="Navigation">
          <div class="sb-section-label" id="nav-nav">Navigation</div>
          <div class="sb-items" role="list" aria-labelledby="nav-nav">
            <button *ngFor="let item of navItems"
                 type="button"
                 role="listitem"
                 class="sb-item"
                 [class.active]="active === item.id"
                 [attr.data-color]="item.color"
                 [attr.aria-current]="active === item.id ? 'page' : null"
                 [attr.aria-label]="item.label + (item.badge ? ', ' + item.badge + ' items' : '') + (item.live ? ', live' : '')"
                 (click)="navigate(item.id)">
              <div class="sb-item-icon" [class]="'ic-' + item.color" aria-hidden="true">
                <lucide-icon [name]="item.icon" [size]="15" [strokeWidth]="1.75"></lucide-icon>
              </div>
              <span class="sb-item-label">{{ item.label }}</span>
              <div class="sb-item-end" aria-hidden="true">
                <span *ngIf="item.live" class="live-dot"></span>
                <span *ngIf="item.badge" class="item-badge" [class]="'bd-' + item.color">{{ item.badge }}</span>
              </div>
            </button>
          </div>
        </nav>

        <div class="sb-divider" aria-hidden="true"></div>

        <nav aria-label="Outputs">
          <div class="sb-section-label" id="nav-outputs">Outputs</div>
          <div class="sb-items" role="list" aria-labelledby="nav-outputs">
            <button *ngFor="let item of outputItems"
                 type="button"
                 role="listitem"
                 class="sb-item"
                 [class.active]="active === item.id"
                 [attr.data-color]="item.color"
                 [attr.aria-current]="active === item.id ? 'page' : null"
                 [attr.aria-label]="item.label + (item.badge ? ', ' + item.badge + ' itens' : '')"
                 (click)="navigate(item.id)">
              <div class="sb-item-icon" [class]="'ic-' + item.color" aria-hidden="true">
                <lucide-icon [name]="item.icon" [size]="15" [strokeWidth]="1.75"></lucide-icon>
              </div>
              <span class="sb-item-label">{{ item.label }}</span>
              <div class="sb-item-end" aria-hidden="true">
                <span *ngIf="item.badge" class="item-badge" [class]="'bd-' + item.color">{{ item.badge }}</span>
              </div>
            </button>
          </div>
        </nav>

        <div class="sb-divider" aria-hidden="true"></div>

        <nav aria-label="System">
          <div class="sb-section-label" id="nav-system">System</div>
          <div class="sb-items" role="list" aria-labelledby="nav-system">
            <button *ngFor="let item of systemItems"
                 type="button"
                 role="listitem"
                 class="sb-item"
                 [class.active]="active === item.id"
                 [attr.data-color]="item.color"
                 [attr.aria-current]="active === item.id ? 'page' : null"
                 [attr.aria-label]="item.label"
                 (click)="navigate(item.id)">
              <div class="sb-item-icon" [class]="'ic-' + item.color" aria-hidden="true">
                <lucide-icon [name]="item.icon" [size]="15" [strokeWidth]="1.75"></lucide-icon>
              </div>
              <span class="sb-item-label">{{ item.label }}</span>
            </button>
          </div>
        </nav>
      </div>

    </aside>
  `,
  styles: [`
    .sidebar {
      width: 234px;
      background: #101420;
      border-right: 1px solid rgba(255,255,255,0.07);
      display: flex; flex-direction: column;
      flex-shrink: 0; height: 100%;
      position: relative; overflow: hidden;
      transition: width 0.25s cubic-bezier(0.4,0,0.2,1), background 0.28s, border-color 0.28s;
    }
    :host-context([data-theme="light"]) .sidebar {
      background: #f0f2f7;
      border-right-color: rgba(0,0,0,0.12);
    }

    /* ── Modo icon-only (tablet 640–1023px) ── */
    @media (min-width: 640px) and (max-width: 1023px) {
      .sidebar { width: 64px; }
      .sb-section-label { display: none; }
      .sb-item-label { display: none; }
      .sb-item-end { display: none; }
      .sb-item { justify-content: center; padding: 10px 0; gap: 0; }
      .sb-item-icon { margin: 0 auto; }
      .sb-divider { margin: 4px 8px; }
      .sb-footer { padding: 10px 8px; }
      .sb-footer-title { display: none; }
      .conn-name { display: none; }
      .conn-ms { display: none; }
      .conn-row { justify-content: center; padding: 6px 0; gap: 0; }
      .sb-scroll { padding: 8px 8px; }
    }

    /* ── Modo drawer mobile (posicionamento via app.css) ── */
    @media (max-width: 639px) {
      .sidebar { width: 240px; }
    }

    /* Linha de acento vertical (colorida) */
    .sb-accent-line {
      position: absolute; left: 0; top: 0; bottom: 0; width: 2px;
      background: linear-gradient(180deg,
        #4f9eff 0%, #b87dff 33%, #00e5ff 66%, #00e676 100%
      );
      opacity: 0.6;
    }

    /* ── Logo ── */
    .sb-logo-area {
      display: flex; align-items: center; gap: 12px;
      padding: 16px 16px 14px 20px;
      border-bottom: 1px solid rgba(255,255,255,0.07);
      flex-shrink: 0;
    }
    .sb-logo-icon {
      width: 36px; height: 36px; border-radius: 10px;
      background: linear-gradient(135deg, #0f1e38, #1a2a4a);
      border: 1px solid rgba(79,158,255,0.3);
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 0 12px rgba(79,158,255,0.15);
    }
    .sb-logo-name {
      font-size: 14px; font-weight: 900; color: #ffffff;
      letter-spacing: 3px; opacity: 0.9;
    }

    /* ── Scroll ── */
    .sb-scroll { flex: 1; overflow-y: auto; padding: 8px 10px 8px 12px; }

    /* ── Section ── */
    .sb-section { margin-bottom: 4px; }
    .sb-section-label {
      font-size: 9.5px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 1.2px; color: rgba(255,255,255,0.35);
      padding: 10px 8px 5px;
    }
    :host-context([data-theme="light"]) .sb-section-label { color: #374151; }
    .sb-items { display: flex; flex-direction: column; gap: 2px; }

    /* ── Item (button reset + estilos) ── */
    .sb-item {
      display: flex; align-items: center; gap: 10px;
      padding: 9px 10px;
      border-radius: 10px;
      cursor: pointer;
      color: rgba(255,255,255,0.55);
      font-size: 13px; font-weight: 500;
      transition: background 0.18s, color 0.18s, border-color 0.18s;
      border: 1px solid transparent;
      position: relative;
      user-select: none;
      /* reset button */
      background: transparent;
      width: 100%;
      text-align: left;
      font-family: inherit;
      outline: none;
    }
    :host-context([data-theme="light"]) .sb-item { color: #111827; }
    .sb-item:focus-visible {
      outline: 2px solid #4f9eff;
      outline-offset: -2px;
      border-radius: 10px;
    }
    .sb-item:hover {
      color: rgba(255,255,255,0.85);
      background: rgba(255,255,255,0.06);
      border-color: rgba(255,255,255,0.08);
    }
    :host-context([data-theme="light"]) .sb-item:hover {
      color: #0f172a;
      background: #d8dff0;
      border-color: rgba(0,0,0,0.12);
    }

    /* Active state: cor diferente para cada item */
    .sb-item.active[data-color="blue"]   { background: rgba(79,158,255,0.14);  border-color: rgba(79,158,255,0.3);   color: #4f9eff;  }
    .sb-item.active[data-color="cyan"]   { background: rgba(0,229,255,0.12);   border-color: rgba(0,229,255,0.3);    color: #00e5ff;  }
    .sb-item.active[data-color="purple"] { background: rgba(184,125,255,0.14); border-color: rgba(184,125,255,0.3);  color: #b87dff;  }
    .sb-item.active[data-color="amber"]  { background: rgba(255,171,0,0.12);   border-color: rgba(255,171,0,0.3);    color: #ffab00;  }
    .sb-item.active[data-color="green"]  { background: rgba(0,230,118,0.12);   border-color: rgba(0,230,118,0.3);    color: #00e676;  }
    .sb-item.active[data-color="pink"]   { background: rgba(255,77,158,0.12);  border-color: rgba(255,77,158,0.3);   color: #ff4d9e;  }

    /* Itens ativos — modo claro: cores vibrantes */
    :host-context([data-theme="light"]) .sb-item.active[data-color="blue"]   { background: rgba(37,99,235,0.12);   border-color: rgba(37,99,235,0.35);   color: #2563eb; }
    :host-context([data-theme="light"]) .sb-item.active[data-color="cyan"]   { background: rgba(8,145,178,0.12);   border-color: rgba(8,145,178,0.35);   color: #0891b2; }
    :host-context([data-theme="light"]) .sb-item.active[data-color="purple"] { background: rgba(124,58,237,0.12);  border-color: rgba(124,58,237,0.35);  color: #7c3aed; }
    :host-context([data-theme="light"]) .sb-item.active[data-color="amber"]  { background: rgba(217,119,6,0.12);   border-color: rgba(217,119,6,0.35);   color: #d97706; }
    :host-context([data-theme="light"]) .sb-item.active[data-color="green"]  { background: rgba(22,163,74,0.12);   border-color: rgba(22,163,74,0.35);   color: #16a34a; }
    :host-context([data-theme="light"]) .sb-item.active[data-color="pink"]   { background: rgba(219,39,119,0.12);  border-color: rgba(219,39,119,0.35);  color: #db2777; }

    /* Indicator bar */
    .sb-item.active::before {
      content: ''; position: absolute;
      left: -1px; top: 20%; bottom: 20%;
      width: 3px; border-radius: 0 3px 3px 0;
    }
    .sb-item.active[data-color="blue"]::before   { background: #4f9eff; box-shadow: 0 0 10px #4f9eff; }
    .sb-item.active[data-color="cyan"]::before   { background: #00e5ff; box-shadow: 0 0 10px #00e5ff; }
    .sb-item.active[data-color="purple"]::before { background: #b87dff; box-shadow: 0 0 10px #b87dff; }
    .sb-item.active[data-color="amber"]::before  { background: #ffab00; box-shadow: 0 0 10px #ffab00; }
    .sb-item.active[data-color="green"]::before  { background: #00e676; box-shadow: 0 0 10px #00e676; }
    .sb-item.active[data-color="pink"]::before   { background: #ff4d9e; box-shadow: 0 0 10px #ff4d9e; }

    /* Indicator bar — modo claro */
    :host-context([data-theme="light"]) .sb-item.active[data-color="blue"]::before   { background: #2563eb; box-shadow: none; }
    :host-context([data-theme="light"]) .sb-item.active[data-color="cyan"]::before   { background: #0891b2; box-shadow: none; }
    :host-context([data-theme="light"]) .sb-item.active[data-color="purple"]::before { background: #7c3aed; box-shadow: none; }
    :host-context([data-theme="light"]) .sb-item.active[data-color="amber"]::before  { background: #d97706; box-shadow: none; }
    :host-context([data-theme="light"]) .sb-item.active[data-color="green"]::before  { background: #16a34a; box-shadow: none; }
    :host-context([data-theme="light"]) .sb-item.active[data-color="pink"]::before   { background: #db2777; box-shadow: none; }

    /* ── Icon wrapper ── */
    .sb-item-icon {
      width: 30px; height: 30px; border-radius: 8px;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0; border: 1px solid rgba(255,255,255,0.07);
      background: rgba(255,255,255,0.04);
      transition: all 0.2s;
    }
    :host-context([data-theme="light"]) .sb-item-icon {
      border-color: rgba(0,0,0,0.12);
      background: #e4e8f2;
    }
    .ic-blue   { color: #4f9eff;  } .sb-item.active[data-color="blue"]   .sb-item-icon { background: rgba(79,158,255,0.18);  border-color: rgba(79,158,255,0.4);  box-shadow: 0 0 12px rgba(79,158,255,0.2); }
    .ic-cyan   { color: #00e5ff;  } .sb-item.active[data-color="cyan"]   .sb-item-icon { background: rgba(0,229,255,0.15);   border-color: rgba(0,229,255,0.4);   box-shadow: 0 0 12px rgba(0,229,255,0.2); }
    .ic-purple { color: #b87dff;  } .sb-item.active[data-color="purple"] .sb-item-icon { background: rgba(184,125,255,0.18); border-color: rgba(184,125,255,0.4); box-shadow: 0 0 12px rgba(184,125,255,0.2); }
    .ic-amber  { color: #ffab00;  } .sb-item.active[data-color="amber"]  .sb-item-icon { background: rgba(255,171,0,0.15);   border-color: rgba(255,171,0,0.4);   box-shadow: 0 0 12px rgba(255,171,0,0.2); }
    .ic-green  { color: #00e676;  } .sb-item.active[data-color="green"]  .sb-item-icon { background: rgba(0,230,118,0.15);   border-color: rgba(0,230,118,0.4);   box-shadow: 0 0 12px rgba(0,230,118,0.2); }
    .ic-pink   { color: #ff4d9e;  } .sb-item.active[data-color="pink"]   .sb-item-icon { background: rgba(255,77,158,0.15);  border-color: rgba(255,77,158,0.4);  box-shadow: 0 0 12px rgba(255,77,158,0.2); }

    /* ── Cores dos ícones no modo claro ── */
    :host-context([data-theme="light"]) .ic-blue   { color: #2563eb; }
    :host-context([data-theme="light"]) .ic-cyan   { color: #0891b2; }
    :host-context([data-theme="light"]) .ic-purple { color: #7c3aed; }
    :host-context([data-theme="light"]) .ic-amber  { color: #d97706; }
    :host-context([data-theme="light"]) .ic-green  { color: #16a34a; }
    :host-context([data-theme="light"]) .ic-pink   { color: #db2777; }

    .sb-item-label { flex: 1; }
    .sb-item-end { display: flex; align-items: center; gap: 5px; }

    /* Live dot */
    .live-dot {
      width: 7px; height: 7px; border-radius: 50%;
      background: #00e676; box-shadow: 0 0 8px #00e676;
      animation: pulseGlow 2s infinite;
    }
    :host-context([data-theme="light"]) .live-dot { background: #16a34a; box-shadow: none; }
    @keyframes pulseGlow { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }

    /* Badge */
    .item-badge {
      font-size: 9px; font-weight: 800; padding: 2px 6px;
      border-radius: 999px; border: 1px solid;
    }
    .bd-blue   { background: rgba(79,158,255,0.15);  color: #4f9eff;  border-color: rgba(79,158,255,0.35); }
    .bd-amber  { background: rgba(255,171,0,0.15);   color: #ffab00;  border-color: rgba(255,171,0,0.35); }
    .bd-cyan   { background: rgba(0,229,255,0.12);   color: #00e5ff;  border-color: rgba(0,229,255,0.3); }
    .bd-green  { background: rgba(0,230,118,0.12);   color: #00e676;  border-color: rgba(0,230,118,0.3); }

    /* Badges — modo claro */
    :host-context([data-theme="light"]) .bd-blue   { background: rgba(37,99,235,0.12);   color: #2563eb; border-color: rgba(37,99,235,0.35); }
    :host-context([data-theme="light"]) .bd-amber  { background: rgba(217,119,6,0.12);   color: #d97706; border-color: rgba(217,119,6,0.35); }
    :host-context([data-theme="light"]) .bd-cyan   { background: rgba(8,145,178,0.12);   color: #0891b2; border-color: rgba(8,145,178,0.30); }
    :host-context([data-theme="light"]) .bd-green  { background: rgba(22,163,74,0.12);   color: #16a34a; border-color: rgba(22,163,74,0.30); }

    /* Divider */
    .sb-divider {
      height: 1px; margin: 6px 8px;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1) 50%, transparent);
    }
    :host-context([data-theme="light"]) .sb-divider {
      background: linear-gradient(90deg, transparent, rgba(0,0,0,0.18) 50%, transparent);
    }

    /* ── Footer ── */
    .sb-footer {
      flex-shrink: 0; padding: 12px 16px 16px;
      border-top: 1px solid rgba(255,255,255,0.07);
      background: rgba(0,0,0,0.2);
      transition: background 0.28s, border-color 0.28s;
    }
    :host-context([data-theme="light"]) .sb-footer {
      border-top-color: rgba(0,0,0,0.12);
      background: #e4e8f2;
    }
    .sb-footer-title {
      font-size: 9.5px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 1px; color: rgba(255,255,255,0.2); margin-bottom: 8px;
    }
    :host-context([data-theme="light"]) .sb-footer-title { color: #374151; }
    .conn-list { display: flex; flex-direction: column; gap: 5px; }
    .conn-row {
      display: flex; align-items: center; gap: 8px;
      padding: 6px 10px; border-radius: 8px;
      border: 1px solid; font-size: 11.5px;
    }
    .conn-row.green { background: rgba(0,230,118,0.06); border-color: rgba(0,230,118,0.2); color: rgba(255,255,255,0.7); }
    .conn-row.amber { background: rgba(255,171,0,0.06);  border-color: rgba(255,171,0,0.2);  color: rgba(255,255,255,0.5); }
    :host-context([data-theme="light"]) .conn-row.green { color: #111827; background: #d1fae5; border-color: rgba(6,95,70,0.30); }
    :host-context([data-theme="light"]) .conn-row.amber { color: #111827; background: #fef3c7; border-color: rgba(120,53,15,0.30); }
    .conn-led {
      width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0;
    }
    .conn-row.green .conn-led { background: #00e676; box-shadow: 0 0 8px #00e676; animation: pulseGlow 2s infinite; }
    .conn-row.amber .conn-led { background: #ffab00; box-shadow: 0 0 6px #ffab00; }
    :host-context([data-theme="light"]) .conn-row.green .conn-led { background: #16a34a; box-shadow: none; }
    :host-context([data-theme="light"]) .conn-row.amber .conn-led { background: #d97706; box-shadow: none; }
    .conn-name { flex: 1; font-weight: 600; color: rgba(255,255,255,0.8); }
    :host-context([data-theme="light"]) .conn-name { color: #050810; }
    .conn-ms {
      font-size: 10px; font-family: "JetBrains Mono", monospace;
      font-weight: 600;
    }
    .conn-row.green .conn-ms { color: #00e676; opacity: 0.9; }
    .conn-row.amber .conn-ms { color: #ffab00; opacity: 0.9; }
    :host-context([data-theme="light"]) .conn-row.green .conn-ms { color: #16a34a; opacity: 1; }
    :host-context([data-theme="light"]) .conn-row.amber .conn-ms { color: #d97706; opacity: 1; }
  `]
})
export class SidebarComponent {
  active: NavItem = 'chat';
  navTo = output<NavItem>();

  navItems: NavEntry[] = [
    { id: 'chat',            label: 'Chat with Bob',  color: 'blue',   live: true,  icon: 'bot-message-square' },
    { id: 'catalog',         label: 'Data Catalog',   color: 'cyan',               icon: 'database' },
    { id: 'history',         label: 'History',        color: 'purple', badge: '12', icon: 'history' },
    { id: 'saved-questions', label: 'Saved Questions', color: 'amber', badge: '5',  icon: 'star' },
  ];

  outputItems: NavEntry[] = [
    { id: 'dashboards', label: 'Dashboards', color: 'green', badge: '3', icon: 'layout-dashboard' },
    { id: 'reports',    label: 'Reports',    color: 'blue',              icon: 'file-text' },
    { id: 'logs',       label: 'Logbook',    color: 'pink',              icon: 'notebook-text' },
  ];

  systemItems: NavEntry[] = [
    { id: 'settings', label: 'Settings', color: 'purple', icon: 'settings' },
  ];

  navigate(item: NavItem): void {
    this.active = item;
    this.navTo.emit(item);
  }
}
