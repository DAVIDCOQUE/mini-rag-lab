import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, map, tap } from 'rxjs';

import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class MaintainerAuthService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;
  private readonly _password = signal<string | null>(null);

  readonly isAuthenticated = computed(() => this._password() !== null);

  login(password: string): Observable<void> {
    const headers = new HttpHeaders({
      Authorization: basicAuthorization(password),
    });

    return this.http
      .get<{ authenticated: boolean }>(`${this.baseUrl}/api/auth/verify`, { headers })
      .pipe(
        tap(() => this._password.set(password)),
        map(() => void 0),
      );
  }

  authorizationHeader(): string | null {
    const password = this._password();
    return password === null ? null : basicAuthorization(password);
  }

  logout(): void {
    this._password.set(null);
  }
}

function basicAuthorization(password: string): string {
  const bytes = new TextEncoder().encode(`mantenedor:${password}`);
  let binary = '';
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return `Basic ${btoa(binary)}`;
}
