import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  computed,
  effect,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

import { ChatService } from '../../core/services/chat.service';
import { UiPreferencesService } from '../../core/services/ui-preferences.service';

// Margen dentro del cual se considera que el usuario sigue el final del hilo.
// Por encima de esto esta leyendo historial y no se le arrastra el scroll.
const PIN_THRESHOLD_PX = 120;

// Cuanto permanece la confirmacion de copiado. Suficiente para leerla sin
// convertirse en un estado que el usuario tenga que esperar.
const COPIED_FEEDBACK_MS = 1600;

// En el quiosco no hay forma de saber que el estudiante se fue: tras este tiempo sin
// tocar nada se pregunta, y si nadie responde la conversacion se borra para el siguiente.
const IDLE_TIMEOUT_MS = 60_000;
const IDLE_COUNTDOWN_S = 10;

@Component({
  selector: 'app-chat',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, MatButtonModule, MatIconModule],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss',
  host: {
    '(document:pointerdown)': 'onActivity($event)',
    '(document:keydown)': 'onActivity($event)',
    '(document:wheel)': 'onActivity($event)',
  },
})
export class ChatComponent {
  private readonly chat = inject(ChatService);
  private readonly destroyRef = inject(DestroyRef);
  readonly ui = inject(UiPreferencesService);

  readonly messages = this.chat.messages;
  readonly loading = this.chat.loading;
  readonly hasMessages = this.chat.hasMessages;
  readonly error = this.chat.error;
  readonly canRetry = this.chat.canRetry;

  draft = '';

  // Id del mensaje cuya copia se acaba de confirmar.
  readonly copiedId = signal<string | null>(null);

  // Segundos que quedan antes de borrar la conversacion; null sin aviso en pantalla.
  readonly idleCountdown = signal<number | null>(null);

  private pinnedToBottom = true;
  private copiedTimer: ReturnType<typeof setTimeout> | null = null;
  private idleTimer: ReturnType<typeof setTimeout> | null = null;
  private countdownTimer: ReturnType<typeof setInterval> | null = null;

  readonly copy = computed(() => {
    const locale = this.ui.locale();

    return locale === 'es'
      ? {
          clear: 'Terminar conversación',
          conversation: 'Conversación',
          hint: 'Enter para enviar · Shift+Enter para nueva línea',
          empty: 'Hola, ¿en qué te puedo ayudar?',
          emptyHint: 'O empieza por una de las sugerencias del panel derecho.',
          placeholder: 'Pregunta sobre documentos, fuentes o próximos pasos…',
          send: 'Enviar mensaje',
          stop: 'Detener la generación',
          retry: 'Reintentar',
          copy: 'Copiar mensaje',
          copied: 'Copiado',
          thinking: 'Pensando…',
          you: 'Tú',
          idleTitle: '¿Sigues ahí?',
          idleBody: (seconds: number) => `La conversación se borrará en ${seconds} s.`,
          stay: 'Sigo aquí',
          model: 'IA',
          errors: {
            unreachable: 'No se pudo obtener respuesta del modelo. Comprueba que Ollama esté activo.',
            cancelled: 'Generación detenida.',
          },
          mode: 'Modo',
          modeTitle: 'Chat con contexto',
          modeBody:
            'Verifica hipótesis, refina prompts y compara respuestas contra la biblioteca indexada.',
          prompts: 'Sugerencias',
          promptItems: [
            'Resume el último documento indexado.',
            'Compara dos chunks relacionados.',
            'Explica por qué devolvió este resultado.',
          ],
          workflow: 'Flujo',
          workflowSteps: [
            { icon: 'library_books', text: 'Extraer contexto desde la biblioteca.' },
            { icon: 'travel_explore', text: 'Rastrear la evidencia de cada respuesta.' },
          ],
        }
      : {
          clear: 'End conversation',
          conversation: 'Conversation',
          hint: 'Enter to send · Shift+Enter for a new line',
          empty: 'Hi, how can I help you?',
          emptyHint: 'Or start from one of the suggestions on the right.',
          placeholder: 'Ask about documents, sources or next steps…',
          send: 'Send message',
          stop: 'Stop generating',
          retry: 'Retry',
          copy: 'Copy message',
          copied: 'Copied',
          thinking: 'Thinking…',
          you: 'You',
          idleTitle: 'Are you still there?',
          idleBody: (seconds: number) => `This conversation will be cleared in ${seconds} s.`,
          stay: "I'm still here",
          model: 'AI',
          errors: {
            unreachable: 'Could not get a reply from the model. Check that Ollama is running.',
            cancelled: 'Generation stopped.',
          },
          mode: 'Mode',
          modeTitle: 'Grounded chat',
          modeBody:
            'Verify hypotheses, refine prompts and compare answers against the indexed library.',
          prompts: 'Suggested prompts',
          promptItems: [
            'Summarize the latest indexed document.',
            'Compare two related chunks.',
            'Explain why a result was returned.',
          ],
          workflow: 'Workflow',
          workflowSteps: [
            { icon: 'library_books', text: 'Pull context from the library.' },
            { icon: 'travel_explore', text: 'Trace the evidence behind each answer.' },
          ],
        };
  });

