import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { DefaultPrompt, PromptTemplate, PromptTemplatePayload } from '../models/prompt.model';

@Injectable({ providedIn: 'root' })
export class PromptService {
  private readonly http = inject(HttpClient);
  private readonly endpoint = `${environment.apiUrl}/api/prompts`;

  list(): Observable<PromptTemplate[]> {
    return this.http.get<PromptTemplate[]>(this.endpoint);
  }

  getDefault(): Observable<DefaultPrompt> {
    return this.http.get<DefaultPrompt>(`${this.endpoint}/default`);
  }

  create(payload: PromptTemplatePayload): Observable<PromptTemplate> {
    return this.http.post<PromptTemplate>(this.endpoint, payload);
  }

  // El code no se edita: identifica la variante en cada peticion.
  update(code: string, payload: Omit<PromptTemplatePayload, 'code'>): Observable<PromptTemplate> {
    return this.http.patch<PromptTemplate>(`${this.endpoint}/${code}`, payload);
  }

  remove(code: string): Observable<void> {
    return this.http.delete<void>(`${this.endpoint}/${code}`);
  }

  activate(code: string): Observable<PromptTemplate> {
    return this.http.post<PromptTemplate>(`${this.endpoint}/${code}/activate`, {});
  }

  // Vuelve al prompt del repositorio sin borrar variantes.
  activateDefault(): Observable<void> {
    return this.http.post<void>(`${this.endpoint}/default/activate`, {});
  }
}
