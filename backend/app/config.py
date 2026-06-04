"""Application configuration loaded from environment variables."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Security
    SECRET_KEY: str = "change-me-in-production-please-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12  # 12 hours

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_CHAT_MODEL: str = "gemini-1.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"

    # Storage paths
    DATA_DIR: str = "/data"
    SQLITE_PATH: str = "/data/app.db"
    CHROMA_DIR: str = "/data/chroma"
    UPLOAD_DIR: str = "/data/uploads"

    # Default admin (used by the init_admin bootstrap script)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_EMAIL: str = "admin@example.com"

    # RAG params
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    RETRIEVAL_K: int = 5

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> "Settings":
    return Settings()


settings = get_settings()
