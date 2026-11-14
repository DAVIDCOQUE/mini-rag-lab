export type ChatRole = 'user' | 'assistant';

// Formato descargable que acompaña a una respuesta; en el quiosco se muestra como QR.
export interface ChatDownload {
  filename: string;
  url: string;
  // Imagen del QR generada por el backend.
  qr_url: string;
}

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: Date;
  downloads?: ChatDownload[];
}
