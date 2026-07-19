export type DocumentStatus = 'PENDING' | 'PROCESSING' | 'INDEXED' | 'ERROR';

export interface DocumentItem {
  id: string;
  original_name: string;
  stored_name: string;
  storage_path: string;
  mime_type: string;
  extension: string;
  size_bytes: number;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
}

export interface DocumentUpdate {
  original_name?: string;
  status?: DocumentStatus;
}
