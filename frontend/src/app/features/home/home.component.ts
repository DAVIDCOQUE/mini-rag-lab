import { ChangeDetectionStrategy, Component, computed, inject, signal, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { HealthService } from '../../core/services/health.service';
import { HealthResponse } from '../../core/models/health.model';
import { UiPreferencesService } from '../../core/services/ui-preferences.service';

type ConnectionState = 'loading' | 'ok' | 'error';

@Component({
  selector: 'app-home',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, MatIconModule, MatButtonModule, MatProgressSpinnerModule],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss',
})
export class HomeComponent implements OnInit {
  private readonly healthService = inject(HealthService);
  readonly ui = inject(UiPreferencesService);

  readonly state = signal<ConnectionState>('loading');
  readonly health = signal<HealthResponse | null>(null);
  readonly detail = signal<string>('');

  readonly copy = computed(() => {
    const locale = this.ui.locale();

    return locale === 'es'
      ? {
          eyebrow: 'Inicio',
          headline: 'Del documento a la respuesta, en una sola superficie.',
          body: 'Ingesta, indexación, búsqueda semántica y conversación fundamentada. Un único recorrido pensado para uso diario.',
          primary: 'Abrir biblioteca',
          secondary: 'Abrir estudio',
          statusLabel: 'Estado',
          checking: 'Comprobando el workspace…',
          connected: 'Backend conectado',
          servicesLabel: 'Servicios',
          connectedValue: 'conectado',
          pathLabel: 'Recorrido',
        }
      : {
          eyebrow: 'Overview',
          headline: 'From document to answer, on one surface.',
          body: 'Ingestion, indexing, semantic search and grounded conversation. A single path built for daily use.',
          primary: 'Open library',
          secondary: 'Open studio',
          statusLabel: 'Status',
          checking: 'Checking the workspace…',
          connected: 'Backend connected',
          servicesLabel: 'Services',
          connectedValue: 'connected',
          pathLabel: 'Path',
        };
  });

  readonly overviewCards = computed(() => {
    const locale = this.ui.locale();

    return locale === 'es'
      ? [
          {
            step: '01',
            label: 'Ingesta',
            title: 'Biblioteca',
            description: 'Sube PDFs, procésalos y promuévelos al corpus buscable.',
            icon: 'folder_open',
            route: '/documents',
          },
          {
            step: '02',
            label: 'Recuperación',
            title: 'Explorar',
            description: 'Busca por significado y compara la relevancia de cada chunk.',
            icon: 'manage_search',
            route: '/search',
          },
          {
            step: '03',
            label: 'Razonamiento',
            title: 'Estudio',
            description: 'Conversa con el modelo sobre la evidencia recuperada.',
            icon: 'chat_bubble',
            route: '/chat',
          },
        ]
      : [
          {
            step: '01',
            label: 'Ingest',
            title: 'Library',
            description: 'Upload PDFs, process them and promote them into the searchable corpus.',
            icon: 'folder_open',
            route: '/documents',
          },
          {
            step: '02',
            label: 'Retrieve',
            title: 'Explore',
            description: 'Search by meaning and compare how relevant each chunk is.',
            icon: 'manage_search',
            route: '/search',
          },
          {
            step: '03',
            label: 'Reason',
            title: 'Studio',
            description: 'Talk to the model about the evidence it retrieved.',
            icon: 'chat_bubble',
            route: '/chat',
          },
        ];
  });

  readonly services = computed(() => {
    const health = this.health();
    if (!health) return [];

    return [
      { label: 'PostgreSQL', value: health.database },
      { label: 'Qdrant', value: health.qdrant },
      { label: 'Ollama', value: health.ollama },
    ];
  });

  ngOnInit(): void {
    this.healthService.check().subscribe({
      next: (res) => {
        this.state.set('ok');
        this.health.set(res);
        this.detail.set(`${res.service} · v${res.version}`);
      },
      error: () => {
        this.state.set('error');
        this.detail.set(
          this.ui.locale() === 'es'
            ? 'No se pudo conectar con el backend. Comprueba que uvicorn esté corriendo.'
            : 'Could not reach the backend. Check that uvicorn is running.'
        );
      },
    });
  }

  isUp(value: string): boolean {
    return value === 'connected';
  }
}
