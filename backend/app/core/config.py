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
        default="http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
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

    # LLM Reasoning Engine Configuration
    llm_provider: str = Field(
        default="openai",
        validation_alias="LLM_PROVIDER",
        description="LLM provider: 'openai', 'gemini', 'groq', 'ollama', or 'heuristic'",
    )
    llm_api_key: Optional[str] = Field(
        default=None,
        validation_alias="LLM_API_KEY",
        description="API key for the LLM provider (leave blank for heuristic fallback)",
    )
    llm_model: str = Field(
        default="gpt-4o-mini",
        validation_alias="LLM_MODEL",
        description="Model identifier (e.g., 'gpt-4o-mini', 'gemini-1.5-flash', 'llama3-70b')",
    )
    llm_base_url: str = Field(
        default="https://api.openai.com/v1",
        validation_alias="LLM_BASE_URL",
        description="OpenAI-compatible API base URL",
    )
    llm_temperature: float = Field(
        default=0.2,
        validation_alias="LLM_TEMPERATURE",
        description="Sampling temperature for incident reasoning",
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
