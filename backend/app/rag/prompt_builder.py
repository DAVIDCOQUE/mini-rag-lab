import re
import unicodedata
from collections.abc import Sequence

from app.schemas.chat import ChatTurn

NO_ANSWER_MESSAGE = "No encontré información suficiente en los documentos para responder esa pregunta."

# Marcador que las variantes de prompt pueden usar para referirse a la frase de
# fallback sin copiarla: asi cambiar NO_ANSWER_MESSAGE no deja prompts guardados
# instruyendo una frase distinta de la que devuelve el corte por umbral.
NO_ANSWER_PLACEHOLDER = "{no_answer}"

# Codigo reservado del prompt del repositorio. No es una fila en base de datos:
# es el comportamiento versionado al que se vuelve siempre que no haya otro elegido.
DEFAULT_PROMPT_CODE = "default"
DEFAULT_PROMPT_NAME = "Prompt por defecto del laboratorio"

SYSTEM_PROMPT_TEMPLATE = """Eres un asistente que responde preguntas EXCLUSIVAMENTE con base en el \
CONTEXTO que se te entrega mas abajo. El contexto es tu unica fuente de verdad: no existe \
ninguna otra fuente de informacion valida para esta tarea.

Reglas estrictas, sin excepciones:
- Usa unicamente la informacion contenida en el contexto para responder.
- Tienes PROHIBIDO usar tu conocimiento propio, general o de entrenamiento, incluso si \
crees saber la respuesta.
- Ignora por completo cualquier informacion que sepas del mundo fuera del contexto.
- No completes, asumas ni infieras datos que no esten explicitos en el contexto.
- No inventes nombres, fechas, cifras, procedimientos ni ningun otro dato que no aparezca \
en el contexto.
- Si la respuesta no aparece claramente en el contexto, responde EXACTAMENTE lo siguiente \
y nada mas, sin explicaciones ni disculpas adicionales: \
"{no_answer}"
- No menciones embeddings, Qdrant, documentos ni fragmentos.
- No digas frases como "según el contexto", "de acuerdo al texto proporcionado", \
"según la información proporcionada" ni ninguna variante que revele que estás \
citando un contexto.
- Responde de forma natural, clara y profesional, como si el conocimiento fuera propio, \
directamente y sin frases introductorias sobre el origen de la información."""


# Prompts de los caminos que no pasan por la base vectorial. Son cortos a proposito:
# el router ya decidio de que va el mensaje, asi que cada uno resuelve un solo caso en
# lugar de llevar dentro el arbol de decisiones completo.
SMALLTALK_PROMPT = """Eres el asistente academico de la universidad. El usuario te ha \
saludado, se ha presentado, te ha dado las gracias o pregunta algo sobre la propia \
conversacion (su nombre, lo que dijo antes).

Responde en espanol, con calidez y en una o dos frases como maximo. Si te dice su \
nombre, usalo. Si pregunta por algo dicho antes, respondelo con lo que aparece en la \
conversacion; si no aparece, dilo sin inventarlo. Ofrece ayuda con documentos de la \
institucion o dudas academicas.
No menciones documentos, contexto ni como funcionas por dentro."""

GENERAL_PROMPT = """Eres el asistente academico de la universidad. El usuario pregunta \
algo general sobre educacion o vida academica que no depende de esta institucion en \
concreto.

Responde en espanol con tu propio conocimiento, de forma breve y clara: dos o tres \
frases bastan. No anadas avisos sobre el origen de la informacion: el sistema los pone.
Si la pregunta necesitara un dato propio de la universidad para responderse bien, dilo en \
lugar de inventarlo."""

# Respaldo cuando la guia no cubre un concepto academico general. El aviso lo pone el
# codigo: el modelo lo omitia a veces.
CONCEPT_FALLBACK_PROMPT = """Eres el asistente academico de la universidad. Explica en espanol, \
en dos o tres frases claras, el concepto academico que pregunta el estudiante. No menciones \
datos de ninguna universidad concreta (cifras, normas, lugares ni personas)."""
GENERAL_NOTICE = "Esto es información general: no aparece en los documentos de la universidad."

