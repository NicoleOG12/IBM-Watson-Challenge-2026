// ============================================================
// sidebar.component.ts
// ============================================================
import { Component, output } from '@angular/core';
import { CommonModule } from '@angular/common';

export type NavItem = 'chat' | 'catalog' | 'history' | 'saved-questions' | 'dashboards' | 'reports' | 'logs' | 'settings';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule],
  template: `
    <!-- ── SIDEBAR ── -->
    <!-- Rotas planejadas: cada item emite navTo para o AppComponent ou RouterLink -->
    <aside class="sidebar">

      <div class="sidebar-section">
        <div class="sidebar-label">Navegação</div>

        <!-- Route: /chat (default) -->
        <div class="sidebar-item" [class.active]="active === 'chat'" (click)="navigate('chat')">
          <svg class="icon" viewBox="0 0 16 16" fill="currentColor"><path d="M2 2h12v10H8.5l-3 2.5V12H2z"/></svg>
          Chat com Bob
          <span class="dot"></span>
        </div>

        <!-- Route: /catalog | GET /api/catalog/tables -->
        <div class="sidebar-item" [class.active]="active === 'catalog'" (click)="navigate('catalog')">
          <svg class="icon" viewBox="0 0 16 16" fill="currentColor"><path d="M1 3h14v2H1zm0 4h14v2H1zm0 4h14v2H1z"/></svg>
          Catálogo de Dados
        </div>

        <!-- Route: /history | GET /api/queries/history?userId=&limit=50 -->
        <div class="sidebar-item" [class.active]="active === 'history'" (click)="navigate('history')">
          <svg class="icon" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm.5 4v4.25l3 1.75-.5.87-3.5-2.03V5h1z"/></svg>
          Histórico
        </div>

        <!-- Route: /saved-questions | GET /api/questions/saved?userId= -->
        <div class="sidebar-item" [class.active]="active === 'saved-questions'" (click)="navigate('saved-questions')">
          <svg class="icon" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1l2 4.5L15 6l-3.5 3.5.8 5L8 12l-4.3 2.5.8-5L1 6l5-.5z"/></svg>
          Perguntas Prontas
        </div>
      </div>

      <hr class="divider" />

      <div class="sidebar-section">
        <div class="sidebar-label">Outputs Gerados</div>

        <!-- Route: /outputs/dashboards | GET /api/outputs?type=dashboard&userId= -->
        <div class="sidebar-item" [class.active]="active === 'dashboards'" (click)="navigate('dashboards')">
          <svg class="icon" viewBox="0 0 16 16" fill="currentColor"><path d="M1 1h6v6H1zm8 0h6v6H9zM1 9h6v6H1zm8 0h6v6H9z"/></svg>
          Dashboards
        </div>

        <!-- Route: /outputs/reports | GET /api/outputs?type=report&userId= -->
        <div class="sidebar-item" [class.active]="active === 'reports'" (click)="navigate('reports')">
          <svg class="icon" viewBox="0 0 16 16" fill="currentColor"><path d="M3 1h10l2 2v12H1V3zm2 4h8v1H5zm0 3h8v1H5zm0 3h5v1H5z"/></svg>
          Relatórios
        </div>

        <!-- Route: /outputs/logs | GET /api/outputs?type=logbook&userId= -->
        <div class="sidebar-item" [class.active]="active === 'logs'" (click)="navigate('logs')">
          <svg class="icon" viewBox="0 0 16 16" fill="currentColor"><path d="M2 1h9l3 3v11H2V1zm5 5H4v1h3zm6 0H8v1h5zm-6 3H4v1h3zm6 0H8v1h5z"/></svg>
          Diário de Bordo
        </div>
      </div>

      <hr class="divider" />

      <div class="sidebar-section">
        <div class="sidebar-label">Admin</div>
        <!-- Route: /settings | GET/PUT /api/settings/database-connections -->
        <div class="sidebar-item" [class.active]="active === 'settings'" (click)="navigate('settings')">
          <svg class="icon" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1a3 3 0 100 6 3 3 0 000-6zM3 10c0-2 2.5-3 5-3s5 1 5 3v1H3v-1z"/></svg>
          Configurações
        </div>
      </div>

      <div class="sidebar-footer">
        <div class="footer-label">Fontes conectadas:</div>
        <span class="db-tag">BigQuery</span>
        <span class="db-tag">Redshift</span>
        <span class="db-tag">S3</span>
      </div>
    </aside>
  `,
  styles: [`
    .sidebar {
      width: 220px;
      background: #fff;
      border-right: 1px solid #e5e7eb;
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
      overflow-y: auto;
      height: 100%;
    }
    .sidebar-section { padding: 14px 14px 6px; }
    .sidebar-label {
      font-size: 10px; color: #57606a;
      text-transform: uppercase; letter-spacing: 0.6px;
      margin-bottom: 6px; font-weight: 600;
    }
    .sidebar-item {
      display: flex; align-items: center; gap: 8px;
      padding: 7px 10px; border-radius: 5px;
      cursor: pointer; color: #1f2328; font-size: 13px;
      margin-bottom: 1px; transition: background 0.15s;
      user-select: none;
    }
    .sidebar-item:hover { background: #f7f8fa; }
    .sidebar-item.active { background: #eff4ff; color: #3b82d4; font-weight: 500; }
    .icon { width: 16px; height: 16px; flex-shrink: 0; }
    .dot {
      width: 6px; height: 6px; border-radius: 50%;
      background: #24a148; margin-left: auto;
    }
    .divider { border: none; border-top: 1px solid #e5e7eb; margin: 8px 0; }
    .sidebar-footer {
      margin-top: auto; padding: 12px 14px;
      border-top: 1px solid #e5e7eb;
      font-size: 11px; color: #57606a;
    }
    .footer-label { margin-bottom: 5px; }
    .db-tag {
      display: inline-block;
      background: #f7f8fa; border: 1px solid #e5e7eb;
      border-radius: 3px; padding: 1px 5px;
      font-size: 10px; margin-right: 4px; margin-bottom: 3px;
      color: #3b82d4;
    }
  `],
})
export class SidebarComponent {
  active: NavItem = 'chat';
  navTo = output<NavItem>();

  navigate(item: NavItem): void {
    this.active = item;
    this.navTo.emit(item);
  }
}
