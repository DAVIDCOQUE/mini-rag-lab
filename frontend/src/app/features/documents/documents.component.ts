import { DatePipe } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  computed,
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

import {
  DocumentItem,
  DocumentStatus,
  IndexedChunks,
  ProcessingResult,
} from '../../core/models/document.model';
import { DocumentService } from '../../core/services/document.service';
import { UiPreferencesService } from '../../core/services/ui-preferences.service';

// Cada estado se mapea a uno de los tonos semanticos del design system.
const STATUS_VARIANTS: Record<DocumentStatus, string> = {
  PENDING: 'neutral',
  PROCESSING: 'info',
  INDEXED: 'ok',
  ERROR: 'danger',
};

@Component({
  selector: 'app-documents',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    DatePipe,
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
  readonly ui = inject(UiPreferencesService);

  readonly documents = signal<DocumentItem[]>([]);
  readonly loading = signal(false);
  readonly busy = signal(false);

  readonly copy = computed(() => {
    const locale = this.ui.locale();

    return locale === 'es'
      ? {
          upload: 'Subir documento',
          refresh: 'Recargar la biblioteca',
          corpusLabel: 'Corpus',
          documentsLabel: 'Documentos',
          process: 'Procesar',
          index: 'Indexar',
          inspect: 'Inspeccionar',
          edit: 'Renombrar documento',
          remove: 'Eliminar documento',
          empty: 'Todavía no hay documentos. Sube un PDF para empezar a construir la biblioteca.',
          statuses: {
            PENDING: 'Pendiente',
            PROCESSING: 'Procesando',
            INDEXED: 'Indexado',
            ERROR: 'Error',
          } as Record<DocumentStatus, string>,
          hints: {
            PENDING: 'Subido, esperando procesamiento e indexación.',
            PROCESSING: 'Se está dividiendo en chunks para recuperación.',
            INDEXED: 'Listo para búsqueda semántica y chat fundamentado.',
            ERROR: 'El procesamiento falló y requiere atención.',
          } as Record<DocumentStatus, string>,
          metrics: {
            total: 'Documentos',
            indexed: 'Indexados',
            processing: 'Procesando',
            pending: 'Pendientes',
          },
          dialogUploadTitle: 'Subir documento',
          dialogSelectPdf: 'Seleccionar PDF',
          dialogVisibleName: 'Nombre visible',
          dialogVisibleHint: 'Opcional. Se usa el nombre del archivo por defecto.',
          dialogEditTitle: 'Renombrar documento',
          dialogProcessTitle: 'Procesamiento',
          dialogIndexedTitle: 'Indexado en Qdrant',
          dialogDeleteTitle: 'Eliminar documento',
          dialogDeleteBody: '¿Eliminar',
          dialogDeleteWarning:
            'El archivo y su registro se eliminarán. Esta acción no se puede deshacer.',
          dialogChunksTitle: 'Chunks generados',
          dialogVectorHint: 'chunks almacenados como vectores en la colección.',
          pages: 'Páginas',
          characters: 'Caracteres',
          chunks: 'Chunks',
          chunkLabel: 'Chunk',
          pageLabel: 'Página',
          charsLabel: 'caracteres',
          cancel: 'Cancelar',
          save: 'Guardar',
          close: 'Cerrar',
          confirmDelete: 'Eliminar',
          toastAction: 'Cerrar',
          toasts: {
            listFailed: 'No se pudieron cargar los documentos.',
            onlyPdf: 'Solo se permiten archivos PDF.',
            uploaded: 'Documento subido.',
            uploadFailed: 'No se pudo subir el documento.',
            updated: 'Documento actualizado.',
            updateFailed: 'No se pudo actualizar el documento.',
            deleted: 'Documento eliminado.',
            deleteFailed: 'No se pudo eliminar el documento.',
            processFailed: 'No se pudo procesar el documento.',
            indexFailed: 'No se pudo indexar el documento.',
            vectorFailed: 'No se pudo consultar la base vectorial.',
            indexed: (chunks: number) => `Indexado: ${chunks} chunks en Qdrant.`,
          },
        }
      : {
          upload: 'Upload document',
          refresh: 'Reload the library',
          corpusLabel: 'Corpus',
          documentsLabel: 'Documents',
          process: 'Process',
          index: 'Index',
          inspect: 'Inspect',
          edit: 'Rename document',
          remove: 'Delete document',
          empty: 'No documents yet. Upload a PDF to start building the library.',
          statuses: {
            PENDING: 'Pending',
            PROCESSING: 'Processing',
            INDEXED: 'Indexed',
            ERROR: 'Error',
          } as Record<DocumentStatus, string>,
          hints: {
            PENDING: 'Uploaded, waiting for processing and indexing.',
            PROCESSING: 'Being chunked for retrieval.',
            INDEXED: 'Ready for semantic search and grounded chat.',
            ERROR: 'Processing failed and needs attention.',
          } as Record<DocumentStatus, string>,
          metrics: {
            total: 'Documents',
            indexed: 'Indexed',
            processing: 'Processing',
            pending: 'Pending',
          },
          dialogUploadTitle: 'Upload document',
          dialogSelectPdf: 'Select PDF',
          dialogVisibleName: 'Visible name',
          dialogVisibleHint: 'Optional. The file name is used by default.',
          dialogEditTitle: 'Rename document',
          dialogProcessTitle: 'Processing',
          dialogIndexedTitle: 'Indexed in Qdrant',
          dialogDeleteTitle: 'Delete document',
          dialogDeleteBody: 'Delete',
          dialogDeleteWarning: 'The file and its record will be removed. This cannot be undone.',
          dialogChunksTitle: 'Generated chunks',
          dialogVectorHint: 'chunks stored as vectors in the collection.',
          pages: 'Pages',
          characters: 'Characters',
          chunks: 'Chunks',
          chunkLabel: 'Chunk',
          pageLabel: 'Page',
          charsLabel: 'characters',
          cancel: 'Cancel',
          save: 'Save',
          close: 'Close',
          confirmDelete: 'Delete',
          toastAction: 'Dismiss',
          toasts: {
            listFailed: 'Could not load the documents.',
            onlyPdf: 'Only PDF files are allowed.',
            uploaded: 'Document uploaded.',
            uploadFailed: 'Could not upload the document.',
            updated: 'Document updated.',
            updateFailed: 'Could not update the document.',
            deleted: 'Document deleted.',
            deleteFailed: 'Could not delete the document.',
            processFailed: 'Could not process the document.',
            indexFailed: 'Could not index the document.',
            vectorFailed: 'Could not query the vector store.',
            indexed: (chunks: number) => `Indexed: ${chunks} chunks in Qdrant.`,
          },
        };
  });

  readonly metrics = computed(() => {
    const docs = this.documents();
    const labels = this.copy().metrics;

    return [
      { key: 'total', label: labels.total, value: docs.length, tone: 'neutral' },
      {
        key: 'indexed',
        label: labels.indexed,
        value: docs.filter((doc) => doc.status === 'INDEXED').length,
        tone: 'ok',
      },
      {
        key: 'processing',
        label: labels.processing,
        value: docs.filter((doc) => doc.status === 'PROCESSING').length,
        tone: 'info',
      },
      {
        key: 'pending',
        label: labels.pending,
        value: docs.filter((doc) => doc.status === 'PENDING').length,
        tone: 'muted',
      },
    ];
  });

  // Estado de los dialogos.
  readonly uploadFile = signal<File | null>(null);
  uploadName = '';
  editName = '';
  readonly deleteTarget = signal<DocumentItem | null>(null);
  readonly processTarget = signal<DocumentItem | null>(null);
  readonly processResult = signal<ProcessingResult | null>(null);
  readonly indexedTarget = signal<DocumentItem | null>(null);
  readonly indexedResult = signal<IndexedChunks | null>(null);

  private readonly uploadDialog = viewChild.required<TemplateRef<unknown>>('uploadDialog');
  private readonly editDialog = viewChild.required<TemplateRef<unknown>>('editDialog');
  private readonly deleteDialog = viewChild.required<TemplateRef<unknown>>('deleteDialog');
  private readonly processDialog = viewChild.required<TemplateRef<unknown>>('processDialog');
  private readonly indexedDialog = viewChild.required<TemplateRef<unknown>>('indexedDialog');

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
        this.notify(this.copy().toasts.listFailed);
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
      this.notify(this.copy().toasts.onlyPdf);
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
          next: () => this.afterMutation(this.copy().toasts.updated),
          error: () => this.fail(this.copy().toasts.updateFailed),
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
          next: () => this.afterMutation(this.copy().toasts.deleted),
          error: () => this.fail(this.copy().toasts.deleteFailed),
        });
      });
  }

  // --- Procesar documento (extraer texto + chunking) ---
  openProcess(doc: DocumentItem): void {
    this.busy.set(true);
    this.service.process(doc.id).subscribe({
      next: (result) => {
        this.busy.set(false);
        this.processTarget.set(doc);
        this.processResult.set(result);
        this.dialog.open(this.processDialog(), { width: '760px', maxHeight: '85vh' });
      },
      error: (err) => {
        this.busy.set(false);
        this.notify(err?.error?.detail ?? this.copy().toasts.processFailed);
      },
    });
  }

  // --- Indexar documento (embeddings + Qdrant) ---
  openIndex(doc: DocumentItem): void {
    this.busy.set(true);
    this.service.index(doc.id).subscribe({
      next: (result) => {
        this.busy.set(false);
        this.notify(this.copy().toasts.indexed(result.total_chunks));
        this.refresh();
      },
      error: (err) => {
        this.busy.set(false);
        this.notify(err?.error?.detail ?? this.copy().toasts.indexFailed);
        this.refresh();
      },
    });
  }

  // --- Ver lo guardado en la base vectorial (Qdrant) ---
  openIndexed(doc: DocumentItem): void {
    this.busy.set(true);
    this.service.indexedChunks(doc.id).subscribe({
      next: (result) => {
        this.busy.set(false);
        this.indexedTarget.set(doc);
        this.indexedResult.set(result);
        this.dialog.open(this.indexedDialog(), { width: '760px', maxHeight: '85vh' });
      },
      error: (err) => {
        this.busy.set(false);
        this.notify(err?.error?.detail ?? this.copy().toasts.vectorFailed);
      },
    });
  }

  statusLabel(status: DocumentStatus): string {
    return this.copy().statuses[status] ?? status;
  }

  statusHint(status: DocumentStatus): string {
    return this.copy().hints[status] ?? '';
  }

  statusVariant(status: DocumentStatus): string {
    return STATUS_VARIANTS[status] ?? 'neutral';
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
            next: () => this.afterMutation(this.copy().toasts.uploaded),
            error: () => this.afterMutation(this.copy().toasts.uploaded),
          });
        } else {
          this.afterMutation(this.copy().toasts.uploaded);
        }
      },
      error: () => this.fail(this.copy().toasts.uploadFailed),
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
    this.snackBar.open(message, this.copy().toastAction, { duration: 3000 });
  }
}
