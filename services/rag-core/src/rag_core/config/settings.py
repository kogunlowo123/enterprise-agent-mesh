"""RAG core service settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class RAGCoreSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "postgresql://mesh:mesh@localhost:5432/mesh_db"
    opensearch_url: str = "http://localhost:9200"
    opensearch_index: str = "agent-mesh"
    embedding_model: str = "BAAI/bge-large-en-v1.5"
    embedding_device: str = "cpu"
    top_k: int = 10
    dense_weight: float = 0.7
    sparse_weight: float = 0.3


settings = RAGCoreSettings()
