import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { MaintainerAuthService } from '../services/maintainer-auth.service';

const MAINTAINER_API_PREFIXES = [
  '/api/documents',
  '/api/search',
  '/api/prompts',
  '/api/chat-logs',
  '/api/profile',
];

export const maintainerAuthInterceptor: HttpInterceptorFn = (request, next) => {
  if (!requiresMaintainer(request.url)) {
    return next(request);
  }

  const auth = inject(MaintainerAuthService);
  const authorization = auth.authorizationHeader();
  if (!authorization) {
    return next(request);
  }

  const router = inject(Router);
  return next(request.clone({ setHeaders: { Authorization: authorization } })).pipe(
    catchError((error: unknown) => {
      if (error instanceof HttpErrorResponse && error.status === 401) {
        auth.logout();
        void router.navigate(['/login'], { queryParams: { returnUrl: router.url } });
      }
      return throwError(() => error);
    }),
  );
};

function requiresMaintainer(url: string): boolean {
  const path = new URL(url, 'http://localhost').pathname;
  if (
    path === '/api/documents/download' ||
    path === '/api/documents/download/qr' ||
    /^\/api\/documents\/[^/]+\/qr$/.test(path)
  ) {
    return false;
  }

  return MAINTAINER_API_PREFIXES.some(
    (prefix) => path === prefix || path.startsWith(`${prefix}/`),
  );
}
