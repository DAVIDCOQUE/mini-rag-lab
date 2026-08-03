export interface SearchResultItem {
  document_id: string;
  page: number;
  chunk_index: number;
  content: string;
  score: number;
}

// Coste de cada etapa del flujo, en milisegundos.
export interface SearchTimings {
  retrieval_ms: number;
  generation_ms: number | null;
  total_ms: number;
}

export interface SearchResponse {
  query: string;
  total: number;
  results: SearchResultItem[];
  timings: SearchTimings;
  answer: string | null;
  generation_skipped: boolean;
  prompt_code: string | null;
}
