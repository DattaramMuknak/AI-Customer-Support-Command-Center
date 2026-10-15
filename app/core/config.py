"""
Centralized application configuration.
Loads from environment variables / .env file using pydantic-settings.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    app_name: str = "AI Customer Support Agent Platform"
    app_env: str = "development"
    app_version: str = "1.0.0"
    debug: bool = True
    secret_key: str = "change-this-to-a-random-secret-in-production"
    access_token_expire_minutes: int = 60

    # --- Database ---
    database_url: str = "mysql+pymysql://support_user:support_pass@localhost:3306/rag"

    # --- Groq ---
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_fallback_model: str = "openai/gpt-oss-20b"

    # --- Pinecone ---
    pinecone_api_key: str = ""
    pinecone_environment: str = "us-east-1"
    pinecone_index_name: str = "support-kb-index"
    embedding_dimension: int = 384

    # --- Embeddings ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- MLflow ---
    mlflow_tracking_uri: str = "http://localhost:5000"
    mlflow_experiment_name: str = "ai-support-agent"

    # --- Retrieval ---
    max_retrieval_docs: int = 5
    similarity_threshold: float = 0.65

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — avoids re-parsing env on every call."""
    return Settings()


settings = get_settings()
