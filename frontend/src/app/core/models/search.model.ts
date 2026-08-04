export interface SearchResultItem {
  document_id: string;
  page: number;
  chunk_index: number;
  content: string;
  score: number;
}

// Coste de cada etapa, en milisegundos. Nulo lo que no llegó a ocurrir.
export interface SearchTimings {
  routing_ms: number | null;
  retrieval_ms: number | null;
  generation_ms: number | null;
  total_ms: number;
}

// Camino elegido por el router. Solo institutional consulta la base vectorial.
export type SearchRoute = 'institutional' | 'general' | 'smalltalk' | 'off_topic';

export interface SearchResponse {
  query: string;
  total: number;
  results: SearchResultItem[];
  timings: SearchTimings;
  answer: string | null;
  generation_skipped: boolean;
  prompt_code: string | null;
  route: SearchRoute | null;
  route_scores: Record<string, number>;
}
