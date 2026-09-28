from functools import lru_cache
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application and external service configuration loaded from environment variables."""

    # Application settings
    app_name: str = Field(default="Hindsight Incident Response Agent", validation_alias="APP_NAME")
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    app_host: str = Field(default="127.0.0.1", validation_alias="APP_HOST")
    app_port: int = Field(default=8000, validation_alias="APP_PORT")
    debug: bool = Field(default=False, validation_alias="DEBUG")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        validation_alias="CORS_ORIGINS",
    )

    # Hindsight Memory Configuration
    hindsight_base_url: str = Field(
        default="http://localhost:8888",
        validation_alias="HINDSIGHT_BASE_URL",
        description="URL of the Hindsight server (e.g., http://localhost:8888 or https://api.hindsight.vectorize.io)",
    )
    hindsight_api_key: Optional[str] = Field(
        default=None,
        validation_alias="HINDSIGHT_API_KEY",
        description="API key for Hindsight Cloud or protected self-hosted instance",
    )
    hindsight_bank_id: str = Field(
        default="incident-response-bank",
        validation_alias="HINDSIGHT_BANK_ID",
        description="Target memory bank ID for storing and retrieving incident context",
    )
    hindsight_timeout: float = Field(
        default=10.0,
        validation_alias="HINDSIGHT_TIMEOUT",
        description="Request timeout in seconds for Hindsight operations",
    )

    @property
    def cors_origin_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        if not self.cors_origins:
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
