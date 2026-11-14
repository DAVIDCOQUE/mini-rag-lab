import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { finalize } from 'rxjs';

import { MaintainerAuthService } from '../../core/services/maintainer-auth.service';

@Component({
  selector: 'app-login',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatButtonModule, MatFormFieldModule, MatIconModule, MatInputModule, RouterLink],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent {
  private readonly auth = inject(MaintainerAuthService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly loading = signal(false);
  readonly errorMessage = signal<string | null>(null);

  submit(event: SubmitEvent): void {
    event.preventDefault();
    const form = event.currentTarget as HTMLFormElement;
    const password = new FormData(form).get('password');
    if (typeof password !== 'string' || password.length === 0 || this.loading()) return;

    this.loading.set(true);
    this.errorMessage.set(null);
    this.auth
      .login(password)
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: () => {
          const returnUrl = this.route.snapshot.queryParamMap.get('returnUrl');
          const destination =
            returnUrl?.startsWith('/') &&
            !returnUrl.startsWith('//') &&
            returnUrl !== '/login'
              ? returnUrl
              : '/documents';
          void this.router.navigateByUrl(destination);
        },
        error: (error: unknown) => this.errorMessage.set(loginError(error)),
      });
  }
}

function loginError(error: unknown): string {
  if (error instanceof HttpErrorResponse && error.status === 401) {
    return 'La contraseña del mantenedor no es correcta.';
  }
  if (error instanceof HttpErrorResponse && error.status === 503) {
    return 'Configura MAINTAINER_PASSWORD en el .env antes de iniciar sesión.';
  }
  return 'No se pudo validar la contraseña. Comprueba que el backend esté disponible.';
}
