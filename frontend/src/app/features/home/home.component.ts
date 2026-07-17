import { ChangeDetectionStrategy, Component, inject, signal, OnInit } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { HealthService } from '../../core/services/health.service';

type ConnectionState = 'loading' | 'ok' | 'error';

@Component({
  selector: 'app-home',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatCardModule, MatIconModule, MatProgressSpinnerModule],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss',
})
export class HomeComponent implements OnInit {
  private readonly healthService = inject(HealthService);

  readonly state = signal<ConnectionState>('loading');
  readonly detail = signal<string>('');

  ngOnInit(): void {
    this.healthService.check().subscribe({
      next: (res) => {
        this.state.set('ok');
        this.detail.set(res.message);
      },
      error: () => {
        this.state.set('error');
        this.detail.set('No se pudo conectar con el backend (¿está uvicorn corriendo?)');
      },
    });
  }
}
