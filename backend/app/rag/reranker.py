from fastembed.rerank.cross_encoder import TextCrossEncoder

from app.core.config import settings


class Reranker:
    """Reordena candidatos con un cross-encoder (lee pregunta + chunk juntos)."""

    def __init__(self) -> None:
        self.model_name = settings.RERANKER_MODEL
        self._model: TextCrossEncoder | None = None

    @property
    def model(self) -> TextCrossEncoder:
        # Carga perezosa: el modelo ONNX se descarga/inicializa en el primer uso.
        if self._model is None:
            self._model = TextCrossEncoder(model_name=self.model_name)
        return self._model

    def rerank(self, query: str, documents: list[str]) -> list[float]:
        """Devuelve un puntaje de relevancia por documento, en el mismo orden de entrada."""
        return list(self.model.rerank(query, documents))
