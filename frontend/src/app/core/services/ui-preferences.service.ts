import { DOCUMENT } from '@angular/common';
import { effect, inject, Injectable, signal } from '@angular/core';

export type UiLocale = 'en' | 'es';
export type UiTheme = 'dark' | 'light';

@Injectable({ providedIn: 'root' })
export class UiPreferencesService {
  private readonly document = inject(DOCUMENT);

  readonly locale = signal<UiLocale>(this.readLocale());
  readonly theme = signal<UiTheme>(this.readTheme());

  constructor() {
    effect(() => {
      const root = this.document.documentElement;
      const locale = this.locale();
      const theme = this.theme();

      root.setAttribute('lang', locale);
      root.setAttribute('data-theme', theme);

      if (typeof window !== 'undefined') {
        window.localStorage.setItem('mini-rag-lab.locale', locale);
        window.localStorage.setItem('mini-rag-lab.theme', theme);
      }
    });
  }

  toggleLocale(): void {
    this.locale.update((value) => (value === 'en' ? 'es' : 'en'));
  }

  toggleTheme(): void {
    this.theme.update((value) => (value === 'dark' ? 'light' : 'dark'));
  }

  private readLocale(): UiLocale {
    if (typeof window === 'undefined') return 'en';

    return window.localStorage.getItem('mini-rag-lab.locale') === 'es' ? 'es' : 'en';
  }

  private readTheme(): UiTheme {
    if (typeof window === 'undefined') return 'dark';

    return window.localStorage.getItem('mini-rag-lab.theme') === 'light' ? 'light' : 'dark';
  }
}
