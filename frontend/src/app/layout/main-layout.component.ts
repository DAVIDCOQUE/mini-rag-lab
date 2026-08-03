import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  computed,
  inject,
  signal,
} from '@angular/core';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { catchError, filter, of, switchMap, timer } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { HealthService } from '../core/services/health.service';
import { UiPreferencesService } from '../core/services/ui-preferences.service';

interface NavItem {
  path: string;
  label: string;
  icon: string;
  description: string;
}

interface ServiceState {
  label: string;
  state: 'up' | 'down' | 'unknown';
}

// Cadencia del indicador ambiental de estado. Un indicador permanente que no se
// refresca miente: 30s es suficiente para notar una caida sin castigar al backend.
const HEALTH_POLL_MS = 30_000;

@Component({
  selector: 'app-main-layout',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatSidenavModule,
    MatIconModule,
    MatButtonModule,
  ],
  templateUrl: './main-layout.component.html',
  styleUrl: './main-layout.component.scss',
})
export class MainLayoutComponent {
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  private readonly health = inject(HealthService);
  readonly ui = inject(UiPreferencesService);

  readonly compact = signal(false);
  readonly mobileNavOpen = signal(false);
  readonly currentPath = signal('/home');
  // Separa el chrome del contenido solo cuando este pasa por debajo.
  readonly scrolled = signal(false);

  readonly version = signal<string | null>(null);
  readonly services = signal<ServiceState[]>([
    { label: 'PostgreSQL', state: 'unknown' },
    { label: 'Qdrant', state: 'unknown' },
    { label: 'Ollama', state: 'unknown' },
  ]);

  readonly sidenavMode = computed(() => (this.compact() ? 'over' : 'side'));
  readonly sidenavOpened = computed(() => (this.compact() ? this.mobileNavOpen() : true));

  readonly navItems = computed<NavItem[]>(() => {
    const locale = this.ui.locale();

    return locale === 'es'
      ? [
          {
            path: '/home',
            label: 'Inicio',
            icon: 'space_dashboard',
            description: 'Estado del workspace',
          },
          {
            path: '/chat',
            label: 'Estudio',
            icon: 'chat_bubble',
            description: 'Conversación con contexto',
          },
          {
            path: '/documents',
            label: 'Biblioteca',
            icon: 'folder_open',
            description: 'Documentos e indexación',
          },
          {
            path: '/search',
            label: 'Explorar',
            icon: 'manage_search',
            description: 'Búsqueda semántica',
          },
          {
            path: '/prompts',
            label: 'Prompts',
            icon: 'tune',
            description: 'Comportamiento del agente',
          },
        ]
      : [
          {
            path: '/home',
            label: 'Overview',
            icon: 'space_dashboard',
            description: 'Workspace health',
          },
          {
            path: '/chat',
            label: 'Studio',
            icon: 'chat_bubble',
            description: 'Grounded conversation',
          },
          {
            path: '/documents',
            label: 'Library',
            icon: 'folder_open',
            description: 'Documents and indexing',
          },
          {
            path: '/search',
            label: 'Explore',
            icon: 'manage_search',
            description: 'Semantic search',
          },
          {
            path: '/prompts',
            label: 'Prompts',
            icon: 'tune',
            description: 'Agent behaviour',
          },
        ];
  });

  readonly activeItem = computed(() => {
    const path = this.currentPath();
    return this.navItems().find((item) => path.startsWith(item.path)) ?? this.navItems()[0];
  });

  readonly chrome = computed(() => {
    const locale = this.ui.locale();
    const theme = this.ui.theme();

    return locale === 'es'
      ? {
          tagline: 'Workspace de IA',
          navLabel: 'Navegar',
          systemLabel: 'Sistema',
          language: 'ES',
          languageHint: 'Cambiar a inglés',
          theme: theme === 'dark' ? 'Oscuro' : 'Claro',
          themeHint: theme === 'dark' ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro',
          navToggle: 'Mostrar u ocultar la navegación',
          offline: 'Backend sin respuesta',
          checking: 'Comprobando servicios…',
        }
      : {
          tagline: 'AI Workspace',
          navLabel: 'Navigate',
          systemLabel: 'System',
          language: 'EN',
          languageHint: 'Switch to Spanish',
          theme: theme === 'dark' ? 'Dark' : 'Light',
          themeHint: theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme',
          navToggle: 'Show or hide navigation',
          offline: 'Backend unreachable',
          checking: 'Checking services…',
        };
  });

  readonly systemSummary = computed(() => {
    const services = this.services();
    if (services.every((service) => service.state === 'unknown')) return this.chrome().checking;
    if (services.every((service) => service.state === 'down')) return this.chrome().offline;

    const up = services.filter((service) => service.state === 'up').length;
    return `${up}/${services.length} · v${this.version() ?? '—'}`;
  });

  constructor() {
    this.syncViewportState();
    this.syncRouteState(this.router.url);

    this.router.events
      .pipe(
        filter((event): event is NavigationEnd => event instanceof NavigationEnd),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe((event) => {
        this.syncRouteState(event.urlAfterRedirects);
        this.scrolled.set(false);
        if (this.compact()) {
          this.mobileNavOpen.set(false);
        }
      });

    timer(0, HEALTH_POLL_MS)
      .pipe(
        switchMap(() => this.health.check().pipe(catchError(() => of(null)))),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe((response) => {
        this.version.set(response?.version ?? null);
        this.services.set([
          { label: 'PostgreSQL', state: toServiceState(response?.database) },
          { label: 'Qdrant', state: toServiceState(response?.qdrant) },
          { label: 'Ollama', state: toServiceState(response?.ollama) },
        ]);
      });
  }

  onContentScroll(event: Event): void {
    this.scrolled.set((event.target as HTMLElement).scrollTop > 4);
  }

  toggleNav(): void {
    if (this.compact()) {
      this.mobileNavOpen.update((value) => !value);
      return;
    }

    this.mobileNavOpen.set(false);
    this.compact.update((value) => !value);
  }

  closeNavOnMobile(): void {
    if (this.compact()) {
      this.mobileNavOpen.set(false);
    }
  }

  toggleLocale(): void {
    this.ui.toggleLocale();
  }

  toggleTheme(): void {
    this.ui.toggleTheme();
  }

  private syncRouteState(url: string): void {
    this.currentPath.set(url.split('?')[0] ?? '/home');
  }

  private syncViewportState(): void {
    if (typeof window === 'undefined') {
      return;
    }

    const query = window.matchMedia('(max-width: 959px)');
    const update = (): void => {
      this.compact.set(query.matches);
      if (!query.matches) {
        this.mobileNavOpen.set(false);
      }
    };

    update();
    query.addEventListener('change', update);
    this.destroyRef.onDestroy(() => query.removeEventListener('change', update));
  }
}

function toServiceState(value: string | undefined): ServiceState['state'] {
  if (!value) return 'down';
  return value === 'connected' ? 'up' : 'down';
}
