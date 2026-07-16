// ============================================================
// app.ts — Shell da aplicação
// ============================================================
import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

import { NavbarComponent }    from './components/navbar/navbar.component';
import { SidebarComponent, NavItem } from './components/sidebar/sidebar.component';
import { ChatComponent }      from './components/chat/chat.component';
import { RightPanelComponent } from './components/right-panel/right-panel.component';
import { StatusBarComponent } from './components/status-bar/status-bar.component';
import type { DbEngine } from './models/copilot.models';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    NavbarComponent,
    SidebarComponent,
    ChatComponent,
    RightPanelComponent,
    StatusBarComponent,
  ],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  engine = signal<DbEngine>('bigquery');
  activeNav = signal<NavItem>('chat');

  onNavChange(item: NavItem): void {
    this.activeNav.set(item);
    // Em produção: RouterLink ou this.router.navigate([item])
    // Atualmente a única "página" montada é /chat (app-chat)
  }
}
