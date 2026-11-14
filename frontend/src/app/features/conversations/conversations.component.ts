import { DatePipe, DecimalPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBar } from '@angular/material/snack-bar';

import { ChatLogFilters, ChatLogItem, ChatLogStats, ChatRoute } from '../../core/models/chat-log.model';
import { ChatLogService } from '../../core/services/chat-log.service';
import { UiPreferencesService } from '../../core/services/ui-preferences.service';

const PAGE_SIZE = 50;

// Cada camino con un tono del design system; "sin respuesta" usa warn aparte.
const ROUTE_VARIANTS: Record<ChatRoute, string> = {
  institutional: 'info',
  general: 'neutral',
  smalltalk: 'ok',
  off_topic: 'neutral',
};

@Component({
  selector: 'app-conversations',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe,
    DecimalPipe,
    FormsModule,
    MatButtonModule,
    MatButtonToggleModule,
    MatCheckboxModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressBarModule,
  ],
  templateUrl: './conversations.component.html',
  styleUrl: './conversations.component.scss',
})
export class ConversationsComponent {
  private readonly service = inject(ChatLogService);
  private readonly snackBar = inject(MatSnackBar);
  readonly ui = inject(UiPreferencesService);

  readonly items = signal<ChatLogItem[]>([]);
  readonly total = signal(0);
  readonly stats = signal<ChatLogStats | null>(null);
  readonly retentionDays = signal<number | null>(null);
  readonly loading = signal(false);
  readonly expanded = signal<string | null>(null);

  // Filtros: ngModel en el template, aplicados al pulsar Buscar o al cambiar camino/check.
  route: ChatRoute | '' = '';
  noAnswer = false;
  q = '';
  dateFrom = '';
  dateTo = '';

  readonly hasMore = computed(() => this.items().length < this.total());

  readonly copy = computed(() =>
    this.ui.locale() === 'es'
      ? {
          summaryLabel: 'Resumen',
          metrics: {
            total: 'Mensajes',
            conversations: 'Conversaciones',
            noAnswer: 'Sin respuesta',
            forms: 'Formatos entregados',
            median: 'Tiempo mediano',
          },
          refresh: 'Recargar',
          export: 'Exportar CSV',
          search: 'Buscar en las preguntas',
          apply: 'Buscar',
          clear: 'Limpiar filtros',
          all: 'Todas',
          routes: {
            institutional: 'Institucional',
            general: 'General',
            smalltalk: 'Charla',
            off_topic: 'Fuera de tema',
          } as Record<ChatRoute, string>,
          onlyNoAnswer: 'Solo sin respuesta',
          from: 'Desde',
          to: 'Hasta',
          noAnswerBadge: 'Sin respuesta',
          offered: 'Ofreció',
          delivered: 'Entregó',
          turn: (n: number) => (n === 0 ? 'Inicio' : `Turno ${n + 1}`),
          answer: 'Respuesta',
          searchedWith: 'Se buscó con',
          score: 'Puntaje del mejor fragmento',
          timings: 'Tiempos',
          router: 'Router',
          routing: 'router',
          retrieval: 'recuperación',
          generation: 'generación',
          loadMore: 'Cargar más',
          showing: (shown: number, total: number) => `${shown} de ${total}`,
          empty: 'No hay mensajes con estos filtros.',
          emptyAll: 'Todavía no hay conversaciones. Aparecerán aquí cuando alguien use el chat.',
          privacy: (days: number) =>
            `Los datos personales (cédulas, correos, teléfonos) se ocultan al guardar y los mensajes se borran solos a los ${days} días.`,
          loadFailed: 'No se pudo cargar el log de conversaciones.',
          toastAction: 'Cerrar',
        }
      : {
          summaryLabel: 'Summary',
          metrics: {
            total: 'Messages',
            conversations: 'Conversations',
            noAnswer: 'No answer',
            forms: 'Forms delivered',
            median: 'Median time',
          },
          refresh: 'Reload',
          export: 'Export CSV',
          search: 'Search the questions',
          apply: 'Search',
          clear: 'Clear filters',
          all: 'All',
          routes: {
            institutional: 'Institutional',
            general: 'General',
            smalltalk: 'Small talk',
            off_topic: 'Off topic',
          } as Record<ChatRoute, string>,
          onlyNoAnswer: 'Only unanswered',
          from: 'From',
          to: 'To',
          noAnswerBadge: 'No answer',
          offered: 'Offered',
          delivered: 'Delivered',
          turn: (n: number) => (n === 0 ? 'Start' : `Turn ${n + 1}`),
          answer: 'Answer',
          searchedWith: 'Searched with',
          score: 'Best chunk score',
          timings: 'Timings',
          router: 'Router',
          routing: 'routing',
          retrieval: 'retrieval',
          generation: 'generation',
          loadMore: 'Load more',
          showing: (shown: number, total: number) => `${shown} of ${total}`,
          empty: 'No messages match these filters.',
          emptyAll: 'No conversations yet. They will show up here once someone uses the chat.',
          privacy: (days: number) =>
            `Personal data (IDs, emails, phone numbers) is hidden when saved, and messages are deleted after ${days} days.`,
          loadFailed: 'Could not load the conversation log.',
          toastAction: 'Dismiss',
        },
  );

