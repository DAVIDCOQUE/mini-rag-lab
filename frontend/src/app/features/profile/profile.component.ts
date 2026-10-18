import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar } from '@angular/material/snack-bar';

import { AssistantGender, AssistantProfile, AssistantProfileUpdate } from '../../core/models/profile.model';
import { ProfileService } from '../../core/services/profile.service';
import { UiPreferencesService } from '../../core/services/ui-preferences.service';

type TextField = Exclude<keyof AssistantProfileUpdate, 'assistant_gender'>;

@Component({
  selector: 'app-profile',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, MatButtonModule, MatButtonToggleModule, MatFormFieldModule, MatIconModule, MatInputModule],
  templateUrl: './profile.component.html',
  styleUrl: './profile.component.scss',
})
export class ProfileComponent {
  private readonly service = inject(ProfileService);
  private readonly snackBar = inject(MatSnackBar);
  readonly ui = inject(UiPreferencesService);

  readonly saved = signal<AssistantProfile | null>(null);
  readonly saving = signal(false);
  readonly loadFailed = signal(false);

  // Borrador editable: se compara con lo guardado para enviar solo lo que cambio.
  draft: Record<TextField, string> = this.emptyDraft();
  gender: AssistantGender = 'FEMININE';

  readonly copy = computed(() =>
    this.ui.locale() === 'es'
      ? {
          eyebrow: 'Perfil del asistente',
          title: 'Quién es y a dónde remite',
          intro:
            'Estos datos solo se usan en textos fijos: la presentación y a dónde ir cuando no hay respuesta. Las respuestas sobre trámites siguen saliendo de los documentos.',
          identity: 'Identidad',
          institution: 'Institución',
          help: 'Atención cuando no hay respuesta',
          helpIntro: 'Se añade al "No encontré información". Lo que quede vacío no se menciona.',
          feminine: 'Femenino (la asistente)',
          masculine: 'Masculino (el asistente)',
          fields: {
            assistant_name: 'Nombre del asistente',
            institution_name: 'Nombre de la institución',
            institution_short_name: 'Nombre corto o sigla',
            city: 'Ciudad',
            website: 'Sitio web',
            help_office: 'Oficina',
            help_location: 'Ubicación',
            help_hours: 'Horario',
            help_phone: 'Teléfono',
            help_email: 'Correo',
          } as Record<TextField, string>,
          save: 'Guardar',
          saved: 'Perfil guardado.',
          saveFailed: 'No se pudo guardar el perfil.',
          nameRequired: 'El asistente necesita un nombre.',
          loadFailed: 'No se pudo cargar el perfil. ¿Está activo el backend?',
        }
      : {
          eyebrow: 'Assistant profile',
          title: 'Who it is and where it refers people',
          intro:
            'Used only in fixed texts: the introduction and where to go when there is no answer. Answers about procedures still come from the documents.',
          identity: 'Identity',
          institution: 'Institution',
          help: 'Help when there is no answer',
          helpIntro: 'Appended to "No information found". Empty fields are not mentioned.',
          feminine: 'Feminine',
          masculine: 'Masculine',
          fields: {
            assistant_name: 'Assistant name',
            institution_name: 'Institution name',
            institution_short_name: 'Short name or acronym',
            city: 'City',
            website: 'Website',
            help_office: 'Office',
            help_location: 'Location',
            help_hours: 'Opening hours',
            help_phone: 'Phone',
            help_email: 'Email',
          } as Record<TextField, string>,
          save: 'Save',
          saved: 'Profile saved.',
          saveFailed: 'Could not save the profile.',
          nameRequired: 'The assistant needs a name.',
          loadFailed: 'Could not load the profile. Is the backend running?',
        }
  );

  readonly institutionFields: TextField[] = ['institution_name', 'institution_short_name', 'city', 'website'];
  readonly helpFields: TextField[] = ['help_office', 'help_location', 'help_hours', 'help_phone', 'help_email'];

  constructor() {
    this.service.get().subscribe({
      next: (profile) => this.load(profile),
      error: () => this.loadFailed.set(true),
    });
  }

  save(): void {
    const profile = this.saved();
    if (!profile || this.saving()) return;
    if (!this.draft.assistant_name.trim()) {
      this.notify(this.copy().nameRequired);
      return;
    }

    const changes: AssistantProfileUpdate = {};
    for (const field of Object.keys(this.draft) as TextField[]) {
      const value = this.draft[field].trim();
      if (value !== (profile[field] ?? '')) changes[field] = value || null;
    }
    if (this.gender !== profile.assistant_gender) changes.assistant_gender = this.gender;
    if (Object.keys(changes).length === 0) return;

    this.saving.set(true);
    this.service.update(changes).subscribe({
      next: (updated) => {
        this.load(updated);
        this.saving.set(false);
        this.notify(this.copy().saved);
      },
      error: (err) => {
        this.saving.set(false);
        this.notify(err?.error?.detail ?? this.copy().saveFailed);
      },
    });
  }

  private load(profile: AssistantProfile): void {
    this.saved.set(profile);
    this.gender = profile.assistant_gender;
    const draft = this.emptyDraft();
    for (const field of Object.keys(draft) as TextField[]) draft[field] = profile[field] ?? '';
    this.draft = draft;
  }

  private emptyDraft(): Record<TextField, string> {
    return {
      assistant_name: '',
      institution_name: '',
      institution_short_name: '',
      city: '',
      website: '',
      help_office: '',
      help_location: '',
      help_hours: '',
      help_phone: '',
      help_email: '',
    };
  }

  private notify(message: string): void {
    this.snackBar.open(message, 'OK', { duration: 3000 });
  }
}
