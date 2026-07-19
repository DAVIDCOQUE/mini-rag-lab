import { DatePipe } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  TemplateRef,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';

import { DocumentItem, DocumentStatus } from '../../core/models/document.model';
import { DocumentService } from '../../core/services/document.service';

const STATUS_LABELS: Record<DocumentStatus, string> = {
  PENDING: 'Pendiente',
  PROCESSING: 'Procesando',
  INDEXED: 'Indexado',
  ERROR: 'Error',
};

@Component({
  selector: 'app-documents',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    DatePipe,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressBarModule,
  ],
  templateUrl: './documents.component.html',
  styleUrl: './documents.component.scss',
})
export class DocumentsComponent {
  private readonly service = inject(DocumentService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);

  readonly documents = signal<DocumentItem[]>([]);
  readonly loading = signal(false);
  readonly busy = signal(false);

  readonly displayedColumns = ['name', 'size', 'status', 'createdAt', 'actions'];

  // Estado de los dialogos.
  readonly uploadFile = signal<File | null>(null);
  uploadName = '';
  editName = '';
  readonly deleteTarget = signal<DocumentItem | null>(null);

  private readonly uploadDialog = viewChild.required<TemplateRef<unknown>>('uploadDialog');
  private readonly editDialog = viewChild.required<TemplateRef<unknown>>('editDialog');
  private readonly deleteDialog = viewChild.required<TemplateRef<unknown>>('deleteDialog');

  constructor() {
    this.refresh();
  }

  refresh(): void {
    this.loading.set(true);
    this.service.list().subscribe({
      next: (docs) => {
        this.documents.set(docs);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.notify('No se pudieron cargar los documentos.');
      },
    });
  }

  // --- Subir documento (dialogo: archivo + nombre visible opcional) ---
  openUpload(): void {
    this.uploadFile.set(null);
    this.uploadName = '';
    this.dialog
      .open(this.uploadDialog(), { width: '480px' })
      .afterClosed()
      .subscribe((confirmed) => {
        const file = this.uploadFile();
        if (!confirmed || !file) return;
        this.upload(file, this.uploadName.trim());
      });
  }

  onUploadFileSelected(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0] ?? null;
    if (file && !this.isPdf(file)) {
      this.notify('Solo se permiten archivos PDF.');
      this.uploadFile.set(null);
      return;
    }
    this.uploadFile.set(file);
    // Autocompletar el nombre visible con el del archivo si aun no se ha escrito uno.
    if (file && !this.uploadName) this.uploadName = file.name;
  }

  // --- Editar (solo nombre visible) ---
  openEdit(doc: DocumentItem): void {
    this.editName = doc.original_name;
    this.dialog
      .open(this.editDialog(), { width: '480px' })
      .afterClosed()
      .subscribe((confirmed) => {
        const name = this.editName.trim();
        if (!confirmed || !name || name === doc.original_name) return;
        this.busy.set(true);
        this.service.update(doc.id, { original_name: name }).subscribe({
          next: () => this.afterMutation('Documento actualizado.'),
          error: () => this.fail('No se pudo actualizar el documento.'),
        });
      });
  }

  // --- Eliminar ---
  openDelete(doc: DocumentItem): void {
    this.deleteTarget.set(doc);
    this.dialog
      .open(this.deleteDialog(), { width: '420px' })
      .afterClosed()
      .subscribe((confirmed) => {
        if (!confirmed) return;
        this.busy.set(true);
        this.service.delete(doc.id).subscribe({
          next: () => this.afterMutation('Documento eliminado.'),
          error: () => this.fail('No se pudo eliminar el documento.'),
        });
      });
  }

  statusLabel(status: DocumentStatus): string {
    return STATUS_LABELS[status] ?? status;
  }

  formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  private upload(file: File, visibleName?: string): void {
    this.busy.set(true);
    this.service.upload(file).subscribe({
      next: (created) => {
        if (visibleName && visibleName !== created.original_name) {
          // Nombre visible personalizado desde el dialogo de subida.
          this.service.update(created.id, { original_name: visibleName }).subscribe({
            next: () => this.afterMutation('Documento subido.'),
            error: () => this.afterMutation('Documento subido.'),
          });
        } else {
          this.afterMutation('Documento subido.');
        }
      },
      error: () => this.fail('No se pudo subir el documento.'),
    });
  }

  private afterMutation(message: string): void {
    this.busy.set(false);
    this.notify(message);
    this.refresh();
  }

  private fail(message: string): void {
    this.busy.set(false);
    this.notify(message);
  }

  private isPdf(file: File): boolean {
    return file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
  }

  private notify(message: string): void {
    this.snackBar.open(message, 'Cerrar', { duration: 3000 });
  }
}
