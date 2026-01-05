from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


# Find .env file in project root (parent of backend/)
_env_file = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI API
    openai_api_key: str = ""

    # USDA FoodData Central (optional for MVP)
    usda_api_key: Optional[str] = None

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # CORS
    cors_origins: str = "http://localhost:5173"

    # File upload limits
    max_file_size_mb: int = 10

    # Database
    sqlite_db_path: str = "./data/nutrition_cache.db"

    # USDA cache
    usda_cache_expiry_days: int = 90

    # Rate limiting
    # Set to False for development/testing, True for production
    rate_limit_enabled: bool = False

    class Config:
        env_file = _env_file
        env_file_encoding = "utf-8"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.max_file_size_mb * 1024 * 1024


settings = Settings()
