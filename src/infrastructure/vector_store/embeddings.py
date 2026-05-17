"""
Embedding generation using Gemini API.
"""

import time
from typing import List

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.logging_config import get_logger
from src.config.settings import get_settings
from src.utils.exceptions import VectorStoreError

logger = get_logger(__name__)


class EmbeddingGenerator:
    """
    Generates embeddings using Gemini Embedding API.

    Supports batch processing and automatic retries.
    """

    def __init__(self):
        """Initialize embedding generator with Gemini API."""
        settings = get_settings()

        # Configure Gemini API with REST transport to avoid gRPC SSL issues
        genai.configure(
            api_key=settings.gemini_api_key,
            transport="rest"  # Use REST instead of gRPC to bypass SSL certificate issues
        )

        self.model_name = settings.embedding_model
        self.batch_size = 5  # Very small batches to respect rate limits
        self.delay_between_batches = 5  # Seconds to wait between batches

        logger.info("embedding_generator_initialized", model=self.model_name)

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
            List[float]: Embedding vector

        Raises:
            VectorStoreError: If embedding generation fails
        """
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document",
            )

            return result["embedding"]

        except Exception as e:
            logger.error("embedding_generation_failed", error=str(e))
            raise VectorStoreError(f"Failed to generate embedding: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of texts to embed

        Returns:
            List[List[float]]: List of embedding vectors

        Raises:
            VectorStoreError: If batch embedding generation fails
        """
        if not texts:
            return []

        logger.info("generating_embeddings_batch", count=len(texts))

        try:
            embeddings = []

            # Process in small batches with delays to respect rate limits
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i : i + self.batch_size]

                for text in batch:
                    result = genai.embed_content(
                        model=self.model_name,
                        content=text,
                        task_type="retrieval_document",
                    )
                    embeddings.append(result["embedding"])

                    # Delay between individual requests to respect free tier limits
                    time.sleep(0.5)

                logger.debug(
                    "batch_processed",
                    batch_start=i,
                    batch_size=len(batch),
                    total=len(texts),
                )

                # Longer delay between batches to avoid rate limits
                if i + self.batch_size < len(texts):
                    time.sleep(self.delay_between_batches)

            logger.info("embeddings_generated", total_count=len(embeddings))

            return embeddings

        except Exception as e:
            logger.error("batch_embedding_failed", error=str(e))
            raise VectorStoreError(f"Failed to generate batch embeddings: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a query (optimized for retrieval).

        Args:
            query: Query text

        Returns:
            List[float]: Query embedding vector

        Raises:
            VectorStoreError: If embedding generation fails
        """
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=query,
                task_type="retrieval_query",  # Optimized for queries
            )

            return result["embedding"]

        except Exception as e:
            logger.error("query_embedding_failed", error=str(e), query=query[:100])
            raise VectorStoreError(f"Failed to generate query embedding: {e}")
