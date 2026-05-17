"""
Factory for creating embedding generators based on configuration.

Supports multiple embedding providers:
- Gemini (Google)
- OpenAI
- Local (sentence-transformers)
- Mock (for testing)
"""

from typing import Any

from src.config.logging_config import get_logger
from src.config.settings import get_settings

logger = get_logger(__name__)


class EmbeddingFactory:
    """
    Factory for creating embedding generator instances.

    Allows easy switching between providers via configuration.
    """

    @staticmethod
    def create_embedding_generator(provider: str = None) -> Any:
        """
        Create embedding generator based on provider name.

        Args:
            provider: Provider name (gemini, openai, local, mock)
                     If None, uses EMBEDDING_PROVIDER from settings

        Returns:
            Embedding generator instance

        Raises:
            ValueError: If provider is unknown
        """
        settings = get_settings()

        # Get provider from parameter or settings
        if provider is None:
            provider = getattr(settings, 'embedding_provider', 'mock').lower()
        else:
            provider = provider.lower()

        logger.info("creating_embedding_generator", provider=provider)

        if provider == "gemini":
            from src.infrastructure.vector_store.embeddings import EmbeddingGenerator
            return EmbeddingGenerator()

        elif provider == "openai":
            from src.infrastructure.vector_store.openai_embeddings import OpenAIEmbeddingGenerator
            return OpenAIEmbeddingGenerator()

        elif provider == "local":
            from src.infrastructure.vector_store.local_embeddings import LocalEmbeddingGenerator
            return LocalEmbeddingGenerator()

        elif provider == "mock":
            from src.infrastructure.vector_store.mock_embeddings import MockEmbeddingGenerator
            return MockEmbeddingGenerator()

        else:
            raise ValueError(
                f"Unknown embedding provider: {provider}. "
                f"Supported: gemini, openai, local, mock"
            )


def get_embedding_generator(provider: str = None) -> Any:
    """
    Convenience function to get embedding generator.

    Args:
        provider: Provider name (gemini, openai, local, mock)

    Returns:
        Embedding generator instance
    """
    return EmbeddingFactory.create_embedding_generator(provider)
