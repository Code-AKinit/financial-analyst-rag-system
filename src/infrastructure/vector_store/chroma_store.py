"""
ChromaDB vector store implementation.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.config.logging_config import get_logger
from src.config.settings import get_settings
from src.domain.interfaces.vector_store import VectorStore
from src.domain.models.document import DocumentChunk, ChunkMetadata
from src.infrastructure.vector_store.embedding_factory import get_embedding_generator
from src.utils.constants import DEFAULT_COLLECTION_NAME
from src.utils.exceptions import VectorStoreError

logger = get_logger(__name__)


class ChromaVectorStore(VectorStore):
    """
    ChromaDB implementation of vector store.

    Provides persistent vector storage with metadata filtering.
    """

    def __init__(
        self,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        persist_directory: Optional[str] = None,
    ):
        """
        Initialize ChromaDB vector store.

        Args:
            collection_name: Name of the collection
            persist_directory: Directory for persistence
        """
        settings = get_settings()

        self.collection_name = collection_name
        self.persist_directory = persist_directory or settings.chroma_persist_directory

        # Ensure persistence directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Financial documents vector store"},
        )

        # Initialize embedding generator using factory
        # This allows easy switching between Gemini, OpenAI, Local, or Mock
        self.embedding_generator = get_embedding_generator()

        logger.info(
            "chroma_store_initialized",
            collection=self.collection_name,
            persist_dir=self.persist_directory,
            embedding_provider=settings.embedding_provider,
        )

    def add_documents(
        self,
        chunks: List[DocumentChunk],
        embeddings: Optional[List[List[float]]] = None,
    ) -> None:
        """
        Add document chunks with embeddings to the store.

        Args:
            chunks: Document chunks to add
            embeddings: Pre-computed embeddings (optional)

        Raises:
            VectorStoreError: If addition fails
        """
        if not chunks:
            logger.warning("no_chunks_to_add")
            return

        logger.info("adding_documents_to_chroma", chunk_count=len(chunks))

        try:
            # Generate embeddings if not provided
            if embeddings is None:
                texts = [chunk.text for chunk in chunks]
                embeddings = self.embedding_generator.generate_embeddings_batch(texts)

            # Prepare data for ChromaDB
            ids = [chunk.chunk_id for chunk in chunks]
            documents = [chunk.text for chunk in chunks]
            metadatas = []

            # Clean metadata: ChromaDB only accepts str, int, float, bool
            for chunk in chunks:
                meta = chunk.metadata.to_dict()
                clean_meta = {}
                for k, v in meta.items():
                    # Skip None values
                    if v is None:
                        continue
                    # Skip empty lists
                    if isinstance(v, list) and len(v) == 0:
                        continue
                    # Convert lists to comma-separated strings
                    if isinstance(v, list):
                        clean_meta[k] = ", ".join(str(x) for x in v)
                    # Keep primitive types
                    elif isinstance(v, (str, int, float, bool)):
                        clean_meta[k] = v
                    # Convert everything else to string
                    else:
                        clean_meta[k] = str(v)
                metadatas.append(clean_meta)

            # Add to collection
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )

            logger.info(
                "documents_added_to_chroma",
                chunk_count=len(chunks),
                collection=self.collection_name,
            )

        except Exception as e:
            logger.error("chroma_add_failed", error=str(e))
            raise VectorStoreError(f"Failed to add documents to ChromaDB: {e}")

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
        logger.debug("searching_chroma", top_k=top_k, has_filters=filters is not None)

        try:
            # Build where clause from filters
            where_clause = self._build_where_clause(filters) if filters else None

            # Query collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause,
            )

            # Convert results to DocumentChunk objects
            chunks = self._results_to_chunks(results)

            logger.debug("search_completed", results_count=len(chunks))

            return chunks

        except Exception as e:
            logger.error("chroma_search_failed", error=str(e))
            raise VectorStoreError(f"Failed to search ChromaDB: {e}")

    def hybrid_search(
        self,
        query_text: str,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """
        Perform hybrid search (vector + keyword).

        ChromaDB doesn't have native hybrid search, so we use vector search
        with post-filtering based on keyword matches.

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
        logger.debug("hybrid_search_chroma", query=query_text[:50], top_k=top_k)

        try:
            # Get more results than needed for reranking
            vector_results = self.search(
                query_embedding=query_embedding,
                top_k=top_k * 2,  # Get 2x results for keyword filtering
                filters=filters,
            )

            # Simple keyword boosting (more sophisticated reranking happens elsewhere)
            query_terms = set(query_text.lower().split())

            scored_results = []
            for chunk in vector_results:
                # Count keyword matches
                chunk_terms = set(chunk.text.lower().split())
                keyword_score = len(query_terms & chunk_terms) / len(query_terms) if query_terms else 0

                # Simple hybrid score (could be more sophisticated)
                hybrid_score = 0.7 + (0.3 * keyword_score)  # 70% vector, 30% keyword

                scored_results.append((chunk, hybrid_score))

            # Sort by hybrid score and return top_k
            scored_results.sort(key=lambda x: x[1], reverse=True)
            top_chunks = [chunk for chunk, _ in scored_results[:top_k]]

            logger.debug("hybrid_search_completed", results_count=len(top_chunks))

            return top_chunks

        except Exception as e:
            logger.error("hybrid_search_failed", error=str(e))
            raise VectorStoreError(f"Failed to perform hybrid search: {e}")

    def delete_collection(self) -> None:
        """
        Delete the entire collection.

        Raises:
            VectorStoreError: If deletion fails
        """
        logger.warning("deleting_collection", collection=self.collection_name)

        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info("collection_deleted", collection=self.collection_name)

        except Exception as e:
            logger.error("collection_deletion_failed", error=str(e))
            raise VectorStoreError(f"Failed to delete collection: {e}")

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.

        Returns:
            Dict: Collection statistics

        Raises:
            VectorStoreError: If retrieval fails
        """
        try:
            count = self.collection.count()

            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory,
            }

        except Exception as e:
            logger.error("stats_retrieval_failed", error=str(e))
            raise VectorStoreError(f"Failed to get collection stats: {e}")

    def collection_exists(self) -> bool:
        """
        Check if collection exists.

        Returns:
            bool: True if collection exists
        """
        try:
            collections = self.client.list_collections()
            return any(c.name == self.collection_name for c in collections)

        except Exception:
            return False

    def _build_where_clause(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build ChromaDB where clause from filters.

        Args:
            filters: Filter dictionary

        Returns:
            Dict: ChromaDB where clause
        """
        where_conditions = {}

        for key, value in filters.items():
            if isinstance(value, list):
                # Handle list of values (OR condition)
                where_conditions[key] = {"$in": value}
            else:
                # Simple equality
                where_conditions[key] = value

        return where_conditions

    def _results_to_chunks(self, results: Dict[str, Any]) -> List[DocumentChunk]:
        """
        Convert ChromaDB results to DocumentChunk objects.

        Args:
            results: ChromaDB query results

        Returns:
            List[DocumentChunk]: Reconstructed chunks
        """
        chunks = []

        if not results["ids"] or not results["ids"][0]:
            return chunks

        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0] if "distances" in results else [None] * len(ids)

        for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
            # Reconstruct ChunkMetadata
            # Convert string values back to enums
            from src.utils.constants import DocumentType, FiscalPeriod

            document_type = metadata["document_type"]
            if isinstance(document_type, str):
                document_type = DocumentType(document_type)

            fiscal_period = metadata.get("fiscal_period")
            if fiscal_period and isinstance(fiscal_period, str):
                try:
                    fiscal_period = FiscalPeriod(fiscal_period)
                except ValueError:
                    fiscal_period = None

            # Convert topics from comma-separated string to list
            topics = metadata.get("topics", [])
            if isinstance(topics, str):
                topics = [t.strip() for t in topics.split(",") if t.strip()]

            chunk_metadata = ChunkMetadata(
                document_name=metadata["document_name"],
                document_type=document_type,
                chunk_index=metadata["chunk_index"],
                total_chunks=metadata["total_chunks"],
                chunk_id=chunk_id,
                page_number=metadata.get("page_number"),
                section=metadata.get("section"),
                fiscal_period=fiscal_period,
                has_table=metadata.get("has_table", False),
                has_numerical_data=metadata.get("has_numerical_data", False),
                topics=topics,
                date_range=metadata.get("date_range"),
            )

            chunk = DocumentChunk(text=text, metadata=chunk_metadata)
            chunks.append(chunk)

        return chunks
