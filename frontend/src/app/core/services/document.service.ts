import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  DocumentItem,
  DocumentUpdate,
  IndexedChunks,
  IndexResult,
  ProcessingResult,
} from '../models/document.model';

@Injectable({ providedIn: 'root' })
export class DocumentService {
  private readonly http = inject(HttpClient);
  private readonly endpoint = `${environment.apiUrl}/api/documents`;

  list(): Observable<DocumentItem[]> {
    return this.http.get<DocumentItem[]>(this.endpoint);
  }

  get(id: string): Observable<DocumentItem> {
    return this.http.get<DocumentItem>(`${this.endpoint}/${id}`);
  }

  upload(file: File): Observable<DocumentItem> {
    const form = new FormData();
    form.append('file', file);
    return this.http.post<DocumentItem>(this.endpoint, form);
  }

  update(id: string, data: DocumentUpdate): Observable<DocumentItem> {
    return this.http.put<DocumentItem>(`${this.endpoint}/${id}`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.endpoint}/${id}`);
  }

  process(id: string): Observable<ProcessingResult> {
    return this.http.post<ProcessingResult>(`${this.endpoint}/${id}/process`, {});
  }

  index(id: string): Observable<IndexResult> {
    return this.http.post<IndexResult>(`${this.endpoint}/${id}/index`, {});
  }

  indexedChunks(id: string): Observable<IndexedChunks> {
    return this.http.get<IndexedChunks>(`${this.endpoint}/${id}/chunks`);
  }
}
