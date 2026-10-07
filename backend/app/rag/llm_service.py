import json
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger("mini_rag_lab")


class LLMError(Exception):
    """No fue posible generar una respuesta (Ollama caido o modelo ausente)."""


def chat(messages: list[dict[str, str]]) -> str:
    """Envia la conversacion a Ollama (/api/chat) y devuelve el texto generado."""
    data = _post_chat({"messages": messages}, timeout=120.0)
    # Solo el conteo, nunca el texto: el historial trae datos personales del estudiante.
    # Excluye lo que Ollama reutilizo de la consulta anterior.
    logger.info(
        "Ollama proceso %s tokens de prompt (ventana %d, %d mensajes)",
        data.get("prompt_eval_count"),
        settings.LLM_NUM_CTX,
        len(messages),
    )
    return data.get("message", {}).get("content", "").strip()


def chat_structured(messages: list[dict[str, str]], schema: dict[str, Any], timeout: float) -> dict[str, Any]:
    """Respuesta forzada a un JSON con el esquema dado. Temperatura 0: es una decision, no texto."""
    data = _post_chat({"messages": messages, "format": schema}, timeout=timeout, temperature=0)
    try:
        return json.loads(data.get("message", {}).get("content", ""))
    except json.JSONDecodeError as exc:
        raise LLMError("El modelo no devolvio un JSON valido") from exc


def _post_chat(body: dict[str, Any], timeout: float, temperature: float | None = None) -> dict[str, Any]:
    url = f"{settings.OLLAMA_URL.rstrip('/')}/api/chat"
    # num_ctx igual en todas las llamadas: si cambia, Ollama recarga el modelo.
    options: dict[str, Any] = {"num_ctx": settings.LLM_NUM_CTX}
    if temperature is not None:
        options["temperature"] = temperature
    payload = {"model": settings.LLM_MODEL, "stream": False, "options": options, **body}
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("Fallo al generar respuesta con Ollama: %s", exc)
        raise LLMError from exc
    return response.json()
