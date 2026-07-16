// ============================================================
// status-bar.component.ts
// ============================================================
import { Component } from '@angular/core';

@Component({
  selector: 'app-status-bar',
  standalone: true,
  template: `
    <div class="status-bar">
      <span class="sb-item"><span class="sb-dot green"></span>BigQuery conectado</span>
      <span class="sb-item"><span class="sb-dot green"></span>Bob API online</span>
      <span class="sb-item"><span class="sb-dot orange"></span>Redshift (stand-by)</span>
      <span class="sb-right">sessão: sess_9f3a &nbsp;·&nbsp; alex.rodrigues&#64;acme.com &nbsp;·&nbsp; {{ time }}</span>
    </div>
  `,
  styles: [`
    .status-bar {
      background: #161616;
      color: #8d8d8d;
      font-size: 10px;
      padding: 3px 16px;
      display: flex;
      gap: 16px;
      align-items: center;
      flex-shrink: 0;
    }
    .sb-item { display: flex; align-items: center; gap: 4px; }
    .sb-dot {
      width: 6px; height: 6px;
      border-radius: 50%; display: inline-block;
    }
    .sb-dot.green  { background: #24a148; }
    .sb-dot.orange { background: #d97706; }
    .sb-right { margin-left: auto; color: #525252; }
  `],
})
export class StatusBarComponent {
  get time(): string {
    return new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
}
