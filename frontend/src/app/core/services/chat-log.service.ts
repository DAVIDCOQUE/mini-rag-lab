import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { ChatLogFilters, ChatLogPage } from '../models/chat-log.model';

@Injectable({ providedIn: 'root' })
export class ChatLogService {
  private readonly http = inject(HttpClient);
  private readonly endpoint = `${environment.apiUrl}/api/chat-logs`;

  list(filters: ChatLogFilters, limit: number, offset: number): Observable<ChatLogPage> {
    const params = this.params(filters).set('limit', limit).set('offset', offset);
    return this.http.get<ChatLogPage>(this.endpoint, { params });
  }

  // URL directa: el navegador descarga el CSV con el nombre que pone el backend.
  exportUrl(filters: ChatLogFilters): string {
    const query = this.params(filters).toString();
    return `${this.endpoint}/export${query ? `?${query}` : ''}`;
  }

  private params(filters: ChatLogFilters): HttpParams {
    let params = new HttpParams();
    if (filters.route) params = params.set('route', filters.route);
    if (filters.noAnswer) params = params.set('no_answer', true);
    if (filters.q?.trim()) params = params.set('q', filters.q.trim());
    if (filters.dateFrom) params = params.set('date_from', filters.dateFrom);
    if (filters.dateTo) params = params.set('date_to', filters.dateTo);
    return params;
  }
}
