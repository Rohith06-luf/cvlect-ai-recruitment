"""
CVlect AI — Application Configuration
All settings loaded from environment variables / .env file.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Central configuration loaded from environment variables."""

    # ---- Database ----
    database_url: str = "sqlite:///./cvlect.db"

    # ---- JWT Authentication ----
    jwt_secret_key: str = "change-this-to-a-strong-random-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440  # 24 hours

    # ---- NVIDIA NIM API ----
    nvidia_api_key: Optional[str] = None
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "z-ai/glm-5.3-flash"

    # ---- File Upload ----
    max_upload_size_mb: int = 10
    upload_dir: str = "./uploads"

    # ---- NLP Models ----
    spacy_model: str = "en_core_web_sm"
    sentence_transformer_model: str = "all-MiniLM-L6-v2"

    # ---- Server ----
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def has_nvidia_api(self) -> bool:
        return bool(self.nvidia_api_key)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)
