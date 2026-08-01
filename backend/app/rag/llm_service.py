import logging

import httpx

from app.core.config import settings

logger = logging.getLogger("mini_rag_lab")


class LLMError(Exception):
    """No fue posible generar una respuesta (Ollama caido o modelo ausente)."""


def generate(prompt: str) -> str:
    """Envia el prompt a Ollama (/api/generate) y devuelve el texto generado."""
    url = f"{settings.OLLAMA_URL.rstrip('/')}/api/generate"
    payload = {"model": settings.LLM_MODEL, "prompt": prompt, "stream": False}
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("Fallo al generar respuesta con Ollama: %s", exc)
        raise LLMError from exc

    return response.json().get("response", "").strip()
