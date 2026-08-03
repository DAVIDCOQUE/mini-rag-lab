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


def render_system_prompt(body: str) -> str:
    """Sustituye el marcador de fallback por la frase real del sistema.

    Se usa replace y no format para que las llaves que el usuario escriba en su propia
    variante no revienten con KeyError.
    """
    return body.replace(NO_ANSWER_PLACEHOLDER, NO_ANSWER_MESSAGE)


def build_prompt(question: str, chunks: list[str], system_prompt: str | None = None) -> str:
    """Combina las instrucciones, el contexto recuperado y la pregunta en un unico prompt.

    Sin system_prompt se usan las instrucciones del repositorio; con el, la variante
    elegida para esa consulta.
    """
    context = "\n\n".join(chunks)
    instructions = render_system_prompt(system_prompt or SYSTEM_PROMPT_TEMPLATE)
    return f"{instructions}\n\nContexto:\n{context}\n\nPregunta: {question}\n\nRespuesta:"
