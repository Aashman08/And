"""Configuration management using pydantic-settings."""
import os
import sys
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    admin_bearer_token: str

    # Database
    database_url: str
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "r2d"
    postgres_user: str = "r2d"
    postgres_password: str = "r2d"

    # OpenSearch
    opensearch_host: str = "opensearch"
    opensearch_port: int = 9200
    opensearch_username: str = "admin"
    opensearch_password: str = "admin"

    # Pinecone
    pinecone_api_key: str
    pinecone_index_name: str = "r2d-chunks"
    pinecone_cloud: str = "aws"
    pinecone_environment: str = "us-west-2"

    # LiteLLM models
    openai_api_key: str
    cohere_api_key: str
    litellm_summarization_model: str = "gpt-4o-mini"
    litellm_rerank_model: str = "command-r"

    # Embeddings
    embedding_model: str = "intfloat/e5-base-v2"

    # Tavily for web search
    tavily_api_key: str

    # Application settings
    pythonhashseed: int = 0

    def validate_required_keys(self) -> None:
        """Validate that all required API keys are present."""
        missing = []

        if not self.openai_api_key or self.openai_api_key.startswith("your-"):
            missing.append("OPENAI_API_KEY")
        if not self.cohere_api_key or self.cohere_api_key.startswith("your-"):
            missing.append("COHERE_API_KEY")
        if not self.pinecone_api_key or self.pinecone_api_key.startswith("your-"):
            missing.append("PINECONE_API_KEY")
        if not self.tavily_api_key or self.tavily_api_key.startswith("your-"):
            missing.append("TAVILY_API_KEY")

        if missing:
            print(
                f"ERROR: Missing required API keys: {', '.join(missing)}",
                file=sys.stderr,
            )
            print(
                "Please set these environment variables in your .env file.",
                file=sys.stderr,
            )
            sys.exit(1)

    @property
    def opensearch_url(self) -> str:
        """Construct OpenSearch URL."""
        return f"http://{self.opensearch_host}:{self.opensearch_port}"


# Global settings instance
settings = Settings()

# Validate on import
settings.validate_required_keys()
