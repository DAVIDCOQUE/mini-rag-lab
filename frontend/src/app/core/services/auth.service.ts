import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, catchError, map, of, shareReplay, tap } from 'rxjs';

import { environment } from '../../../environments/environment';

interface LoginResponse {
  token: string;
  expires_at: string;
}

interface Session {
  token: string;
  expiresAt: number;
}

const STORAGE_KEY = 'sara.session';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly endpoint = `${environment.apiUrl}/api/auth`;

  private readonly session = signal<Session | null>(this.restore());
  // Si el backend pide contrasena; se consulta una vez por carga de la app.
  private enabled$?: Observable<boolean>;

  readonly isLoggedIn = computed(() => {
    const session = this.session();
    return !!session && session.expiresAt > Date.now();
  });

  token(): string | null {
    return this.isLoggedIn() ? this.session()!.token : null;
  }

  // Sin contrasena configurada en el backend el mantenedor no pide login (desarrollo).
  // Si el backend no responde se asume que si: mejor una pantalla de login que una abierta.
  authEnabled(): Observable<boolean> {
    this.enabled$ ??= this.http.get<{ enabled: boolean }>(`${this.endpoint}/status`).pipe(
      map((status) => status.enabled),
      catchError(() => of(true)),
      shareReplay(1),
    );
    return this.enabled$;
  }

  login(password: string): Observable<void> {
    return this.http.post<LoginResponse>(`${this.endpoint}/login`, { password }).pipe(
      tap((res) => this.store({ token: res.token, expiresAt: Date.parse(res.expires_at) })),
      map(() => undefined),
    );
  }

  logout(): void {
    this.store(null);
  }

  private store(session: Session | null): void {
    this.session.set(session);
    try {
      if (session) localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
      else localStorage.removeItem(STORAGE_KEY);
    } catch {
      // Navegacion privada o almacenamiento bloqueado: la sesion dura lo que la pestana.
    }
  }

  private restore(): Session | null {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const session = raw ? (JSON.parse(raw) as Session) : null;
      return session && session.expiresAt > Date.now() ? session : null;
    } catch {
      return null;
    }
  }
}
