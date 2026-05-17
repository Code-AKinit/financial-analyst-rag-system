"""
Mock embedding generator for testing without API calls.

Uses random embeddings so semantic search won't be perfect,
but allows testing all other system features.
"""

from typing import List
import numpy as np

from src.config.logging_config import get_logger

logger = get_logger(__name__)


class MockEmbeddingGenerator:
    """
    Generates mock/random embeddings for testing.

    Embeddings are deterministic (based on text hash) for reproducibility,
    but random, so semantic similarity won't work properly.
    """

    def __init__(self, dimension: int = 768):
        """
        Initialize mock embedding generator.

        Args:
            dimension: Embedding dimension (default: 768 like Gemini)
        """
        self.dimension = dimension
        logger.info("mock_embedding_generator_initialized", dimension=dimension)
        logger.warning("using_mock_embeddings", message="Semantic search will not be accurate")

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate a mock embedding vector.

        Uses hash of text as seed for reproducibility.

        Args:
            text: Text to embed

        Returns:
            List[float]: Random embedding vector (normalized)
        """
        # Use hash of text as seed for reproducibility
        seed = hash(text) % (2**32)
        np.random.seed(seed)

        # Generate random vector
        embedding = np.random.randn(self.dimension).astype(np.float32)

        # Normalize to unit length (like real embeddings)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding.tolist()

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of texts to embed

        Returns:
            List[List[float]]: List of embedding vectors
        """
        if not texts:
            return []

        logger.info("generating_mock_embeddings_batch", count=len(texts))

        embeddings = [self.generate_embedding(text) for text in texts]

        logger.info("mock_embeddings_generated", total_count=len(embeddings))

        return embeddings

    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a query.

        Args:
            query: Query text

        Returns:
            List[float]: Query embedding vector
        """
        return self.generate_embedding(query)
