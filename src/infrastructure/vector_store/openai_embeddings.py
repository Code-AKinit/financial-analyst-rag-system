"""
OpenAI embedding generator.

Uses OpenAI's text-embedding-3-small model for high-quality embeddings.
"""

import time
from typing import List

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.logging_config import get_logger
from src.config.settings import get_settings
from src.utils.exceptions import VectorStoreError

logger = get_logger(__name__)


class OpenAIEmbeddingGenerator:
    """
    OpenAI implementation of embedding generator.

    Uses text-embedding-3-small model (1536 dimensions).
    High quality, fast, and generous rate limits.
    """

    def __init__(self):
        """
        Initialize OpenAI embedding generator.

        Requires OPENAI_API_KEY in environment.
        """
        settings = get_settings()

        # Get API key from settings
        api_key = getattr(settings, 'openai_api_key', None)
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        self.client = OpenAI(api_key=api_key)
        self.model_name = "text-embedding-3-small"  # 1536 dimensions
        self.dimension = 1536
        self.batch_size = 100  # OpenAI allows large batches

        logger.info(
            "openai_embedding_generator_initialized",
            model=self.model_name,
            dimension=self.dimension
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List[float]: Embedding vector (1536 dimensions)

        Raises:
            VectorStoreError: If embedding generation fails
        """
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.model_name,
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error("openai_embedding_failed", error=str(e))
            raise VectorStoreError(f"Failed to generate OpenAI embedding: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.

        OpenAI allows up to 2048 texts per request, but we batch
        conservatively to avoid timeouts.

        Args:
            texts: List of texts to embed

        Returns:
            List[List[float]]: List of embedding vectors

        Raises:
            VectorStoreError: If batch embedding generation fails
        """
        if not texts:
            return []

        logger.info("generating_openai_embeddings_batch", count=len(texts))

        try:
            all_embeddings = []

            # Process in batches
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i : i + self.batch_size]

                logger.debug(
                    "processing_batch",
                    batch_start=i,
                    batch_size=len(batch),
                    total=len(texts)
                )

                response = self.client.embeddings.create(
                    input=batch,
                    model=self.model_name,
                )

                # Extract embeddings in order
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                # Small delay between batches to be respectful
                if i + self.batch_size < len(texts):
                    time.sleep(0.5)

            logger.info("openai_embeddings_generated", total_count=len(all_embeddings))

            return all_embeddings

        except Exception as e:
            logger.error("openai_batch_embedding_failed", error=str(e))
            raise VectorStoreError(f"Failed to generate OpenAI embeddings batch: {e}")

    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a query.

        Args:
            query: Query text

        Returns:
            List[float]: Query embedding vector
        """
        return self.generate_embedding(query)
