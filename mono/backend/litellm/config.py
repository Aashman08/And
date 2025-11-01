"""Configuration management for LiteLLM service."""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """LiteLLM service settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys
    openai_api_key: str = ""
    
    # Models
    litellm_summarization_model: str = "gpt-4o-mini"


# Global settings instance
settings = Settings()

