import logging
import time

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import LLMService, OllamaConnectionError

logger = logging.getLogger("mini_rag_lab")

router = APIRouter(tags=["chat"])
llm_service = LLMService()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Reenvia el mensaje del usuario a Ollama y devuelve la respuesta del modelo."""
    logger.info("Pregunta recibida: %s", request.message)

    start = time.perf_counter()
    try:
        answer = llm_service.generate(request.message)
    except OllamaConnectionError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con Ollama.")
    elapsed = time.perf_counter() - start

    logger.info("Respuesta del modelo '%s' en %.2fs", settings.LLM_MODEL, elapsed)
    return ChatResponse(response=answer)