# Sin LLM: el camino fuera de ambito no merece una generacion.
OFF_TOPIC_MESSAGE = (
    "Solo puedo ayudarte con los documentos de la institución y con temas académicos. "
    "¿Quieres preguntarme algo sobre eso?"
)


# Respuesta fija y no generada: con el nombre en el prompt, llama3.1:8b lo atribuia a
# "equipos de investigacion" o confundia al estudiante con el autor.
CREATOR_MESSAGE = (
    "Me desarrolló un equipo de estudiantes de la Universidad Santiago de Cali, "
    "con la colaboración de David Sánchez."
)
_CREATOR_QUESTION = re.compile(
    # Dirigida al asistente ("te", "tu"): "¿quien creo la politica?" es otra pregunta.
    r"\b(quien|quienes)\s+te\s+(creo|crearon|hizo|hicieron|desarrollo|desarrollaron|programo|programaron|diseno)\b"
    r"|\btu\s+(creador|creadora|desarrollador|desarrolladora|autor|autora)\b"
)


def asks_about_creator(question: str) -> bool:
    """Si el mensaje pregunta quien creo al asistente, sin acentos ni mayusculas."""
    decomposed = unicodedata.normalize("NFD", question.lower())
    text = "".join(c for c in decomposed if not unicodedata.combining(c))
    return bool(_CREATOR_QUESTION.search(text))


# Quien, donde, cuando, cuanto, a que hora o un contacto piden un dato concreto, nunca un
# concepto. El router a veces marcaba "¿quien es el rector?" como concepto y se respondia
# con la definicion del cargo.
_SPECIFIC_DATA_QUESTION = re.compile(
    r"\b(quien|quienes|donde|cuando|cuanto|cuanta|cuantos|cuantas|horario|hora|telefono|celular|correo|extension)\b"
)


def asks_specific_data(question: str) -> bool:
    """Si el mensaje pide un dato concreto (persona, lugar, fecha, costo, contacto)."""
    decomposed = unicodedata.normalize("NFD", question.lower())
    text = "".join(c for c in decomposed if not unicodedata.combining(c))
    return bool(_SPECIFIC_DATA_QUESTION.search(text))


# El formato se ofrece y solo se entrega si el estudiante acepta o lo pide. Textos fijos:
# la oferta lleva el nombre exacto del formato para reconocerlo en el turno siguiente.
FORM_DELIVERY_MESSAGE = "Escanea el código QR para descargar el formato."
FORMS_DELIVERY_MESSAGE = "Escanea los códigos QR para descargar los formatos."

_AFFIRMATIVE = re.compile(
    r"^\W*(si|sip|claro|dale|ok|okay|bueno|listo|perfecto|obvio|de una|por favor|porfa|"
    r"me lo|pasamelo|mandamelo|enviamelo|muestramelo|quiero|lo quiero|va|vale)\b"
)
_FORM_REQUEST = re.compile(r"\bformatos?\b")


def form_offer(names: list[str]) -> str:
    if len(names) == 1:
        return f"¿Quieres el formato {names[0]} para descargarlo?"
    return f"¿Quieres los formatos {', '.join(names[:-1])} y {names[-1]} para descargarlos?"


def form_delivery(count: int) -> str:
    return FORM_DELIVERY_MESSAGE if count == 1 else FORMS_DELIVERY_MESSAGE


def is_affirmative(message: str) -> bool:
    """Respuesta corta de aceptacion ("si", "dale", "si porfa"). Una frase larga es otra pregunta."""
    text = _plain(message)
    return len(text.split()) <= 6 and bool(_AFFIRMATIVE.search(text))


def asks_for_form(message: str) -> bool:
    """El estudiante pide el formato directamente: se entrega sin preguntar."""
    return bool(_FORM_REQUEST.search(_plain(message)))


