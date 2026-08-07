# Cambios implementados

Esta sección documenta únicamente las funcionalidades agregadas después de la versión inicial del laboratorio.

---

## Generación de respuestas con IA

El endpoint `/chat` dejó de devolver únicamente los chunks recuperados desde Qdrant y ahora genera una respuesta en lenguaje natural utilizando un modelo LLM.

Flujo implementado:

```
Pregunta
    │
    ▼
Embeddings
    │
    ▼
Qdrant
    │
    ▼
Reranker
    │
    ▼
Prompt Builder
    │
    ▼
LLM (Qwen2.5:7B)
    │
    ▼
Respuesta final
```

---

## Prompt Builder

Se implementó `rag/prompt_builder.py`, encargado de construir el prompt que recibe el modelo.

El prompt incluye:

- Contexto recuperado desde Qdrant.
- Pregunta del usuario.
- Instrucciones para responder.

El modelo nunca recibe directamente la pregunta del usuario; siempre recibe un prompt construido con el contexto recuperado.

---

## Servicio del LLM

Se implementó `rag/llm_service.py`.

Responsabilidades:

- Enviar el prompt al modelo Qwen mediante Ollama.
- Obtener la respuesta generada.
- Devolver únicamente el texto generado al endpoint `/chat`.

Modelo utilizado:

```
qwen2.5:7b
```

---

## Endpoint `/chat`

El endpoint fue modificado para ejecutar el flujo completo RAG.

Proceso:

1. Generar embedding de la pregunta.
2. Recuperar documentos desde Qdrant.
3. Aplicar reranking.
4. Construir el prompt.
5. Generar respuesta mediante el LLM.
6. Devolver la respuesta junto con las fuentes utilizadas.

Respuesta actual:

```json
{
    "question": "...",
    "answer": "...",
    "sources": [
        {
            "filename": "...",
            "score": -0.42,
            "chunk": "..."
        }
    ]
}
```

---

## RAG estricto

Se reforzó el comportamiento del asistente para evitar alucinaciones.

El modelo tiene prohibido:

- utilizar conocimiento general;
- responder usando información aprendida durante el entrenamiento;
- inventar información;
- completar datos faltantes;
- realizar inferencias fuera del contexto.

Debe responder únicamente utilizando la información recuperada desde los documentos indexados.

---

## Validación del contexto

Antes de llamar al modelo se verifica que exista suficiente evidencia documental.

Configuración agregada:

| Ajuste | Valor |
|---------|------|
| CHAT_MIN_RESULTS | 1 |
| CHAT_MIN_SCORE | -1.5 |

Si no se cumplen estas condiciones:

- no se llama al LLM;
- se devuelve el mensaje de fallback.

Mensaje utilizado:

```
No encontré información suficiente en los documentos para responder esa pregunta.
```

---

## Evidencia de respuesta

Además de la respuesta generada, el endpoint devuelve los fragmentos utilizados durante la generación.

Cada fuente incluye:

- nombre del documento;
- score de relevancia;
- chunk utilizado.

Esto permite verificar de dónde proviene la información utilizada por el modelo.

---

## Interfaz del chat

Se corrigió el comportamiento responsive del módulo de conversación.

Cambios realizados:

- el cuadro de texto permanece fijo en la parte inferior;
- el historial posee scroll independiente;
- el textarea crece automáticamente hasta un límite;
- se corrigió el comportamiento en pantallas pequeñas.

---

## Archivos agregados o modificados

| Archivo | Función |
|----------|----------|
| `rag/prompt_builder.py` | Construcción del prompt para el LLM. |
| `rag/llm_service.py` | Comunicación con Qwen mediante Ollama. |
| `api/routes/chat.py` | Flujo completo de generación de respuestas. |
| `schemas/chat.py` | Nuevos modelos de respuesta (`answer` y `sources`). |
| `core/config.py` | Configuración de RAG estricto (`CHAT_MIN_RESULTS`, `CHAT_MIN_SCORE`). |
| `frontend/chat.service.ts` | Adaptación del nuevo formato de respuesta. |
| `chat.component.scss` | Correcciones del diseño responsive del chat. |

---

## Estado actual

Implementado:

- Generación de respuestas mediante IA.
- Prompt Builder.
- Integración con Qwen2.5.
- RAG estricto.
- Validación del contexto antes del LLM.
- Respuesta con evidencia (`sources`).
- Mejoras en la interfaz del chat.
- OCR para PDFs escaneados (ver sección siguiente).

