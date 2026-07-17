from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracion central de la aplicacion (cargada desde variables de entorno / .env)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Aplicacion
    PROJECT_NAME: str = "Mini RAG Lab"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # Base de datos PostgreSQL
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/mini_rag_lab"

    # CORS: origenes permitidos para el frontend Angular
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:4200"]


@lru_cache
def get_settings() -> Settings:
    """Instancia unica de settings reutilizada en toda la app."""
    return Settings()


settings = get_settings()
