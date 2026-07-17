import logging

import httpx

from app.core.config import settings

logger = logging.getLogger("mini_rag_lab")


class OllamaConnectionError(Exception):
    """Se lanza cuando no es posible comunicarse con Ollama."""


class LLMService:
    """Encapsula la comunicacion con Ollama a traves de su API HTTP oficial."""

    def __init__(self) -> None:
        # URL y modelo salen del .env; nunca hardcodeados.
        self.base_url = settings.OLLAMA_URL.rstrip("/")
        self.model = settings.LLM_MODEL

    def generate(self, message: str) -> str:
        """Envia el mensaje del usuario al modelo y devuelve la respuesta en texto plano."""
        url = f"{self.base_url}/api/generate"
        payload = {"model": self.model, "prompt": message, "stream": False}
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Fallo la comunicacion con Ollama: %s", exc)
            raise OllamaConnectionError from exc

        return response.json().get("response", "").strip()
