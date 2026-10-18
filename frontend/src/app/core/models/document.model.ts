export type DocumentStatus = 'PENDING' | 'PROCESSING' | 'INDEXED' | 'ERROR';

// KNOWLEDGE: el asistente responde con el. FORM: formato en blanco que se descarga
// por QR y nunca se indexa.
export type DocumentKind = 'KNOWLEDGE' | 'FORM';

export interface DocumentItem {
  id: string;
  original_name: string;
  stored_name: string;
  storage_path: string;
  mime_type: string;
  extension: string;
  size_bytes: number;
  status: DocumentStatus;
  kind: DocumentKind;
  // Para que sirve el formato; con ella se decide cuando ofrecerlo.
  description: string | null;
  // Codigo impreso en el formato (p. ej. R-GA004); opcional.
  form_code: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentUpdate {
  original_name?: string;
  status?: DocumentStatus;
  kind?: DocumentKind;
  description?: string | null;
  form_code?: string | null;
}

export interface ChunkResult {
  index: number;
  page: number;
  characters: number;
  content: string;
}

export interface ProcessingResult {
  document_id: string;
  total_pages: number;
  total_characters: number;
  total_chunks: number;
  chunks: ChunkResult[];
}

export interface IndexResult {
  document_id: string;
  total_chunks: number;
  status: DocumentStatus;
}

export interface IndexedChunks {
  document_id: string;
  total_chunks: number;
  chunks: ChunkResult[];
}
