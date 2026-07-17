from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracion central de la app. Todos los valores provienen de variables de entorno / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Aplicacion ---
    PROJECT_NAME: str = "Mini RAG Lab"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api"

    # --- Servidor (uvicorn) ---
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # --- PostgreSQL ---
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "mini_rag_lab"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"

    # --- Qdrant ---
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # --- Ollama ---
    OLLAMA_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "qwen2.5:7b"

    # --- CORS: origenes del frontend Angular (formato JSON en .env) ---
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:4200"]

    @property
    def DATABASE_URL(self) -> str:
        """URL de conexion SQLAlchemy construida a partir de las piezas POSTGRES_*."""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    """Instancia unica de settings reutilizada en toda la app."""
    return Settings()


settings = get_settings()
