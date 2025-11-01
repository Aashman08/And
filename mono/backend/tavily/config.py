"""Configuration management for Tavily service."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Tavily service settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys
    tavily_api_key: str = ""
    
    # Service settings
    api_host: str = "0.0.0.0"
    api_port: int = 8003


# Global settings instance
settings = Settings()

