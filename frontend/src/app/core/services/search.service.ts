import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { SearchResponse } from '../models/search.model';

@Injectable({ providedIn: 'root' })
export class SearchService {
  private readonly http = inject(HttpClient);
  private readonly endpoint = `${environment.apiUrl}/api/search`;

  // generate pide ademas la respuesta del LLM sobre los chunks recuperados; la
  // politica es de la vista, no del servicio. promptCode elige con que instrucciones
  // se genera: sin el manda la variante activa del mantenedor.
  search(
    query: string,
    limit = 5,
    generate = false,
    promptCode?: string
  ): Observable<SearchResponse> {
    return this.http.post<SearchResponse>(this.endpoint, {
      query,
      limit,
      generate,
      prompt_code: promptCode ?? null,
    });
  }
}
