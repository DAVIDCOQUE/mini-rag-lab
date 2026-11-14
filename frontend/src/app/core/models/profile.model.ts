export type AssistantGender = 'FEMININE' | 'MASCULINE';

// Identidad del asistente y datos de la institucion. Una sola ficha: solo alimenta
// textos fijos (presentacion y a donde remitir).
export interface AssistantProfile {
  id: string;
  assistant_name: string;
  assistant_gender: AssistantGender;
  institution_name: string | null;
  institution_short_name: string | null;
  city: string | null;
  website: string | null;
  help_office: string | null;
  help_location: string | null;
  help_hours: string | null;
  help_phone: string | null;
  help_email: string | null;
  updated_at: string;
}

// null vacia un campo; el backend rechaza dejar el asistente sin nombre.
export type AssistantProfileUpdate = {
  [K in keyof Omit<AssistantProfile, 'id' | 'updated_at'>]?: AssistantProfile[K] | null;
};
