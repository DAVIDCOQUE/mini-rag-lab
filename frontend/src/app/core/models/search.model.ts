export interface SearchResultItem {
  document_id: string;
  page: number;
  chunk_index: number;
  content: string;
  score: number;
}

export interface SearchResponse {
  query: string;
  total: number;
  results: SearchResultItem[];
}
