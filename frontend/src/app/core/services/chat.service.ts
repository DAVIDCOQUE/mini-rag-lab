import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Subscription } from 'rxjs';

import { environment } from '../../../environments/environment';
import { ChatMessage, ChatRole } from '../models/chat-message.model';

interface ChatApiResponse {
  response: string;
}

// El servicio expone la clase de fallo, no un texto: la traduccion es cosa de la
// vista, que si conoce el idioma activo.
export type ChatErrorKind = 'unreachable' | 'cancelled';

@Injectable({ providedIn: 'root' })
export class ChatService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  private readonly _messages = signal<ChatMessage[]>([]);
  private readonly _loading = signal(false);
  private readonly _error = signal<ChatErrorKind | null>(null);

  // Peticion en vuelo: permite cancelarla desde la UI.
  private pending: Subscription | null = null;
  private lastPrompt = '';

  // Estado expuesto (solo lectura) para los componentes.
  readonly messages = this._messages.asReadonly();
  readonly loading = this._loading.asReadonly();
  readonly error = this._error.asReadonly();
  readonly hasMessages = computed(() => this._messages().length > 0);
  readonly canRetry = computed(() => this._error() !== null && this.lastPrompt !== '');

  sendMessage(content: string): void {
    const text = content.trim();
    if (!text || this._loading()) return;

    this.append('user', text);
    this.lastPrompt = text;
    this.request(text);
  }

  retry(): void {
    if (!this.lastPrompt || this._loading()) return;
    this.request(this.lastPrompt);
  }

  // Cancelar aborta el XHR: al desuscribirse, HttpClient cierra la peticion.
  stop(): void {
    if (!this.pending) return;

    this.pending.unsubscribe();
    this.pending = null;
    this._loading.set(false);
    this._error.set('cancelled');
  }

  clearConversation(): void {
    this.stop();
    this._messages.set([]);
    this._error.set(null);
    this.lastPrompt = '';
  }

  private request(text: string): void {
    this._error.set(null);
    this._loading.set(true);

    this.pending = this.http
      .post<ChatApiResponse>(`${this.baseUrl}/api/chat`, { message: text })
      .subscribe({
        next: (res) => {
          this.append('assistant', res.response);
          this.settle();
        },
        error: () => {
          // Un fallo es estado del sistema, no un turno del modelo: no se inventa
          // un mensaje del asistente que el usuario podria citar como respuesta.
          this._error.set('unreachable');
          this.settle();
        },
      });
  }

  private settle(): void {
    this.pending = null;
    this._loading.set(false);
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
