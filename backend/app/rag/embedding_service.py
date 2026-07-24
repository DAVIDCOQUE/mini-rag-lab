import logging

import httpx

from app.core.config import settings

logger = logging.getLogger("mini_rag_lab")


class EmbeddingError(Exception):
    """No fue posible generar embeddings (Ollama caido o modelo ausente)."""


class EmbeddingService:
    """Genera embeddings a partir de texto usando la API HTTP de Ollama (/api/embed)."""

    def __init__(self) -> None:
        # URL y modelo salen del .env; nunca hardcodeados.
        self.base_url = settings.OLLAMA_URL.rstrip("/")
        self.model = settings.EMBEDDING_MODEL

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Devuelve un vector por cada texto (en el mismo orden)."""
        url = f"{self.base_url}/api/embed"
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, json={"model": self.model, "input": texts})
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Fallo al generar embeddings con Ollama: %s", exc)
            raise EmbeddingError from exc
        return response.json()["embeddings"]

    def embed_query(self, text: str) -> list[float]:
        """Embedding de una sola consulta."""
        return self.embed([text])[0]
