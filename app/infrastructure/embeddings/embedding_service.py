"""
Generates vector embeddings by calling the EmbeddingGemma Server API.
Server docs: POST /embed, GET /health at EMBEDDING_SERVER_URL.
"""

import os
import numpy as np
import asyncio
import httpx
from typing import List, Optional
from threading import Lock

import logging

logger = logging.getLogger(__name__)

EMBEDDING_SERVER_URL = os.getenv("EMBEDDING_SERVER_URL", "http://localhost:8000")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "768"))


class EmbeddingService:

    _instance: Optional["EmbeddingService"] = None
    _lock: Lock = Lock()

    def __init__(
        self,
        server_url: str = EMBEDDING_SERVER_URL,
        dimension: int = EMBEDDING_DIMENSION,
    ):
        logger.info(
            f"Initializing EmbeddingService (EmbeddingGemma API at {server_url}, dim={dimension})"
        )
        self.server_url = server_url.rstrip("/")
        self.embedding_dim = dimension

        # Synchronous health check on init
        try:
            resp = httpx.get(f"{self.server_url}/health", timeout=15.0)
            resp.raise_for_status()
            health = resp.json()
            if health.get("model_loaded"):
                logger.info(
                    f"EmbeddingGemma server is healthy — model: {health.get('model_name')}"
                )
            else:
                logger.warning("EmbeddingGemma server reports model not loaded yet.")
        except Exception as e:
            logger.error(f"EmbeddingGemma health check failed: {e}")
            raise RuntimeError(
                f"Cannot reach EmbeddingGemma server at {self.server_url}: {e}"
            )

    @classmethod
    def get_instance(cls) -> "EmbeddingService":
        """Thread-safe singleton accessor."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------ #
    #  Synchronous batch embedding (used by ContextRetriever)
    # ------------------------------------------------------------------ #
    def generate_embeddings_batch(
        self,
        texts: List[str],
        embedding_type: str = "document",
    ) -> np.ndarray:
        """
        Generate embeddings for a batch of texts synchronously.
        Calls the EmbeddingGemma /embed endpoint.
        """
        if not texts:
            return np.array([])

        valid_texts = [
            (t.strip() if t else "") for t in texts if t is not None
        ]

        try:
            payload = {
                "text": valid_texts,
                "normalize": True,
                "dimension": self.embedding_dim,
                "embedding_type": embedding_type,
            }
            resp = httpx.post(
                f"{self.server_url}/embed",
                json=payload,
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return np.array(data["embeddings"], dtype=np.float32)
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise RuntimeError(f"Embedding generation failed: {e}")

    # ------------------------------------------------------------------ #
    #  Async single-text embedding (used by DocumentIndexer)
    # ------------------------------------------------------------------ #
    async def generate_embedding_async(
        self,
        text: str,
        embedding_type: str = "document",
    ) -> np.ndarray:
        """
        Generate embedding for a single text string asynchronously.
        Uses httpx.AsyncClient to avoid blocking the event loop.
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding generation.")
            return np.array([])

        try:
            payload = {
                "text": text,
                "normalize": True,
                "dimension": self.embedding_dim,
                "embedding_type": embedding_type,
            }
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{self.server_url}/embed",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

            embeddings = data["embeddings"]
            if not embeddings or len(embeddings) == 0:
                return np.array([])

            return np.array(embeddings[0], dtype=np.float32)

        except Exception as e:
            logger.error(f"Async embedding generation failed: {e}")
            raise RuntimeError(f"Async embedding generation failed: {e}")

    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embeddings (default 768 for EmbeddingGemma)."""
        return self.embedding_dim


def get_embedding_service() -> EmbeddingService:
    """Dependency injection helper."""
    return EmbeddingService.get_instance()
