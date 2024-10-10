import os

from mem0.embeddings.configs import EmbedderConfig
from mem0.llms.configs import LlmConfig
from mem0.vector_stores.configs import VectorStoreConfig

vector_config = VectorStoreConfig(
    provider="qdrant",
    config={
        "host": os.getenv("QDRANT_HOST", "127.0.0.1"),
        "port": os.getenv("QDRANT_PORT", "6333")
    }
).dict()

llm_config = LlmConfig(
    provider="openai",
    config={
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    }
).dict()

embedding_config = EmbedderConfig(
    provider="openai",
    config={
        "model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    }
).dict()
