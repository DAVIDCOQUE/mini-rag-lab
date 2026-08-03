// Variante de prompt guardada en base de datos.
export interface PromptTemplate {
  id: string;
  code: string;
  name: string;
  body: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Prompt del repositorio: solo lectura, es la referencia para crear variantes.
export interface DefaultPrompt {
  code: string;
  name: string;
  body: string;
  no_answer_placeholder: string;
  no_answer_message: string;
}

export interface PromptTemplatePayload {
  code: string;
  name: string;
  body: string;
}