  readonly errorMessage = computed(() => {
    const kind = this.error();
    return kind ? this.copy().errors[kind] : null;
  });

  // Una cancelacion es informativa; un fallo real merece tono de error.
  readonly errorIsFailure = computed(() => this.error() === 'unreachable');

  private readonly scrollContainer = viewChild<ElementRef<HTMLElement>>('scrollContainer');
  private readonly composer = viewChild('composer', { read: ElementRef<HTMLTextAreaElement> });

  constructor() {
    effect(() => {
      this.messages();
      this.loading();
      this.error();

      // Solo se sigue el hilo si el usuario ya estaba al final.
      if (!this.pinnedToBottom) return;

      const el = this.scrollContainer()?.nativeElement;
      if (el) {
        // Salto instantaneo: el hilo avanza decenas de veces por sesion, animarlo
        // seria ruido (y ademas competiria con la entrada del mensaje).
        setTimeout(() => (el.scrollTop = el.scrollHeight));
      }
    });

    // Mientras el asistente responde la inactividad no corre: una respuesta tarda hasta ~18 s.
    effect(() => {
      if (this.loading()) this.clearIdle();
      else this.armIdle();
    });

    this.destroyRef.onDestroy(() => {
      if (this.copiedTimer) clearTimeout(this.copiedTimer);
      this.clearIdle();
    });
  }

  onMessagesScroll(event: Event): void {
    const el = event.target as HTMLElement;
    const distanceToBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    this.pinnedToBottom = distanceToBottom <= PIN_THRESHOLD_PX;
  }

  send(): void {
    const text = this.draft.trim();
    if (!text || this.loading()) return;

    // Enviar siempre devuelve al usuario al final del hilo.
    this.pinnedToBottom = true;
    this.chat.sendMessage(text);
    this.draft = '';
  }

  stop(): void {
    this.chat.stop();
  }

  retry(): void {
    this.pinnedToBottom = true;
    this.chat.retry();
  }

  // Borra todo lo del estudiante actual, incluido lo escrito sin enviar.
  clear(): void {
    this.clearIdle();
    this.chat.clearConversation();
    this.draft = '';
    this.pinnedToBottom = true;
  }

  stay(): void {
    this.armIdle();
  }

  onActivity(event: Event): void {
    // Los botones del aviso tienen su propia accion; reiniciar aqui los desmontaria
    // antes de que llegue el click.
    if ((event.target as Element | null)?.closest?.('.idle-dialog')) return;
    if (this.loading()) return;
    this.armIdle();
  }

  private armIdle(): void {
    this.clearIdle();
    this.idleTimer = setTimeout(() => this.startCountdown(), IDLE_TIMEOUT_MS);
  }

  private startCountdown(): void {
    // La pantalla de espera no caduca: solo se avisa si hay algo que borrar.
    if (!this.hasMessages() && !this.draft.trim()) return;

    this.idleCountdown.set(IDLE_COUNTDOWN_S);
    this.countdownTimer = setInterval(() => {
      const left = (this.idleCountdown() ?? 0) - 1;
      if (left <= 0) this.clear();
      else this.idleCountdown.set(left);
    }, 1000);
  }

  private clearIdle(): void {
    if (this.idleTimer) clearTimeout(this.idleTimer);
    if (this.countdownTimer) clearInterval(this.countdownTimer);
    this.idleTimer = null;
    this.countdownTimer = null;
    this.idleCountdown.set(null);
  }

  usePrompt(prompt: string): void {
    this.draft = prompt;
    this.composer()?.nativeElement.focus();
  }

  async copyMessage(message: { id: string; content: string }): Promise<void> {
    try {
      await navigator.clipboard.writeText(message.content);
    } catch {
      // Sin permiso de portapapeles no hay nada que confirmar.
      return;
    }

    if (this.copiedTimer) clearTimeout(this.copiedTimer);
    this.copiedId.set(message.id);
    this.copiedTimer = setTimeout(() => this.copiedId.set(null), COPIED_FEEDBACK_MS);
  }

  onKeydown(event: KeyboardEvent): void {
    // Enter envia; Shift+Enter inserta salto de linea.
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.send();
    }
  }
}
