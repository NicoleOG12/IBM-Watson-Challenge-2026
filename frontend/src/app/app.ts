// ============================================================
// app.ts — Shell da aplicação
// ============================================================
import { Component, signal, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  LucideAngularModule,
  LUCIDE_ICONS,
  LucideIconProvider,
  Menu,
  BotMessageSquare,
  Database,
  History,
} from 'lucide-angular';

import { NavbarComponent }     from './components/navbar/navbar.component';
import { SidebarComponent, NavItem } from './components/sidebar/sidebar.component';
import { ChatComponent }       from './components/chat/chat.component';
import { RightPanelComponent } from './components/right-panel/right-panel.component';
import { StatusBarComponent }  from './components/status-bar/status-bar.component';
import type { DbEngine } from './models/copilot.models';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    LucideAngularModule,
    NavbarComponent,
    SidebarComponent,
    ChatComponent,
    RightPanelComponent,
    StatusBarComponent,
  ],
  providers: [
    { provide: LUCIDE_ICONS, multi: true, useValue: new LucideIconProvider({ Menu, BotMessageSquare, Database, History }) },
  ],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  engine      = signal<DbEngine>('bigquery');
  activeNav   = signal<NavItem>('chat');
  sidebarOpen = signal(false);

  onNavChange(item: NavItem): void {
    this.activeNav.set(item);
    // fecha o drawer no mobile ao navegar
    this.sidebarOpen.set(false);
  }

  toggleSidebar(): void {
    this.sidebarOpen.update(v => !v);
  }

  closeSidebar(): void {
    this.sidebarOpen.set(false);
  }

  // fecha o sidebar ao pressionar Escape
  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.sidebarOpen.set(false);
  }
}