def _plain(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


# Identidad generica a proposito: el nombre de la institucion o del asistente no va en el
# codigo. Quien lo quiera, lo escribe en una variante de prompt desde la UI.
FIRST_TURN_GREETING = "¡Hola! Soy el asistente académico de la universidad."

# Se anaden al prompt de sistema solo en el chat; /search son consultas sueltas.
FIRST_TURN_INSTRUCTION = (
    "Es el primer mensaje de la conversacion: empieza saludando de forma breve y cordial "
    "y despues responde."
)
FOLLOW_UP_INSTRUCTION = "La conversacion ya empezo: no vuelvas a saludar ni a presentarte."
# Para cuando el saludo se antepone fijo a la respuesta del modelo.
NO_GREETING_INSTRUCTION = "El saludo ya esta dado: no saludes ni te presentes, responde directamente."

# Estimacion sin tokenizador: con llama3.1 el espanol midio ~4,15 caracteres por token;
# 4 deja margen a favor de no desbordar la ventana.
CHARS_PER_TOKEN = 4

Message = dict[str, str]


def estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN + 1


def fit_history(history: Sequence[ChatTurn], max_tokens: int, answer_chars: int) -> list[Message]:
    """Turnos previos que caben en max_tokens, del mas reciente hacia atras.

    El primer mensaje del usuario se conserva siempre: es donde suele decir quien es y
    que busca, y es lo que mas se nota si se olvida.
    """
    turns = [
        {
            "role": turn.role,
            "content": _shorten(turn.content, answer_chars) if turn.role == "assistant" else turn.content,
        }
        for turn in history
    ]
    if not turns or max_tokens <= 0:
        return []

    pinned = turns[0] if turns[0]["role"] == "user" else None
    rest = turns[1:] if pinned else turns
    budget = max_tokens - (estimate_tokens(pinned["content"]) if pinned else 0)
    if budget < 0:
        return []

    window: list[Message] = []
    for turn in reversed(rest):
        cost = estimate_tokens(turn["content"])
        if cost > budget:
            break
        window.append(turn)
        budget -= cost
    window.reverse()

    # Si se recorto, una respuesta al inicio del tramo quedaria sin la pregunta que la origino.
    while window and window[0]["role"] == "assistant" and len(window) < len(rest):
        window.pop(0)

    return ([pinned] if pinned else []) + window


def with_turn_instruction(
    system_prompt: str, history: Sequence[ChatTurn] | None, llm_greets: bool = True
) -> str:
    """Anade la instruccion de saludo segun el turno. Sin historial (None) no es una conversacion.

    llm_greets=False: el saludo del primer turno lo pone el codigo, el modelo no saluda.
    """
    if history is None:
        return system_prompt
    if history:
        instruction = FOLLOW_UP_INSTRUCTION
    else:
        instruction = FIRST_TURN_INSTRUCTION if llm_greets else NO_GREETING_INSTRUCTION
    return f"{system_prompt}\n\n{instruction}"


def build_messages(system_prompt: str, user_content: str, history: Sequence[Message] = ()) -> list[Message]:
    """Sistema, historial y mensaje actual, en ese orden.

    Ollama reutiliza el inicio del prompt si no cambio desde la consulta anterior: con
    el contenido nuevo al final, el historial ya leido no se vuelve a procesar.
    """
    return [{"role": "system", "content": system_prompt}, *history, {"role": "user", "content": user_content}]


# Va al final, junto a la pregunta: llama3.1:8b obedece mas lo ultimo que lee. Sin el,
# 2 de 12 respuestas largas decian "segun el contexto"; con el, 0 de 18.
CONTEXT_REMINDER = "Responde directamente y como conocimiento propio, sin aludir a de donde sale la informacion."


def build_context_message(question: str, chunks: list[str]) -> str:
    """Mensaje del usuario con el contexto recuperado delante de la pregunta."""
    context = "\n\n".join(chunks)
    return f"Contexto:\n{context}\n\nPregunta: {question}\n\n{CONTEXT_REMINDER}"


def institutional_instructions(system_prompt: str | None = None) -> str:
    """Instrucciones del camino institucional: la variante elegida o, sin ella, las del repositorio."""
    return render_system_prompt(system_prompt or SYSTEM_PROMPT_TEMPLATE)


def _shorten(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def render_system_prompt(body: str) -> str:
    """Sustituye el marcador de fallback por la frase real del sistema.

    Se usa replace y no format para que las llaves que el usuario escriba en su propia
    variante no revienten con KeyError.
    """
    return body.replace(NO_ANSWER_PLACEHOLDER, NO_ANSWER_MESSAGE)
