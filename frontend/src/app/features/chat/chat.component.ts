import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  effect,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { TextFieldModule } from '@angular/cdk/text-field';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

import { ChatService } from '../../core/services/chat.service';

@Component({
  selector: 'app-chat',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, TextFieldModule, MatButtonModule, MatIconModule],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss',
})
export class ChatComponent {
  private readonly chat = inject(ChatService);

  readonly messages = this.chat.messages;
  readonly loading = this.chat.loading;
  readonly hasMessages = this.chat.hasMessages;

  draft = '';

  private readonly scrollContainer = viewChild<ElementRef<HTMLElement>>('scrollContainer');

  constructor() {
    // Scroll automatico al final cuando cambian los mensajes o aparece "Escribiendo...".
    effect(() => {
      this.messages();
      this.loading();
      const el = this.scrollContainer()?.nativeElement;
      if (el) {
        setTimeout(() => (el.scrollTop = el.scrollHeight));
      }
    });
  }

  send(): void {
    const text = this.draft.trim();
    if (!text || this.loading()) return;
    this.chat.sendMessage(text);
    this.draft = '';
  }

  clear(): void {
    this.chat.clearConversation();
  }

  onKeydown(event: KeyboardEvent): void {
    // Enter envia; Shift+Enter inserta salto de linea.
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.send();
    }
  }
}
