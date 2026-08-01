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

Pendiente:

- Memoria conversacional.
- Streaming de respuestas.
- OCR para PDFs escaneados.
- Citas automáticas dentro de la respuesta.