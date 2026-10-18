# Integración del avatar (Unity) con el backend

Cómo debe comunicarse el cliente del quiosco con el backend de Sara. El backend
ya resuelve la búsqueda en documentos, la elección de cómo responder y el saludo.
El cliente solo envía la pregunta, guarda la conversación en curso y la borra
cuando el estudiante se va.

---

## Idea central: la memoria la guarda el quiosco

El servidor **no guarda conversaciones**. Cada petición lleva la conversación
completa (`history`), el servidor responde y la olvida. Por eso:

- **Para recordar,** el cliente envía siempre el historial.
- **Para olvidar,** el cliente vacía su lista. No hay que avisar al servidor.
- Dos quioscos nunca comparten conversación, aunque usen el mismo backend.

---

## Dirección del servidor

| Entorno | URL base |
|---|---|
| Desarrollo local | `http://localhost:8000` |
| Docker (`docker compose up`) | `http://<ip-del-servidor>:8000` |

Si el backend corre **fuera de Docker** y Unity está en otra máquina, el `.env`
del backend debe tener `HOST=0.0.0.0`. Con el valor por defecto (`127.0.0.1`)
solo acepta conexiones desde su propia máquina.

---

## Enviar una pregunta

**`POST /api/chat`** · `Content-Type: application/json`

### Petición

