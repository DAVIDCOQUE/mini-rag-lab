export type ChatRoute = 'institutional' | 'general' | 'smalltalk' | 'off_topic';

export interface ChatLogItem {
  id: string;
  created_at: string;
  conversation_id: string | null;
  // 0 = primer mensaje de la conversacion.
  turn: number;
  // Texto con cedulas, correos y telefonos ya enmascarados por el backend.
  question: string;
  answer: string;
  route: ChatRoute;
  router: string | null;
  search_query: string | null;
  top_score: number | null;
  no_answer: boolean;
  offered_forms: string | null;
  delivered_forms: string | null;
  prompt_code: string | null;
  routing_ms: number | null;
  retrieval_ms: number | null;
  generation_ms: number | null;
  total_ms: number;
}

export interface ChatLogStats {
  total: number;
  no_answer: number;
  forms_delivered: number;
  median_ms: number | null;
  conversations: number;
  by_route: Partial<Record<ChatRoute, number>>;
}

export interface ChatLogPage {
  total: number;
  items: ChatLogItem[];
  stats: ChatLogStats;
  retention_days: number;
}

export interface ChatLogFilters {
  route?: ChatRoute | null;
  noAnswer?: boolean;
  q?: string;
  dateFrom?: string;
  dateTo?: string;
}
