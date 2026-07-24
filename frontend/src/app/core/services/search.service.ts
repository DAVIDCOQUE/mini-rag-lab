import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { SearchResponse } from '../models/search.model';

@Injectable({ providedIn: 'root' })
export class SearchService {
  private readonly http = inject(HttpClient);
  private readonly endpoint = `${environment.apiUrl}/api/search`;

  search(query: string, limit = 5): Observable<SearchResponse> {
    return this.http.post<SearchResponse>(this.endpoint, { query, limit });
  }
}