```json
{
  "message": "¿Y cuánto cuesta?",
  "history": [
    { "role": "user", "content": "¿Cuál es el procedimiento para la matrícula?" },
    { "role": "assistant", "content": "La matrícula se hace en línea por el portal…" }
  ]
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `message` | string | Lo que dijo el estudiante ahora |
| `history` | lista | Turnos anteriores de **esta** conversación, en orden. Vacía en el primer mensaje |
| `history[].role` | `"user"` o `"assistant"` | Quién lo dijo |
| `history[].content` | string | El texto tal cual |

No hay que recortar el historial. El servidor se queda con lo que cabe en la
memoria del modelo y conserva siempre el primer mensaje del estudiante.

### Respuesta `200`

```json
{
  "question": "¿Y cuánto cuesta?",
  "answer": "El valor de la matrícula es…",
  "sources": [
    { "filename": "Guia-Actualizada-2023.pdf", "score": -0.71, "chunk": "texto del documento…" }
  ],
  "downloads": [
    {
      "document_id": "022e1a06-…",
      "filename": "Formato-cancelacion-semestre.pdf",
      "url": "https://<servidor>/api/documents/download?token=…",
      "qr_url": "https://<servidor>/api/documents/download/qr?token=…",
      "expires_at": "2026-10-17T20:20:17Z"
    }
  ]
}
```

| Campo | Uso en el quiosco |
|---|---|
| `answer` | Lo que dice el avatar |
| `sources` | Documentos de los que salió la respuesta. Vacío si no se buscó en documentos. Opcional mostrarlo |
| `downloads` | Formatos que el estudiante puede llevarse. Vacío casi siempre. Ver [Formatos descargables](#formatos-descargables-qr) |
| `question` | Eco de la pregunta; no hace falta usarlo |

`score` no es un porcentaje: puede ser negativo. No conviene mostrarlo al estudiante.

### Respuestas que también son `200`

No son errores; el avatar las dice como cualquier otra:

- **Algo que no está en los documentos:** *"No encontré información suficiente
  en los documentos para responder esa pregunta."*
- **Un tema ajeno a la universidad:** *"Solo puedo ayudarte con los documentos
  de la institución y con temas académicos…"*

### Errores

| Código | Significa | Qué hacer |
|---|---|---|
| `503` | Falla un servicio interno (el modelo de IA o la base de documentos) | Decir algo como "No estoy disponible en este momento" y **no** añadir nada al historial |
| `422` | La petición está mal formada (falta `message`, `role` inválido…) | Es un error del cliente: revisar el JSON |

---

## Reglas de la conversación

### Al recibir cada respuesta

Añadir **dos** turnos al historial: la pregunta del estudiante y la respuesta.

```
history += { role: "user",      content: message }
history += { role: "assistant", content: answer  }
```

Si la petición falla, no se añade nada: el estudiante puede repetir la pregunta.

### Primer mensaje

Se envía con `history: []`. El backend antepone el saludo
("¡Hola! Soy el asistente académico de la universidad…"), así que **el cliente
no debe añadir otro**. En los mensajes siguientes el backend ya no saluda.

### Una pregunta a la vez

No enviar otra pregunta hasta recibir la respuesta. Tiempos orientativos en la
máquina de desarrollo, con GPU:

| Tipo de pregunta | Tiempo |
|---|---|
| Saludo, despedida, sobre la propia conversación | 1–3 s |
| Académica general | 2–5 s |
| Sobre la universidad (busca en documentos) | 5–25 s |
| **La primera tras arrancar el servidor** | hasta ~2 min (carga los modelos) |

Se recomienda un timeout de **60 s** y mostrar al avatar "pensando" mientras tanto.

### Cuándo borrar la conversación

Borrar = vaciar `history` y volver a la pantalla de espera. Hay que hacerlo:

1. **Si el estudiante pulsa "Terminar conversación".**
2. **Tras 60 s sin interacción.** Aparece "¿Sigues ahí?" con una cuenta atrás de 10 s
   y un botón "Sigo aquí". Cualquier interacción cancela el aviso. Si llega a 0,
   se borra.
3. **Si el quiosco detecta que no hay nadie delante** (cámara o sensor), si lo tiene.
   Es más fiable que el contador; el contador queda de respaldo.

Además:

- **El contador no corre mientras se espera una respuesta**, que puede tardar 20 s.
- **En la pantalla de espera no corre,** porque no hay nada que borrar.
- **Al borrar se cancela la petición en curso,** para que la respuesta tardía de un
  estudiante no le aparezca al siguiente.

### Privacidad

- La conversación vive **solo en memoria**. No escribirla en disco, en
  `PlayerPrefs` ni en logs: los estudiantes dicen su nombre y otros datos.
- Al cerrar o reiniciar la aplicación, la conversación se pierde, y es lo correcto.

---

## Formatos descargables (QR)

En el mantenedor hay dos tipos de documento:

- **Información** (reglamentos, guías): el asistente responde con su contenido.
  Nunca se descargan.
- **Formatos** (por ejemplo, el de cancelación de semestre): el asistente no los
  lee. Se ofrecen para descargar cuando la pregunta es sobre su trámite.

Cuando la pregunta corresponde a un trámite con formato, `downloads` trae su enlace
(como mucho 3) y `answer` termina con *"Puedes descargar el formato escaneando el
código QR."*. Si ningún formato encaja exactamente, `downloads` viene vacío: el
servidor prefiere no ofrecer nada antes que un formato de otro trámite.

Para cada elemento de `downloads`:

1. **Mostrar la imagen de `qr_url`.** Es un PNG del QR ya generado por el servidor
   (se descarga con `UnityWebRequestTexture.GetTexture`), así que Unity no necesita
   ninguna librería de QR. El estudiante lo escanea con su celular y descarga el PDF.
2. **Mostrar `filename` junto al QR**, para que sepa qué se lleva.
3. **Quitar el QR al terminar la conversación o al pasar `expires_at`.** El enlace
   caduca a los 15 minutos; después devuelve `404`.

El enlace va firmado: no se puede modificar para bajar otro documento. Si en el
mantenedor se desmarca un formato, sus enlaces dejan de funcionar al instante.

**Requisito de red:** el celular del estudiante tiene que poder abrir `url`. La
dirección sale de `PUBLIC_BASE_URL` en el `.env` del backend, y debe ser la IP del
servidor en la red del campus (el celular tendría que estar en ese WiFi) o un
dominio público con HTTPS. Con `localhost` el QR no funciona desde un celular.

---

## Comprobar que el servidor está listo

**`GET /health`** (sin el prefijo `/api`)

```json
{ "status": "ok", "database": "connected", "qdrant": "connected", "ollama": "connected" }
```

Sirve para mostrar "fuera de servicio" al arrancar el quiosco. **No basta con
`status`**: siempre vale `"ok"` mientras la API responda. Hay que comprobar que
`database`, `qdrant` y `ollama` estén en `"connected"`.

---

## Ejemplo en C#

```csharp
using System;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

