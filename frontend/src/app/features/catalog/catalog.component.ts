import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'app-catalog',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="p-4">
      <h1 class="h4">Catalog</h1>
      <p class="text-muted">Pendiente de implementar en las próximas clases.</p>
    </div>
  `,
})
export class CatalogComponent {}
