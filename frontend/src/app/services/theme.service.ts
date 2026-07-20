// ============================================================
// theme.service.ts — Gerencia modo claro / escuro
// ============================================================
import { Injectable, signal, effect } from '@angular/core';

export type Theme = 'dark' | 'light';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  readonly theme = signal<Theme>('dark');

  constructor() {
    // Persiste preferência no localStorage
    const saved = localStorage.getItem('bob-theme') as Theme | null;
    if (saved === 'light' || saved === 'dark') {
      this.theme.set(saved);
    }

    effect(() => {
      const t = this.theme();
      document.documentElement.setAttribute('data-theme', t);
      localStorage.setItem('bob-theme', t);
    });
  }

  toggle(): void {
    this.theme.update(t => (t === 'dark' ? 'light' : 'dark'));
  }
}
