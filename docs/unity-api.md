# Integración del quiosco (Unity) con Sara

Qué envía el quiosco al backend, qué recibe y cómo se comporta Sara, de punta a punta.
La primera sección responde lo básico en un minuto; el resto es el detalle.

---

## Respuestas rápidas

| Pregunta | Respuesta |
|---|---|
| **Endpoint y método** | `POST /api/chat`, con `Content-Type: application/json` |
| **¿Qué le envío?** | La pregunta (`message`) **y la conversación anterior completa** (`history`). No hay `session_id` que dé memoria: el servidor no guarda nada entre peticiones. Opcionalmente un `conversation_id`, que solo sirve para el log del mantenedor. Ver [Petición](#petición) |
| **¿Qué devuelve?** | `answer` (lo que dice el avatar), `sources` (de qué documento salió) y `downloads` (formatos con su QR, casi siempre vacío). Ver el [ejemplo real](#ejemplo-real) |
| **¿Streaming?** | No. La respuesta llega **completa, de una vez**, en un único JSON |
| **¿Cuánto tarda?** | Mediana de **~5 s**; las preguntas sobre la universidad, entre 5 y 13 s; los saludos, 1–2 s. Timeout recomendado: **60 s**. Ver [Tiempos](#tiempos-de-respuesta) |
| **¿Hay Swagger?** | Sí: **`/docs`** (por ejemplo `https://<url-ngrok>/docs`). Desde ahí se puede probar `/api/chat`. El resto de rutas son del mantenedor y piden contraseña |

---

## Cómo funciona Sara

```
 Quiosco (Unity)                         Backend (FastAPI)
 ───────────────                         ──────────────────────────────────────────
 guarda la conversación   POST /api/chat
 en memoria         ───────────────────▶  1. Clasifica la pregunta:
                     {message, history}      institucional · general · charla · fuera de tema
                                          2. Solo si es institucional, busca en los documentos
                                             cargados (Qdrant) y elige los 5 fragmentos más útiles
                                          3. Si no encuentra nada suficiente, dice que no sabe
                                             y a dónde acudir. Nunca inventa datos de la universidad
                                          4. Si hay información, el modelo (Ollama) redacta la
                                             respuesta con esos fragmentos y el historial
                                          5. Si la respuesta corresponde a un formato, lo ofrece
                    ◀───────────────────     y, si el estudiante acepta, lo entrega con QR
 dice answer,          {answer, sources,  6. Guarda el turno en el log (datos personales ocultos)
 muestra QR             downloads}
```

- **Fuera de tema** ("¿quién ganó el partido?") responde con un mensaje fijo, sin llamar al modelo.
- **General** ("¿qué es un crédito académico?") responde con conocimiento general y un aviso de que
  no viene de los documentos de la universidad.
- **Charla** (saludos, gracias, "¿cómo te llamas?") responde breve.
- **Institucional** es lo que importa: trámites, requisitos y normas, siempre basados en los documentos.

---

## Probar juntos con ngrok

Pasos para quien corre el backend:

1. **Poner contraseña al mantenedor antes de exponerlo.** Con ngrok la URL es pública: sin
   contraseña, cualquiera que la tenga podría borrar documentos. Ver
   [Contraseña del mantenedor](#contraseña-del-mantenedor).
2. Levantar todo: `.\scripts\start-sara.ps1 -NoFrontend` desde la raíz del proyecto.
3. En otra terminal: `ngrok http 8000`. Copiar la URL `https://….ngrok-free.app` que muestra.
4. **Para que los QR funcionen desde un celular,** poner esa URL en el `backend/.env` y reiniciar
   el backend:
   ```
   PUBLIC_BASE_URL=https://xxxx.ngrok-free.app
   ```
   Con `localhost`, el QR se genera pero el celular no puede abrirlo. Cada vez que ngrok cambie de
   URL hay que actualizarlo.
5. Pasarle la URL al compañero de Unity.

Del lado de Unity:

- `baseUrl = "https://xxxx.ngrok-free.app"` (sin barra al final).
- **Enviar la cabecera `ngrok-skip-browser-warning: true`** en cada petición. Sin ella, ngrok gratuito
  puede responder con una página HTML de aviso en lugar del JSON. El [ejemplo en C#](#ejemplo-en-c)
  ya la incluye.
- Al escanear un QR con el celular, ngrok gratuito puede mostrar primero esa misma página de aviso;
  basta con pulsar *Visit Site*. Con un servidor real o con enlaces de OneDrive no pasa.

---

## Petición

**`POST /api/chat`** · `Content-Type: application/json`

```json
{
  "message": "sí",
  "history": [
    { "role": "user", "content": "¿Cómo cancelo el semestre?" },
    { "role": "assistant", "content": "¡Hola! Soy Sara, … ¿Quieres el formato R-GA004 (Formato de cancelacion de semestre) para descargarlo?" }
  ],
  "conversation_id": "3f1c2a9e-7b4d-4e21-9a6f-0c8d5e2b1a77"
}
```

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `message` | string | Sí | Lo que dijo el estudiante ahora |
| `history` | lista | Sí (vacía en el primer mensaje) | Turnos anteriores de **esta** conversación, en orden |
| `history[].role` | `"user"` o `"assistant"` | Sí | Quién lo dijo |
| `history[].content` | string | Sí | El texto tal cual, **sin recortar** |
| `conversation_id` | string (máx. 64) | No | Un GUID nuevo por conversación, renovado al borrarla. Solo agrupa los turnos en el log del mantenedor; sin él el chat funciona igual |

Cabeceras:

| Cabecera | Cuándo |
|---|---|
| `Content-Type: application/json` | Siempre |
| `ngrok-skip-browser-warning: true` | Mientras se pruebe a través de ngrok |
| `X-Kiosk-Key: <clave>` | Solo si el backend define `KIOSK_API_KEY`. Sin clave configurada no hace falta |

No hay que recortar el historial: el servidor se queda con lo que cabe en la memoria del modelo y
conserva siempre el primer mensaje del estudiante.

---

## Ejemplo real

Conversación de dos turnos capturada del backend. Los fragmentos de `sources` están acortados.

**Turno 1** · `history: []` · tardó 6,9 s

```json
{
  "question": "¿Cómo cancelo el semestre?",
  "answer": "¡Hola! Soy Sara, la asistente académica de la Universidad Santiago de Cali. Para cancelar el semestre debes estar matriculado y diligenciar el formato R-GA004, radicarlo en la Secretaría Académica dentro de las fechas establecidas en el calendario académico. Además, es necesario adjuntar soportes como carta de justificación, copia del recibo de pago y copia del documento de identidad.\n\n¿Quieres el formato R-GA004 (Formato de cancelacion de semestre) para descargarlo?",
  "sources": [
    {
      "filename": "Guia-Sara-Actualizada.pdf",
      "score": 1.17,
      "chunk": "Cancelación de semestre\n\n“Entendido esta como un acto mediante el cual se pierde la calidad de estudiante” …"
    },
    {
      "filename": "Guia-Sara-Actualizada.pdf",
      "score": -0.65,
      "chunk": "Cancelación de Cursos o Créditos\n\nEntendida esta como un acto mediante el cual se modifica la matrícula. …"
    }
  ],
  "downloads": []
}
```

**Turno 2** · el estudiante dice `"sí"` · instantáneo

```json
{
  "question": "sí",
  "answer": "Escanea el código QR para descargar el formato.",
  "sources": [],
  "downloads": [
    {
      "document_id": "89840ca3-bfa0-47ac-8df8-c99239ffadf9",
      "filename": "FORMATO_DE_CANCELACION_DE_SEMESTRE.pdf",
      "url": "https://<servidor>/api/documents/download?token=ODk4NDBj…",
      "qr_url": "https://<servidor>/api/documents/download/qr?token=ODk4NDBj…",
      "expires_at": "2026-11-12T13:40:38Z"
    }
  ]
}
```

| Campo | Uso en el quiosco |
|---|---|
| `answer` | Lo que dice el avatar. Puede traer saltos de línea (`\n\n`) |
| `downloads` | Formatos para descargar. **Mostrar QR solo cuando no viene vacío**, nunca por el texto. Ver [Formatos y QR](#formatos-descargables-qr) |
| `sources` | Documentos de los que salió la respuesta; vacío si no se buscó. Opcional mostrarlo |
| `question` | Eco de la pregunta; no hace falta usarlo |

`score` no es un porcentaje y puede ser negativo: no mostrarlo al estudiante.

### Respuestas que también son `200`

No son errores; el avatar las dice como cualquier otra:

- **No está en los documentos:** *"No encontré información suficiente en los documentos para responder
  esa pregunta. Puedes consultarlo en la Secretaría Académica…"* (con los datos de atención del perfil).
- **Tema ajeno a la universidad:** *"Solo puedo ayudarte con los documentos de la institución y con
  temas académicos…"*

### Errores

| Código | Significa | Qué hacer |
|---|---|---|
| `401` | Falta la `X-Kiosk-Key` o no es válida (solo si el backend la exige) | Revisar la clave configurada en Unity |
| `422` | JSON mal formado (falta `message`, `role` inválido…) | Error del cliente: revisar el cuerpo |
| `429` | Más de 20 mensajes por minuto desde el mismo equipo | Esperar; trae `Retry-After: 60`. Con uso normal no ocurre |
| `503` | Falla un servicio interno (modelo de IA o base de documentos) | Decir "No estoy disponible en este momento" y **no** tocar el historial |

---

## Reglas de la conversación

### La memoria la guarda el quiosco

El servidor **no guarda conversaciones**. Cada petición lleva el historial completo, el servidor
responde y lo olvida. Por eso:

- **Para recordar,** se envía siempre el historial.
- **Para olvidar,** se vacía la lista. No hay que avisar al servidor.
- Dos quioscos nunca comparten conversación, aunque usen el mismo backend.

### Al recibir cada respuesta

Añadir **dos** turnos al historial: la pregunta del estudiante y la respuesta.

```
history += { role: "user",      content: message }
history += { role: "assistant", content: answer  }
```

Si la petición falla, no se añade nada: el estudiante puede repetir la pregunta.

### Primer mensaje

Se envía con `history: []`. El backend antepone el saludo ("¡Hola! Soy Sara, la asistente académica
de…"), así que **Unity no debe añadir otro**. En los mensajes siguientes ya no saluda.

### Una pregunta a la vez

No enviar otra pregunta hasta recibir la respuesta. Mientras tanto, mostrar al avatar "pensando".

### Tiempos de respuesta

Medidos en la máquina de desarrollo (GPU RTX 3060) con 50 preguntas de prueba:

| Tipo de pregunta | Tiempo |
|---|---|
| Aceptar un formato ("sí") | Instantáneo |
| Saludo, despedida, "¿cómo te llamas?" | 0,3–2 s |
| Fuera de tema | ~1 s |
| Académica general | 2–3 s |
| Sobre la universidad (busca en documentos) | 5–13 s; mediana ~6 s |
| **Primera pregunta tras arrancar el servidor** | ~10 s si se arrancó con `start-sara.ps1` (precarga el modelo); varios minutos si no |

Timeout recomendado: **60 s**.

### Cuándo borrar la conversación (reset)

Borrar = vaciar `history`, generar un `conversation_id` nuevo y volver a la pantalla de espera. Hay
que hacerlo:

1. **Si el estudiante pulsa "Terminar conversación".**
2. **Tras 60 s sin interacción:** aparece "¿Sigues ahí?" con una **cuenta atrás de 10 s** y un botón
   "Sigo aquí". Cualquier interacción cancela el aviso. Si llega a 0, se borra. En total, **70 s**
   de inactividad.
3. **Si el quiosco detecta que no hay nadie delante** (cámara o sensor), si lo tiene. Es más fiable
   que el contador; el contador queda de respaldo.

Además:

- **El contador no corre mientras se espera una respuesta.**
- **En la pantalla de espera no corre,** porque no hay nada que borrar.
- **Al borrar se cancela la petición en curso,** para que la respuesta tardía de un estudiante no le
  aparezca al siguiente.

El chat del mantenedor usa estos mismos valores (`IDLE_TIMEOUT_MS = 60_000`, `IDLE_COUNTDOWN_S = 10`
en `frontend/src/app/features/chat/chat.component.ts`), así que sirve para probar el comportamiento.

### Privacidad en el quiosco

- La conversación vive **solo en memoria**: nunca en disco, `PlayerPrefs` ni logs de Unity. Los
  estudiantes dicen su nombre, su cédula y otros datos.
- Al cerrar o reiniciar la aplicación la conversación se pierde, y es lo correcto.

---

## Formatos descargables (QR)

En el mantenedor hay dos tipos de documento:

- **Información** (reglamentos, guías): Sara responde con su contenido. Nunca se descargan.
- **Formatos** (por ejemplo R-GA004, cancelación de semestre): Sara no los lee; los **ofrece** cuando
  la pregunta es sobre su trámite.

El formato **se ofrece y solo se entrega si el estudiante acepta**. Lo resuelve el servidor con el
historial; Unity no tiene que detectar nada:

```
Estudiante: ¿Cómo cancelo el semestre?
Sara:       Para cancelar el semestre debes… ¿Quieres el formato R-GA004 (…) para descargarlo?
            → downloads: []                      (solo la oferta, sin QR)
Estudiante: sí
Sara:       Escanea el código QR para descargar el formato.
            → downloads: [ { …, qr_url } ]       (aquí se muestra el QR)
```

- Si el estudiante pide el formato directamente ("pásame el formato de cancelación"), se entrega en
  esa misma respuesta.
- Si responde "no", no llega ningún QR.
- Se entregan como máximo 3 formatos a la vez.

Para cada elemento de `downloads`:

1. **Mostrar la imagen de `qr_url`.** Es un PNG ya generado por el servidor (se descarga con
   `UnityWebRequestTexture.GetTexture`, con las mismas cabeceras que el chat), así que Unity no
   necesita ninguna librería de QR.
2. **Mostrar `filename` junto al QR,** para que el estudiante sepa qué se lleva.
3. **Quitar el QR al terminar la conversación.** Además, según `expires_at`:
   - **Con fecha:** enlace del backend, firmado, que **caduca a los 15 minutos** (después devuelve
     `404`). Quitar el QR al pasar esa hora.
   - **`null`:** `url` es el enlace público del formato en OneDrive o Drive y no caduca.

El enlace firmado no se puede modificar para bajar otro documento. Si en el mantenedor un formato
deja de serlo, sus enlaces dejan de funcionar al instante.

**Requisito de red:** el celular del estudiante tiene que poder abrir `url`. Con enlaces del backend,
la dirección sale de `PUBLIC_BASE_URL` (ver [ngrok](#probar-juntos-con-ngrok)); con enlaces de
OneDrive funciona desde cualquier celular con internet.

---

## Comprobar que el servidor está listo

**`GET /health`** (sin el prefijo `/api`, sin autenticación)

```json
{ "status": "ok", "service": "Sara", "version": "1.0.0", "database": "connected", "qdrant": "connected", "ollama": "connected" }
```

Sirve para mostrar "fuera de servicio" al arrancar el quiosco. **No basta con `status`**: siempre vale
`"ok"` mientras la API responda. Hay que comprobar que `database`, `qdrant` y `ollama` estén en
`"connected"`.

---

## Ejemplo en C#

```csharp
using System;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

[Serializable] public class ChatTurn { public string role; public string content; }
[Serializable] public class ChatRequest { public string message; public List<ChatTurn> history; public string conversation_id; }
[Serializable] public class ChatSource { public string filename; public float score; public string chunk; }
[Serializable] public class ChatDownload { public string document_id; public string filename; public string url; public string qr_url; public string expires_at; }
[Serializable] public class ChatResponse { public string question; public string answer; public List<ChatSource> sources; public List<ChatDownload> downloads; }

public class SaraClient : MonoBehaviour
{
    [SerializeField] string baseUrl = "http://localhost:8000";  // o la URL de ngrok, sin barra final
    [SerializeField] string kioskKey = "";                       // vacío si el backend no la exige

    // La memoria de la conversación: solo en RAM, nunca en disco.
    readonly List<ChatTurn> history = new();
    string conversationId = Guid.NewGuid().ToString();
    UnityWebRequest pending;
    int generation;  // cambia al borrar: descarta respuestas de la conversación anterior

    public void Ask(string message, Action<ChatResponse> onAnswer, Action onUnavailable)
    {
        if (pending != null) return;  // una pregunta a la vez
        StartCoroutine(Send(message, onAnswer, onUnavailable));
    }

    System.Collections.IEnumerator Send(string message, Action<ChatResponse> onAnswer, Action onUnavailable)
    {
        var body = JsonUtility.ToJson(new ChatRequest { message = message, history = history, conversation_id = conversationId });
        using var req = new UnityWebRequest($"{baseUrl}/api/chat", "POST")
        {
            uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(body)),
            downloadHandler = new DownloadHandlerBuffer(),
            timeout = 60,
        };
        SetHeaders(req);
        req.SetRequestHeader("Content-Type", "application/json");

        var startedIn = generation;
        pending = req;
        yield return req.SendWebRequest();

        // Se terminó la conversación mientras se esperaba: la respuesta ya no es de nadie.
        if (startedIn != generation) yield break;
        pending = null;

        if (req.result != UnityWebRequest.Result.Success)
        {
            onUnavailable();  // 503, 429, timeout o sin red: no se toca el historial
            yield break;
        }

        var res = JsonUtility.FromJson<ChatResponse>(req.downloadHandler.text);
        history.Add(new ChatTurn { role = "user", content = message });
        history.Add(new ChatTurn { role = "assistant", content = res.answer });
        onAnswer(res);  // decir res.answer; si res.downloads trae elementos, mostrar sus QR
    }

    // Imagen del QR de un formato entregado.
    public System.Collections.IEnumerator LoadQr(ChatDownload download, Action<Texture2D> onLoaded)
    {
        using var req = UnityWebRequestTexture.GetTexture(download.qr_url);
        SetHeaders(req);
        yield return req.SendWebRequest();
        if (req.result == UnityWebRequest.Result.Success)
            onLoaded(DownloadHandlerTexture.GetContent(req));
    }

    // Botón "Terminar", fin de la cuenta atrás o nadie delante del quiosco.
    public void EndConversation()
    {
        generation++;
        pending?.Abort();
        pending = null;
        history.Clear();
        conversationId = Guid.NewGuid().ToString();
    }

    void SetHeaders(UnityWebRequest req)
    {
        // Mientras se pruebe por ngrok gratuito: evita su página HTML de aviso.
        req.SetRequestHeader("ngrok-skip-browser-warning", "true");
        if (!string.IsNullOrEmpty(kioskKey)) req.SetRequestHeader("X-Kiosk-Key", kioskKey);
    }
}
```

---

## El mantenedor (para el equipo)

El mantenedor es la aplicación web (Angular, `http://localhost:4200`) donde se administra Sara.
Unity no lo usa, pero define lo que Sara sabe y cómo responde.

### Contraseña del mantenedor

Todo el mantenedor está protegido con **una contraseña compartida**. `/api/chat`, las descargas de
formatos y `/health` siguen siendo públicos, porque los usan el quiosco y los celulares.

Para configurarla, desde `backend/` con el entorno virtual activo:

```powershell
python -m scripts.hash_password
```

1. Pide la contraseña que se quiera usar (mínimo 10 caracteres), dos veces. No se ve al escribir.
2. Imprime una línea `ADMIN_PASSWORD_HASH=pbkdf2_sha256$…`: copiarla en `backend/.env`.
3. Añadir también `AUTH_SECRET=` con un texto largo y aleatorio. Sin él, reiniciar el backend cierra
   las sesiones.
4. Reiniciar el backend.

En el `.env` se guarda el código cifrado, nunca la contraseña. Para entrar se escribe la contraseña
del paso 1. La sesión dura 8 horas (`AUTH_TOKEN_TTL_HOURS`). Tras 10 intentos fallidos en un minuto,
el login se bloquea un minuto. Si se olvida la contraseña, se repiten los pasos con una nueva.

Sin `ADMIN_PASSWORD_HASH` el mantenedor queda abierto, lo que solo sirve para desarrollo; el backend
lo avisa al arrancar.

### Pantallas

| Pantalla | Para qué |
|---|---|
| **Inicio** | Estado de PostgreSQL, Qdrant y Ollama |
| **Estudio** | Chat de prueba con el mismo contrato y las mismas reglas que el quiosco |
| **Biblioteca** | Subir PDF, marcarlos como *Información* o *Formato*, procesarlos e indexarlos |
| **Explorar** | Búsqueda en los documentos, con tiempos por etapa |
| **Prompts** | Variantes de las instrucciones de Sara, sin tocar código |
| **Conversaciones** | Qué preguntan los estudiantes y dónde falla Sara |
| **Perfil** | Nombre del asistente, institución y datos de atención (los que da cuando no sabe algo) |

### Documentos cargados

- **Información:** se sube el PDF, se pulsa *Procesar* y luego *Indexar*. A partir de ahí Sara
  responde con su contenido. Las páginas escaneadas se leen con OCR.
- **Formatos:** se sube el PDF con una **descripción** de para qué sirve (es lo que se compara con la
  pregunta) y su **código** (R-GA004). Si no se escribe el código, se intenta leer del PDF. Los
  formatos no se indexan.
  - **Enlace público (opcional):** se puede pegar un enlace de OneDrive o Drive con acceso para
    cualquiera, o marcar *Subir a OneDrive* si está configurado. Con enlace público, el QR apunta ahí
    y no caduca.

Hoy hay cargados: la *Guía Sara* (información, 12 trámites académicos) y 5 formatos (R-GA001 a
R-GA005). Lo que no está en la guía (costos, horarios, grado, certificados, becas…) Sara no lo
responde: dice que no sabe y a dónde acudir.

### Log de conversaciones

Cada mensaje de `/api/chat` se guarda con la pregunta, la respuesta, el camino que tomó, si Sara
supo responder, el formato ofrecido o entregado y los tiempos. En la pantalla *Conversaciones* se
filtra por fecha, camino o "solo sin respuesta", y se exporta a CSV.

- **Datos personales ocultos:** cédulas, códigos, teléfonos y correos se reemplazan por `[numero]` o
  `[correo]` antes de guardar.
- **Borrado automático a los 30 días** (`CHAT_LOG_RETENTION_DAYS`).
- Se apaga con `CHAT_LOG_ENABLED=false`.

### Protecciones de `/api/chat`

- **Límite de 20 mensajes por minuto por equipo** (`CHAT_RATE_LIMIT_PER_MINUTE`): protege la GPU de
  ráfagas. Un estudiante normal no lo alcanza.
- **Clave del quiosco opcional** (`KIOSK_API_KEY`): si se define, solo responde a quien envíe
  `X-Kiosk-Key` con ese valor (o a una sesión del mantenedor).

---

## Pendiente del lado del servidor

Cosas que el avatar va a notar y que aún no están resueltas:

- **Formato para voz.** Algunas respuestas traen saltos de línea o listas pensadas para pantalla. Se
  puede ajustar sin tocar código con una variante de prompt ("responde en frases cortas, sin listas")
  desde *Prompts*.
- **Respuesta en streaming.** Hoy la respuesta llega completa al final. Para que el avatar empiece a
  hablar antes haría falta una versión de `/api/chat` que envíe el texto a medida que se genera.
- **Voz a texto y texto a voz.** Aún no está decidido si van en Unity o en el backend.
