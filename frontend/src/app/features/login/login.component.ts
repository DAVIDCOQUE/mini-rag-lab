import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { ActivatedRoute, Router } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { UiPreferencesService } from '../../core/services/ui-preferences.service';

@Component({
  selector: 'app-login',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, MatButtonModule, MatFormFieldModule, MatIconModule, MatInputModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  readonly ui = inject(UiPreferencesService);

  password = '';
  readonly showPassword = signal(false);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);

  readonly copy = computed(() =>
    this.ui.locale() === 'es'
      ? {
          title: 'Mantenedor de Sara',
          subtitle: 'Ingresa la contraseña de administración para continuar.',
          password: 'Contraseña',
          show: 'Mostrar contraseña',
          hide: 'Ocultar contraseña',
          submit: 'Entrar',
          wrong: 'Contraseña incorrecta.',
          tooMany: 'Demasiados intentos. Espera un minuto.',
          unreachable: 'No se pudo conectar con el backend.',
        }
      : {
          title: 'Sara admin',
          subtitle: 'Enter the admin password to continue.',
          password: 'Password',
          show: 'Show password',
          hide: 'Hide password',
          submit: 'Sign in',
          wrong: 'Wrong password.',
          tooMany: 'Too many attempts. Wait a minute.',
          unreachable: 'Could not reach the backend.',
        },
  );

  submit(): void {
    if (!this.password || this.busy()) return;
    this.busy.set(true);
    this.error.set(null);
    this.auth.login(this.password).subscribe({
      next: () => {
        const next = this.route.snapshot.queryParamMap.get('next');
        // Solo rutas internas: un ?next= externo no debe sacar al usuario de la app.
        this.router.navigateByUrl(next?.startsWith('/') && !next.startsWith('//') ? next : '/home');
      },
      error: (err) => {
        this.busy.set(false);
        this.password = '';
        const copy = this.copy();
        this.error.set(err?.status === 401 ? copy.wrong : err?.status === 429 ? copy.tooMany : copy.unreachable);
      },
    });
  }
}
