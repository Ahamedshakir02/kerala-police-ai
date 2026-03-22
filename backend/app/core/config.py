from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://kpai:kpai_secret@localhost:5432/kpai_db"

    # Security
    SECRET_KEY: str = "supersecretkey_change_in_production_32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Bhashini
    BHASHINI_API_KEY: str = ""
    BHASHINI_USER_ID: str = ""
    BHASHINI_PIPELINE_ID: str = "64392f96daac500b55c543cd"

    # Google Maps
    GOOGLE_MAPS_API_KEY: str = ""

    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # CORS — stored as JSON string in .env
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ML
    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"
    MODEL_CACHE_DIR: str = ".model_cache"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()