  readonly metrics = computed(() => {
    const stats = this.stats();
    const labels = this.copy().metrics;
    if (!stats) return [];
    const rate = stats.total ? Math.round((stats.no_answer / stats.total) * 100) : 0;
    return [
      { key: 'total', label: labels.total, value: `${stats.total}`, tone: 'neutral' },
      { key: 'conversations', label: labels.conversations, value: `${stats.conversations}`, tone: 'neutral' },
      {
        key: 'no-answer',
        label: labels.noAnswer,
        value: stats.no_answer ? `${stats.no_answer} · ${rate}%` : '0',
        tone: stats.no_answer ? 'warn' : 'ok',
      },
      { key: 'forms', label: labels.forms, value: `${stats.forms_delivered}`, tone: 'info' },
      {
        key: 'median',
        label: labels.median,
        value: stats.median_ms === null ? '—' : `${(stats.median_ms / 1000).toFixed(1)} s`,
        tone: 'neutral',
      },
    ];
  });

  readonly routeOptions: ChatRoute[] = ['institutional', 'general', 'smalltalk', 'off_topic'];

  constructor() {
    this.load();
  }

  load(): void {
    this.fetch(0);
  }

  loadMore(): void {
    this.fetch(this.items().length);
  }

  clearFilters(): void {
    this.route = '';
    this.noAnswer = false;
    this.q = '';
    this.dateFrom = '';
    this.dateTo = '';
    this.load();
  }

  exportCsv(): void {
    this.service.exportCsv(this.filters()).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `conversaciones-sara-${new Date().toISOString().slice(0, 10)}.csv`;
        link.click();
        URL.revokeObjectURL(url);
      },
      error: () => this.snackBar.open(this.copy().loadFailed, this.copy().toastAction, { duration: 3000 }),
    });
  }

  toggle(item: ChatLogItem): void {
    this.expanded.update((id) => (id === item.id ? null : item.id));
  }

  routeLabel(route: ChatRoute): string {
    return this.copy().routes[route] ?? route;
  }

  routeVariant(route: ChatRoute): string {
    return ROUTE_VARIANTS[route] ?? 'neutral';
  }

  seconds(ms: number | null): string {
    return ms === null ? '—' : `${(ms / 1000).toFixed(1)} s`;
  }

  private filters(): ChatLogFilters {
    return {
      route: this.route || null,
      noAnswer: this.noAnswer,
      q: this.q,
      dateFrom: this.dateFrom,
      dateTo: this.dateTo,
    };
  }

  private fetch(offset: number): void {
    this.loading.set(true);
    this.service.list(this.filters(), PAGE_SIZE, offset).subscribe({
      next: (page) => {
        this.items.set(offset === 0 ? page.items : [...this.items(), ...page.items]);
        this.total.set(page.total);
        this.stats.set(page.stats);
        this.retentionDays.set(page.retention_days);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.snackBar.open(this.copy().loadFailed, this.copy().toastAction, { duration: 3000 });
      },
    });
  }
}