[Serializable] public class ChatTurn { public string role; public string content; }
[Serializable] public class ChatRequest { public string message; public List<ChatTurn> history; }
[Serializable] public class ChatSource { public string filename; public float score; public string chunk; }
[Serializable] public class ChatDownload { public string document_id; public string filename; public string url; public string qr_url; public string expires_at; }
[Serializable] public class ChatResponse { public string question; public string answer; public List<ChatSource> sources; public List<ChatDownload> downloads; }

public class SaraClient : MonoBehaviour
{
    [SerializeField] string baseUrl = "http://localhost:8000";

    // La memoria de la conversación: solo en RAM, nunca en disco.
    readonly List<ChatTurn> history = new();
    UnityWebRequest pending;
    int conversationId;  // cambia al borrar: descarta respuestas de la conversación anterior

    public void Ask(string message, Action<string> onAnswer, Action onUnavailable)
    {
        if (pending != null) return;  // una pregunta a la vez
        StartCoroutine(Send(message, onAnswer, onUnavailable));
    }

    System.Collections.IEnumerator Send(string message, Action<string> onAnswer, Action onUnavailable)
    {
        var body = JsonUtility.ToJson(new ChatRequest { message = message, history = history });
        using var req = new UnityWebRequest($"{baseUrl}/api/chat", "POST")
        {
            uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(body)),
            downloadHandler = new DownloadHandlerBuffer(),
            timeout = 60,
        };
        req.SetRequestHeader("Content-Type", "application/json");
        var startedIn = conversationId;
        pending = req;
        yield return req.SendWebRequest();

        // Se terminó la conversación mientras se esperaba: la respuesta ya no es de nadie.
        if (startedIn != conversationId) yield break;
        pending = null;

        if (req.result != UnityWebRequest.Result.Success)
        {
            onUnavailable();  // 503, timeout o sin red: no se toca el historial
            yield break;
        }

        var res = JsonUtility.FromJson<ChatResponse>(req.downloadHandler.text);
        history.Add(new ChatTurn { role = "user", content = message });
        history.Add(new ChatTurn { role = "assistant", content = res.answer });
        onAnswer(res.answer);
    }

    // Botón "Terminar", fin de la cuenta atrás o nadie delante del quiosco.
    public void EndConversation()
    {
        conversationId++;
        pending?.Abort();
        pending = null;
        history.Clear();
    }
}
```

---

## Pendiente del lado del servidor

Cosas que el avatar va a notar y que aún no están resueltas:

- **Formato para voz.** Algunas respuestas traen listas numeradas o negritas,
  pensadas para pantalla. Se puede ajustar sin tocar código con una variante de
  prompt ("responde en frases cortas, sin listas") desde la vista *Prompts* del
  mantenedor.
- **Respuesta en streaming.** Hoy la respuesta llega completa al final. Para que
  el avatar empiece a hablar antes, haría falta una versión de `/api/chat` que
  envíe el texto a medida que se genera.
- **Voz a texto y texto a voz.** Aún no está decidido si van en Unity o en el
  backend.

Para probar todo esto sin Unity, el chat del mantenedor (`http://localhost:4200`)
usa exactamente este mismo contrato y simula las reglas del quiosco: historial,
botón Terminar y el aviso de inactividad.
