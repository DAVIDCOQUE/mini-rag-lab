import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';

import { SearchResultItem } from '../../core/models/search.model';
import { SearchService } from '../../core/services/search.service';
import { UiPreferencesService } from '../../core/services/ui-preferences.service';

@Component({
  selector: 'app-search',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, MatButtonModule, MatIconModule, MatProgressBarModule],
  templateUrl: './search.component.html',
  styleUrl: './search.component.scss',
})
export class SearchComponent {
  private readonly service = inject(SearchService);
  readonly ui = inject(UiPreferencesService);

  query = '';
  readonly loading = signal(false);
  readonly searched = signal(false);
  readonly results = signal<SearchResultItem[]>([]);
  readonly lastQuery = signal('');

  readonly copy = computed(() => {
    const locale = this.ui.locale();

    return locale === 'es'
      ? {
          eyebrow: 'Búsqueda semántica',
          headline: 'Busca por significado, no por nombre de archivo.',
          placeholder: 'Pregunta por conceptos, cláusulas, pasos o definiciones…',
          submit: 'Buscar',
          clear: 'Limpiar la búsqueda',
          suggestions: 'Prueba con',
          idle: 'Escribe una consulta para recuperar los chunks más relevantes del corpus indexado.',
          noResults: 'Sin coincidencias para esta consulta. Indexa más documentos o prueba con un concepto más específico.',
          resultsLabel: 'Resultados',
          relevance: 'Relevancia',
          page: 'Página',
          chunk: 'chunk',
          document: 'Documento',
          quickQueries: [
            'Resume el último documento indexado',
            'Chunks sobre onboarding o uso de API',
            'Fuentes relacionadas con el tema actual',
          ],
        }
      : {
          eyebrow: 'Semantic search',
          headline: 'Search by meaning, not by filename.',
          placeholder: 'Ask about concepts, clauses, steps or definitions…',
          submit: 'Search',
          clear: 'Clear the search',
          suggestions: 'Try',
          idle: 'Type a query to retrieve the most relevant chunks from the indexed corpus.',
          noResults: 'No matches for this query. Index more documents or try a more specific concept.',
          resultsLabel: 'Results',
          relevance: 'Relevance',
          page: 'Page',
          chunk: 'chunk',
          document: 'Document',
          quickQueries: [
            'Summarize the latest indexed document',
            'Chunks about onboarding or API usage',
            'Sources related to the current topic',
          ],
        };
  });

  search(): void {
    const text = this.query.trim();
    if (!text || this.loading()) return;

    this.loading.set(true);
    this.lastQuery.set(text);
    this.service.search(text).subscribe({
      next: (res) => {
        this.results.set(res.results);
        this.searched.set(true);
        this.loading.set(false);
      },
      error: () => {
        this.results.set([]);
        this.searched.set(true);
        this.loading.set(false);
      },
    });
  }

  // Una sugerencia ejecuta la busqueda: pulsarla y volver a pulsar Buscar seria
  // un paso de mas para lo que ya es una intencion explicita.
  runSuggestion(prompt: string): void {
    this.query = prompt;
    this.search();
  }

  clear(): void {
    this.query = '';
    this.results.set([]);
    this.searched.set(false);
    this.lastQuery.set('');
  }

  scorePercent(score: number): number {
    return Math.round(score * 100);
  }
}
