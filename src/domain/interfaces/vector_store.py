"""
Interface for Vector Store (Port).

Defines the contract for vector database operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.domain.models.document import DocumentChunk


class VectorStore(ABC):
    """
    Abstract interface for vector store operations.

    This port defines how the domain layer interacts with vector databases,
    independent of the specific implementation (ChromaDB, FAISS, etc.).
    """

    @abstractmethod
    def add_documents(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
    ) -> None:
        """
        Add document chunks with embeddings to the store.

        Args:
            chunks: Document chunks to add
            embeddings: Corresponding embeddings

        Raises:
            VectorStoreError: If addition fails
        """
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """
        Search for similar chunks using vector similarity.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filters: Metadata filters to apply

        Returns:
            List[DocumentChunk]: Top matching chunks

        Raises:
            VectorStoreError: If search fails
        """
        pass

    @abstractmethod
    def hybrid_search(
        self,
        query_text: str,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """
        Perform hybrid search (vector + keyword).

        Args:
            query_text: Query text for keyword search
            query_embedding: Query embedding for vector search
            top_k: Number of results to return
            filters: Metadata filters to apply

        Returns:
            List[DocumentChunk]: Top matching chunks

        Raises:
            VectorStoreError: If search fails
        """
        pass

    @abstractmethod
    def delete_collection(self) -> None:
        """
        Delete the entire collection.

        Raises:
            VectorStoreError: If deletion fails
        """
        pass

    @abstractmethod
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.

        Returns:
            Dict: Collection statistics (document count, etc.)

        Raises:
            VectorStoreError: If retrieval fails
        """
        pass

    @abstractmethod
    def collection_exists(self) -> bool:
        """
        Check if collection exists.

        Returns:
            bool: True if collection exists
        """
        pass
