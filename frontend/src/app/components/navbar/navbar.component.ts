// ============================================================
// navbar.component.ts
// ============================================================
import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import type { DbEngine } from '../../models/copilot.models';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule],
  template: `
    <!-- ── TOP NAVIGATION ── -->
    <!-- Component: NavbarComponent -->
    <nav class="topnav">
      <div class="topnav-brand">
        <div class="logo">IBM</div>
        <strong>Bob</strong>
        <span>/ Corporate Data Copilot</span>
      </div>
      <div class="topnav-right">
        <!-- badge reflete o engine ativo, recebe sinal do AppComponent -->
        <span class="badge-env">{{ engine() }}</span>
        <span class="workspace">workspace: acme-corp-prod</span>
        <div class="avatar">AR</div>
      </div>
    </nav>
  `,
  styles: [`
    .topnav {
      background: #161616;
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 20px;
      height: 48px;
      flex-shrink: 0;
      border-bottom: 1px solid #393939;
    }
    .topnav-brand { display: flex; align-items: center; gap: 10px; }
    .logo {
      background: #3b82d4;
      color: #fff;
      font-weight: 700;
      font-size: 13px;
      padding: 3px 8px;
      border-radius: 3px;
      letter-spacing: 0.5px;
    }
    .topnav-brand span { font-size: 14px; color: #c6c6c6; }
    .topnav-brand strong { font-size: 15px; }
    .topnav-right { display: flex; align-items: center; gap: 16px; }
    .badge-env {
      background: #24a148;
      color: #fff;
      font-size: 10px;
      padding: 2px 8px;
      border-radius: 10px;
      letter-spacing: 0.4px;
      text-transform: uppercase;
    }
    .workspace { color: #8d8d8d; font-size: 12px; }
    .avatar {
      width: 28px; height: 28px;
      background: #7c5cd8;
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 11px; color: #fff; font-weight: 600;
    }
  `],
})
export class NavbarComponent {
  engine = input<DbEngine>('bigquery');
}
