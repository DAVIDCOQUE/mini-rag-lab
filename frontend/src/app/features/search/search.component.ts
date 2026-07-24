import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';

import { SearchResultItem } from '../../core/models/search.model';
import { SearchService } from '../../core/services/search.service';

@Component({
  selector: 'app-search',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, MatButtonModule, MatIconModule, MatProgressBarModule],
  templateUrl: './search.component.html',
  styleUrl: './search.component.scss',
})
export class SearchComponent {
  private readonly service = inject(SearchService);

  query = '';
  readonly loading = signal(false);
  readonly searched = signal(false);
  readonly results = signal<SearchResultItem[]>([]);

  search(): void {
    const text = this.query.trim();
    if (!text || this.loading()) return;
    this.loading.set(true);
    this.service.search(text).subscribe({
      next: (res) => {
        this.results.set(res.results);
        this.searched.set(true);
        this.loading.set(false);
      },
      error: () => {
        this.results.set([]);
        this.searched.set(true);
        this.loading.set(false);
      },
    });
  }

  scorePercent(score: number): number {
    return Math.round(score * 100);
  }
}
