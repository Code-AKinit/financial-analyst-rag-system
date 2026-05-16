"""
Advanced retrieval strategies.

Implements hybrid search, reranking, and retrieval optimization.
"""

from typing import Any, Dict, List, Optional

from src.config.logging_config import get_logger
from src.config.settings import get_settings
from src.domain.interfaces.vector_store import VectorStore
from src.domain.models.document import DocumentChunk
from src.domain.models.query import Query
from src.infrastructure.vector_store.embeddings import EmbeddingGenerator

logger = get_logger(__name__)


class RetrievalStrategy:
    """
    Advanced retrieval strategy with hybrid search and reranking.
    """

    def __init__(self, vector_store: VectorStore):
        """
        Initialize retrieval strategy.

        Args:
            vector_store: Vector store instance
        """
        self.vector_store = vector_store
        self.embedding_generator = EmbeddingGenerator()
        self.settings = get_settings()

        logger.info("retrieval_strategy_initialized")

    def retrieve(
        self,
        query: Query,
        top_k: Optional[int] = None,
        use_hybrid: Optional[bool] = None,
        use_reranking: Optional[bool] = None,
    ) -> List[DocumentChunk]:
        """
        Retrieve relevant chunks for query.

        Args:
            query: User query
            top_k: Number of results (default from settings)
            use_hybrid: Use hybrid search (default from settings)
            use_reranking: Use reranking (default from settings)

        Returns:
            List[DocumentChunk]: Retrieved chunks
        """
        top_k = top_k if top_k is not None else self.settings.retrieval_top_k
        use_hybrid = use_hybrid if use_hybrid is not None else self.settings.hybrid_search_enabled
        use_reranking = (
            use_reranking if use_reranking is not None else self.settings.rerank_enabled
        )

        logger.info(
            "retrieving_chunks",
            query=query.text[:100],
            top_k=top_k,
            hybrid=use_hybrid,
            reranking=use_reranking,
        )

        # Generate query embedding
        query_embedding = self.embedding_generator.generate_query_embedding(query.effective_text)

        # Build metadata filters from query
        filters = self._build_filters(query)

        # Retrieve chunks
        if use_hybrid:
            # Get more candidates for reranking
            retrieve_k = top_k * 2 if use_reranking else top_k

            chunks = self.vector_store.hybrid_search(
                query_text=query.effective_text,
                query_embedding=query_embedding,
                top_k=retrieve_k,
                filters=filters,
            )
        else:
            # Pure vector search
            retrieve_k = top_k * 2 if use_reranking else top_k

            chunks = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=retrieve_k,
                filters=filters,
            )

        # Apply reranking if enabled
        if use_reranking and len(chunks) > top_k:
            chunks = self._rerank_chunks(query, chunks, top_k)

        logger.info("chunks_retrieved", count=len(chunks))

        return chunks

    def _build_filters(self, query: Query) -> Optional[Dict[str, Any]]:
        """
        Build metadata filters from query.

        Args:
            query: User query

        Returns:
            Dict | None: Metadata filters
        """
        filters = {}

        # Filter by fiscal period if mentioned
        if query.metadata.fiscal_periods:
            # Convert to values
            periods = [p.value for p in query.metadata.fiscal_periods]
            filters["fiscal_period"] = periods

        # Could add more filters based on query metadata
        # e.g., document type, has_table, etc.

        return filters if filters else None

    def _rerank_chunks(
        self,
        query: Query,
        chunks: List[DocumentChunk],
        top_k: int,
    ) -> List[DocumentChunk]:
        """
        Rerank chunks by relevance.

        Uses simple keyword-based reranking. Could be enhanced with
        cross-encoder models or LLM-based scoring.

        Args:
            query: User query
            chunks: Chunks to rerank
            top_k: Number to return

        Returns:
            List[DocumentChunk]: Reranked chunks
        """
        logger.debug("reranking_chunks", count=len(chunks))

        query_terms = set(query.effective_text.lower().split())

        scored_chunks = []

        for chunk in chunks:
            score = self._calculate_relevance_score(query, query_terms, chunk)
            scored_chunks.append((chunk, score))

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        # Return top k
        reranked = [chunk for chunk, _ in scored_chunks[:top_k]]

        logger.debug("chunks_reranked", returned=len(reranked))

        return reranked

    def _calculate_relevance_score(
        self,
        query: Query,
        query_terms: set,
        chunk: DocumentChunk,
    ) -> float:
        """
        Calculate relevance score for a chunk.

        Args:
            query: User query
            query_terms: Query terms set
            chunk: Document chunk

        Returns:
            float: Relevance score
        """
        score = 0.0

        chunk_terms = set(chunk.text.lower().split())

        # Keyword overlap (0-1)
        overlap = len(query_terms & chunk_terms)
        keyword_score = overlap / len(query_terms) if query_terms else 0
        score += keyword_score * 0.4  # 40% weight

        # Metadata boosting
        # Fiscal period match
        if query.metadata.fiscal_periods:
            if chunk.metadata.fiscal_period in query.metadata.fiscal_periods:
                score += 0.3  # 30% boost

        # Has numerical data (important for financial queries)
        if chunk.metadata.has_numerical_data:
            score += 0.1  # 10% boost

        # Has table (structured data)
        if chunk.metadata.has_table:
            score += 0.1  # 10% boost

        # Section relevance
        if chunk.metadata.section:
            section_lower = chunk.metadata.section.lower()
            # Check if section matches query keywords
            for keyword in query.metadata.keywords:
                if keyword in section_lower:
                    score += 0.1  # 10% boost per matching keyword
                    break

        return score

    def multi_query_retrieve(
        self,
        queries: List[str],
        top_k: int,
    ) -> List[DocumentChunk]:
        """
        Retrieve using multiple query variations.

        Args:
            queries: List of query variations
            top_k: Total results to return

        Returns:
            List[DocumentChunk]: Merged results
        """
        logger.info("multi_query_retrieval", query_count=len(queries))

        all_chunks = []
        seen_ids = set()

        # Retrieve for each query variation
        for query_text in queries:
            # Create temporary query object
            from src.domain.models.query import Query

            temp_query = Query(
                text=query_text,
                conversation_id="temp",
            )

            chunks = self.retrieve(temp_query, top_k=top_k // len(queries) + 1)

            # Add unique chunks
            for chunk in chunks:
                if chunk.chunk_id not in seen_ids:
                    all_chunks.append(chunk)
                    seen_ids.add(chunk.chunk_id)

        # Return top k
        return all_chunks[:top_k]
