import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

import { DefaultPrompt, PromptTemplate } from '../../core/models/prompt.model';
import { PromptService } from '../../core/services/prompt.service';
import { UiPreferencesService } from '../../core/services/ui-preferences.service';

// Codigo reservado del prompt del repositorio; el backend usa el mismo.
const DEFAULT_CODE = 'default';

@Component({
  selector: 'app-prompts',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, MatButtonModule, MatIconModule],
  templateUrl: './prompts.component.html',
  styleUrl: './prompts.component.scss',
})
export class PromptsComponent {
  private readonly service = inject(PromptService);
  readonly ui = inject(UiPreferencesService);

  readonly templates = signal<PromptTemplate[]>([]);
  readonly defaultPrompt = signal<DefaultPrompt | null>(null);

  // Variante abierta en el editor; null significa que se esta creando una nueva.
  readonly editing = signal<PromptTemplate | null>(null);
  readonly saving = signal(false);
  readonly errorKey = signal<'duplicate' | 'invalid' | 'unreachable' | null>(null);
  // Borrar es destructivo: se confirma en la propia fila en lugar de en un dialogo.
  readonly pendingDelete = signal<string | null>(null);

  draftCode = '';
  draftName = '';
  draftBody = '';

  readonly activeCode = computed(
    () => this.templates().find((template) => template.is_active)?.code ?? DEFAULT_CODE
  );
  readonly isCreating = computed(() => this.editing() === null);

  readonly copy = computed(() => {
    const locale = this.ui.locale();

    return locale === 'es'
      ? {
          eyebrow: 'Comportamiento del agente',
          headline: 'Las instrucciones que recibe el modelo antes de tu pregunta.',
          variants: 'Variantes',
          newVariant: 'Nueva variante',
          activeBadge: 'En uso',
          activate: 'Usar esta',
          useDefault: 'Volver al del repositorio',
          defaultLabel: 'Prompt por defecto',
          defaultHint:
            'Vive en el código y no se puede editar aquí. Es el que se usa cuando ninguna variante está en uso.',
          useAsBase: 'Copiar como base',
          editorNew: 'Nueva variante',
          editorEdit: 'Editando',
          codeLabel: 'Código',
          codeHint: 'Identificador estable: minúsculas, dígitos y guiones. No se puede cambiar después.',
          nameLabel: 'Nombre',
          bodyLabel: 'Instrucciones',
          placeholderMarker: 'Escribe {no_answer} donde quieras la frase de “no encontré nada”.',
          save: 'Guardar',
          cancel: 'Cancelar',
          delete: 'Eliminar',
          confirmDelete: '¿Eliminar?',
          confirmYes: 'Sí, eliminar',
          confirmNo: 'No',
          empty: 'Todavía no hay variantes. El sistema usa el prompt del repositorio.',
          errors: {
            duplicate: 'Ya existe una variante con ese código.',
            invalid: 'Revisa el código (minúsculas, dígitos y guiones) y que las instrucciones tengan al menos 20 caracteres.',
            unreachable: 'No se pudo guardar. Comprueba que el backend esté activo.',
          },
        }
      : {
          eyebrow: 'Agent behaviour',
          headline: 'The instructions the model receives before your question.',
          variants: 'Variants',
          newVariant: 'New variant',
          activeBadge: 'In use',
          activate: 'Use this one',
          useDefault: 'Back to the repository one',
          defaultLabel: 'Default prompt',
          defaultHint:
            'It lives in the code and cannot be edited here. It is used whenever no variant is in use.',
          useAsBase: 'Copy as a base',
          editorNew: 'New variant',
          editorEdit: 'Editing',
          codeLabel: 'Code',
          codeHint: 'Stable identifier: lowercase, digits and dashes. It cannot be changed later.',
          nameLabel: 'Name',
          bodyLabel: 'Instructions',
          placeholderMarker: 'Write {no_answer} wherever you want the “nothing found” sentence.',
          save: 'Save',
          cancel: 'Cancel',
          delete: 'Delete',
          confirmDelete: 'Delete?',
          confirmYes: 'Yes, delete',
          confirmNo: 'No',
          empty: 'No variants yet. The system uses the repository prompt.',
          errors: {
            duplicate: 'A variant with that code already exists.',
            invalid: 'Check the code (lowercase, digits and dashes) and that the instructions are at least 20 characters.',
            unreachable: 'Could not save. Check that the backend is running.',
          },
        };
  });

  readonly errorMessage = computed(() => {
    const key = this.errorKey();
    return key ? this.copy().errors[key] : null;
  });

  // Metodo y no computed: los campos del formulario son propiedades de ngModel, no
  // signals, asi que un computed se quedaria con el primer valor que leyo.
  canSave(): boolean {
    return this.draftName.trim().length >= 2 && this.draftBody.trim().length >= 20;
  }

  constructor() {
    this.load();
    this.service.getDefault().subscribe({ next: (res) => this.defaultPrompt.set(res) });
  }

  load(): void {
    this.service.list().subscribe({ next: (res) => this.templates.set(res) });
  }

  startNew(): void {
    this.editing.set(null);
    this.errorKey.set(null);
    this.draftCode = '';
    this.draftName = '';
    this.draftBody = '';
  }

  edit(template: PromptTemplate): void {
    this.editing.set(template);
    this.errorKey.set(null);
    this.draftCode = template.code;
    this.draftName = template.name;
    this.draftBody = template.body;
  }

  // Partir del prompt del repositorio es el camino normal: se ajusta una regla en
  // lugar de escribir veinte desde cero.
  useDefaultAsBase(): void {
    const base = this.defaultPrompt();
    if (!base) return;

    this.startNew();
    this.draftBody = base.body;
  }

  save(): void {
    if (!this.canSave() || this.saving()) return;

    this.saving.set(true);
    this.errorKey.set(null);

    const current = this.editing();
    const request = current
      ? this.service.update(current.code, {
          name: this.draftName.trim(),
          body: this.draftBody,
        })
      : this.service.create({
          code: this.draftCode.trim(),
          name: this.draftName.trim(),
          body: this.draftBody,
        });

    request.subscribe({
      next: (saved) => {
        this.saving.set(false);
        this.load();
        this.edit(saved);
      },
      error: (response: { status?: number }) => {
        this.saving.set(false);
        if (response.status === 409) this.errorKey.set('duplicate');
        else if (response.status === 422) this.errorKey.set('invalid');
        else this.errorKey.set('unreachable');
      },
    });
  }

  activate(template: PromptTemplate): void {
    this.service.activate(template.code).subscribe({ next: () => this.load() });
  }

  activateDefault(): void {
    this.service.activateDefault().subscribe({ next: () => this.load() });
  }

  askDelete(template: PromptTemplate): void {
    this.pendingDelete.set(template.code);
  }

  cancelDelete(): void {
    this.pendingDelete.set(null);
  }

  confirmDelete(template: PromptTemplate): void {
    this.service.remove(template.code).subscribe({
      next: () => {
        this.pendingDelete.set(null);
        if (this.editing()?.code === template.code) this.startNew();
        this.load();
      },
    });
  }
}
