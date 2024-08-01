import os
from mem0.vector_stores.configs import VectorStoreConfig
from mem0.llms.configs import LlmConfig
from mem0.embeddings.configs import EmbedderConfig


vector_config = VectorStoreConfig(
    provider="qdrant",
    config={
        "host": "127.0.0.1",
        "port": 6333,
    }
).dict()

llm_config = LlmConfig(
    provider="openai",
    config={
        "model": os.getenv("OPENAI_MODEL", "gpt-4o")
    }
).dict()

embedding_config = EmbedderConfig(
    provider="openai",
    config={
        "model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    }
).dict()
