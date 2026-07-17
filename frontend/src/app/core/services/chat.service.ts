import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';

import { environment } from '../../../environments/environment';
import { ChatMessage, ChatRole } from '../models/chat-message.model';

interface ChatApiResponse {
  response: string;
}

const OLLAMA_ERROR = 'No fue posible conectar con Ollama.';

@Injectable({ providedIn: 'root' })
export class ChatService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  private readonly _messages = signal<ChatMessage[]>([]);
  private readonly _loading = signal(false);

  // Estado expuesto (solo lectura) para los componentes.
  readonly messages = this._messages.asReadonly();
  readonly loading = this._loading.asReadonly();
  readonly hasMessages = computed(() => this._messages().length > 0);

  sendMessage(content: string): void {
    const text = content.trim();
    if (!text || this._loading()) return;

    this.append('user', text);
    this._loading.set(true);

    this.http.post<ChatApiResponse>(`${this.baseUrl}/api/chat`, { message: text }).subscribe({
      next: (res) => {
        this.append('assistant', res.response);
        this._loading.set(false);
      },
      error: () => {
        // No exponer detalles tecnicos: solo un mensaje amigable.
        this.append('assistant', OLLAMA_ERROR);
        this._loading.set(false);
      },
    });
  }

  clearConversation(): void {
    this._messages.set([]);
  }

  private append(role: ChatRole, content: string): void {
    const message: ChatMessage = {
      id: crypto.randomUUID(),
      role,
      content,
      createdAt: new Date(),
    };
    this._messages.update((list) => [...list, message]);
  }
}
