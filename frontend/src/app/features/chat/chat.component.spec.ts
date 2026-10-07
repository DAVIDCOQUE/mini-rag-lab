import { computed, signal } from '@angular/core';
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';

import { ChatMessage } from '../../core/models/chat-message.model';
import { ChatService } from '../../core/services/chat.service';
import { ChatComponent } from './chat.component';

class FakeChatService {
  readonly messages = signal<ChatMessage[]>([]);
  readonly loading = signal(false);
  readonly error = signal(null);
  readonly hasMessages = computed(() => this.messages().length > 0);
  readonly canRetry = signal(false);

  clearConversation = jasmine.createSpy('clearConversation').and.callFake(() => this.messages.set([]));
  sendMessage = jasmine.createSpy('sendMessage');
  stop = jasmine.createSpy('stop');
  retry = jasmine.createSpy('retry');
}

const MESSAGE: ChatMessage = { id: '1', role: 'user', content: 'hola', createdAt: new Date() };

describe('ChatComponent · inactividad del quiosco', () => {
  let fixture: ComponentFixture<ChatComponent>;
  let component: ChatComponent;
  let chat: FakeChatService;

  beforeEach(() => {
    chat = new FakeChatService();
    TestBed.configureTestingModule({
      imports: [ChatComponent],
      providers: [{ provide: ChatService, useValue: chat }],
    });
    fixture = TestBed.createComponent(ChatComponent);
    component = fixture.componentInstance;
  });

  function startWith(messages: ChatMessage[]): void {
    chat.messages.set(messages);
    fixture.detectChanges();
  }

  it('avisa tras 60 s sin actividad y borra al terminar la cuenta atras', fakeAsync(() => {
    startWith([MESSAGE]);

    tick(60_000);
    expect(component.idleCountdown()).toBe(10);

    tick(10_000);
    expect(chat.clearConversation).toHaveBeenCalled();
    expect(component.idleCountdown()).toBeNull();
  }));

  it('cualquier toque cancela el aviso y reinicia el contador', fakeAsync(() => {
    startWith([MESSAGE]);
    tick(60_000);
    expect(component.idleCountdown()).toBe(10);

    component.onActivity(new Event('pointerdown'));
    expect(component.idleCountdown()).toBeNull();

    tick(59_000);
    expect(component.idleCountdown()).toBeNull();
    tick(1_000);
    expect(component.idleCountdown()).toBe(10);

    component.clear();
  }));

  it('la pantalla de espera no caduca', fakeAsync(() => {
    startWith([]);

    tick(120_000);
    expect(component.idleCountdown()).toBeNull();
    expect(chat.clearConversation).not.toHaveBeenCalled();
  }));

  it('lo escrito sin enviar tambien cuenta como conversacion y se borra', fakeAsync(() => {
    startWith([]);
    component.draft = 'una pregunta a medias';
    component.onActivity(new Event('keydown'));

    tick(70_000);
    expect(chat.clearConversation).toHaveBeenCalled();
    expect(component.draft).toBe('');
  }));

  it('el contador esta en pausa mientras el asistente responde', fakeAsync(() => {
    startWith([MESSAGE]);
    chat.loading.set(true);
    fixture.detectChanges();

    tick(120_000);
    expect(component.idleCountdown()).toBeNull();

    chat.loading.set(false);
    fixture.detectChanges();
    tick(60_000);
    expect(component.idleCountdown()).toBe(10);

    component.clear();
  }));
});
