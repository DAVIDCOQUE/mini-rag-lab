import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';

import { PromptTemplate } from '../../core/models/prompt.model';
import { SearchResultItem, SearchTimings } from '../../core/models/search.model';
import { PromptService } from '../../core/services/prompt.service';
import { SearchService } from '../../core/services/search.service';
import { UiPreferencesService } from '../../core/services/ui-preferences.service';

// Codigo reservado del prompt del repositorio; el backend usa el mismo.
const DEFAULT_CODE = 'default';

@Component({
  selector: 'app-search',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, MatButtonModule, MatIconModule, MatProgressBarModule],
  templateUrl: './search.component.html',
  styleUrl: './search.component.scss',
})
export class SearchComponent {
  private readonly service = inject(SearchService);
  private readonly prompts = inject(PromptService);
  readonly ui = inject(UiPreferencesService);

  query = '';
  readonly loading = signal(false);
  readonly searched = signal(false);
  readonly results = signal<SearchResultItem[]>([]);
  readonly lastQuery = signal('');

  // Respuesta del LLM sobre los chunks recuperados y coste de cada etapa: en esta
  // superficie el flujo RAG se ve completo, no solo la recuperacion.
  readonly answer = signal<string | null>(null);
  readonly generationSkipped = signal(false);
  readonly timings = signal<SearchTimings | null>(null);

  // Con que instrucciones se genera la respuesta de esta consulta. Cambiarlo aqui
  // no toca la variante activa: es una prueba puntual, no una decision del sistema.
  readonly promptOptions = signal<PromptTemplate[]>([]);
  readonly selectedPrompt = signal<string>(DEFAULT_CODE);
  readonly usedPrompt = signal<string | null>(null);

  constructor() {
    this.prompts.list().subscribe({
      next: (list) => {
        this.promptOptions.set(list);
        // Arrancar por la que el sistema usaria de verdad evita comparar contra algo
        // que el chat no esta usando.
        this.selectedPrompt.set(list.find((item) => item.is_active)?.code ?? DEFAULT_CODE);
      },
    });
  }

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
          working: 'Recuperando chunks y generando la respuesta…',
          answerLabel: 'Respuesta generada',
          contextLabel: 'Chunks usados como contexto',
          retrievalTime: 'Recuperación',
          generationTime: 'Generación',
          totalTime: 'Total',
          skipped:
            'No se llamó al modelo: el mejor chunk no alcanzó el umbral de relevancia, así que se devolvió el fallback sin gastar una generación.',
          promptLabel: 'Instrucciones',
          promptDefault: 'Por defecto',
          promptUsed: 'Generada con',
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
          working: 'Retrieving chunks and generating the answer…',
          answerLabel: 'Generated answer',
          contextLabel: 'Chunks used as context',
          retrievalTime: 'Retrieval',
          generationTime: 'Generation',
          totalTime: 'Total',
          skipped:
            'The model was not called: the top chunk did not reach the relevance threshold, so the fallback was returned without spending a generation.',
          promptLabel: 'Instructions',
          promptDefault: 'Default',
          promptUsed: 'Generated with',
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
    this.answer.set(null);
    this.generationSkipped.set(false);
    this.timings.set(null);
    this.usedPrompt.set(null);

    // generate: true — el backend recupera y genera en la misma llamada, y devuelve
    // el tiempo de cada etapa por separado.
    this.service.search(text, 5, true, this.selectedPrompt()).subscribe({
      next: (res) => {
        this.results.set(res.results);
        this.answer.set(res.answer);
        this.generationSkipped.set(res.generation_skipped);
        this.timings.set(res.timings);
        this.usedPrompt.set(res.prompt_code);
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
    this.answer.set(null);
    this.generationSkipped.set(false);
    this.timings.set(null);
  }

  // Con el reranker activo el score es un logit del cross-encoder: sin techo y con
  // negativos. Multiplicarlo por 100 producia "115%" y "-269%". El valor crudo es el
  // dato real y ademas se compara de un vistazo con el umbral de CHAT_MIN_SCORE.
  formatScore(score: number): string {
    return `${score >= 0 ? '+' : ''}${score.toFixed(2)}`;
  }

  // La barra solo orienta, asi que el logit se comprime a 0-1 con una sigmoide. No es
  // una probabilidad: es una escala monotona para poder comparar barras entre si.
  scoreBar(score: number): number {
    return 1 / (1 + Math.exp(-score));
  }

  // Por debajo del segundo los milisegundos son la unidad legible; por encima,
  // leer "9857 ms" cuesta mas que leer "9.9 s".
  formatDuration(ms: number): string {
    return ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`;
  }
}