Pendiente:

- Memoria conversacional.
- Streaming de respuestas.
- Citas automáticas dentro de la respuesta.



















----------------------------------------

## OCR para PDFs escaneados

Se agregó soporte para OCR automático en la etapa de extracción de texto del PDF. El
objetivo es que el laboratorio también pueda procesar PDFs escaneados o documentos
compuestos por imágenes con texto, sin tocar el resto del flujo RAG (chunker, embeddings,
Qdrant, retriever, reranker, chat).

Flujo implementado:

```
PDF
 │
 ▼
PyMuPDF: page.get_text()
 │
 ▼
¿La página trae texto?
 │
 ├─ Sí ──────────────────────────► usar ese texto
 │
 └─ No ──► renderizar la página a imagen ──► EasyOCR ──► texto detectado
                                                              │
                                                              ▼
                                                texto de la página (igual en ambos casos)
                                                              │
                                                              ▼
                                          Chunking → Embeddings → Qdrant (sin cambios)
```

### Servicio OCR

Se implementó un módulo independiente, `documents/ocr.py`, encargado exclusivamente del
reconocimiento óptico de caracteres.

Responsabilidades:

- Recibir una imagen ya renderizada de una página del PDF.
- Ejecutar EasyOCR (`Reader`, cargado de forma perezosa la primera vez que se usa).
- Devolver el texto detectado como una cadena.

El módulo OCR no sabe nada de PDFs, chunking, embeddings ni Qdrant: solo transforma una
imagen en texto.

---

### Integración con el parser de PDF

Se modificó `documents/pdf_parser.py` para decidir, página por página, cuándo usar OCR:

1. Intentar extraer texto con `page.get_text()`.
2. Si el texto no está vacío, usarlo tal cual (comportamiento sin cambios).
3. Si está vacío, renderizar únicamente esa página a imagen y pasarla al servicio OCR.
4. El texto resultante (de PyMuPDF o de OCR) sigue el mismo formato que antes.

`extract_pages()` mantiene exactamente la misma firma y el mismo contrato de salida
(`list[str]`, un elemento por página), así que el resto del pipeline no necesitó cambios.

---

### Optimización

El OCR solo se ejecuta en páginas sin texto: las páginas con texto seleccionable nunca
pasan por EasyOCR. Esto evita procesar de más un PDF mixto (por ejemplo, un anexo
escaneado dentro de un documento digital).

---

### Manejo de errores

Si EasyOCR falla al procesar una página (imagen corrupta, error del modelo, etc.), la
excepción se captura, se registra en el log y esa página queda con texto vacío. El resto
del documento sigue procesándose con normalidad: un fallo puntual de OCR no detiene la
indexación completa.

---

### Compatibilidad

Con esta mejora el laboratorio puede indexar:

- PDFs digitales con texto seleccionable (comportamiento sin cambios).
- Documentos escaneados.
- Fotografías de documentos convertidas a PDF.
- Capturas de pantalla o folletos con texto incrustado en una imagen.

No se añadió interpretación semántica de gráficos, diagramas o fotografías: solo se
extrae el texto presente en la imagen.

---

### Archivos agregados o modificados

| Archivo | Función |
|---|---|
| `documents/ocr.py` | Nuevo. Reconocimiento óptico de caracteres mediante EasyOCR. |
| `documents/pdf_parser.py` | Decide por página cuándo usar OCR; `extract_pages()` conserva el mismo contrato de salida. |
| `requirements.txt` | Se agregó la dependencia `easyocr`. |

> `documents/indexer.py` **no se modificó**. No necesita saber si el texto de una página
> vino de PyMuPDF o de OCR, así que no había nada que cambiarle ahí.

---

### Nota de entorno

La primera vez que se ejecuta el OCR, EasyOCR descarga sus modelos de detección y
reconocimiento (una sola vez; quedan cacheados localmente). Esa descarga puede tardar
varios minutos según la conexión.

---

## Estado actual (OCR)

Implementado:

- OCR automático para páginas sin texto.
- Integración transparente con el parser de PDF (mismo contrato de `extract_pages`).
- Compatibilidad con documentos escaneados o con páginas mixtas.
- Manejo de errores por página sin detener la indexación completa.

Pendiente:

- Interpretación de gráficos y diagramas.
- Soporte para modelos de visión (Vision-Language Models).
- Extracción automática de tablas complejas.
- Generación de descripciones de imágenes mediante IA.
