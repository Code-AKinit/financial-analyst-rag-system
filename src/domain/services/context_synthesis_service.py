"""
Context synthesis service.

Synthesizes retrieved chunks into coherent context for LLM.
"""

from typing import List

from src.config.logging_config import get_logger
from src.domain.models.document import DocumentChunk
from src.domain.models.query import Query
from src.infrastructure.llm.prompt_templates import PromptTemplates

logger = get_logger(__name__)


class ContextSynthesisService:
    """
    Service for synthesizing context from multiple document chunks.

    Deduplicates, ranks, and organizes retrieved chunks.
    """

    def __init__(self):
        """Initialize context synthesis service."""
        self.templates = PromptTemplates()
        logger.info("context_synthesis_service_initialized")

    def synthesize_context(
        self,
        query: Query,
        chunks: List[DocumentChunk],
        max_context_length: int = 8000,
    ) -> str:
        """
        Synthesize chunks into coherent context.

        Args:
            query: User query
            chunks: Retrieved chunks
            max_context_length: Maximum context length

        Returns:
            str: Synthesized context
        """
        logger.info("synthesizing_context", chunk_count=len(chunks))

        if not chunks:
            logger.warning("no_chunks_to_synthesize")
            return "No relevant information found in the documents."

        # Deduplicate chunks
        unique_chunks = self._deduplicate_chunks(chunks)

        # Rank by relevance
        ranked_chunks = self._rank_chunks(query, unique_chunks)

        # Build context within length limit
        context = self._build_context(ranked_chunks, max_context_length)

        logger.info(
            "context_synthesized",
            original_chunks=len(chunks),
            unique_chunks=len(unique_chunks),
            final_chunks=len(ranked_chunks),
            context_length=len(context),
        )

        return context

    def _deduplicate_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """
        Remove duplicate or highly similar chunks.

        Args:
            chunks: List of chunks

        Returns:
            List[DocumentChunk]: Deduplicated chunks
        """
        if not chunks:
            return []

        unique_chunks = []
        seen_content = set()

        for chunk in chunks:
            # Create a normalized version for comparison
            normalized = self._normalize_text(chunk.text)

            # Check if we've seen this content
            if normalized not in seen_content:
                unique_chunks.append(chunk)
                seen_content.add(normalized)

        logger.debug(
            "chunks_deduplicated",
            original=len(chunks),
            unique=len(unique_chunks),
        )

        return unique_chunks

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison.

        Args:
            text: Text to normalize

        Returns:
            str: Normalized text
        """
        # Remove extra whitespace
        normalized = " ".join(text.split())
        # Convert to lowercase
        normalized = normalized.lower()
        # Take first 500 chars for comparison (to handle minor variations)
        normalized = normalized[:500]

        return normalized

    def _rank_chunks(
        self,
        query: Query,
        chunks: List[DocumentChunk],
    ) -> List[DocumentChunk]:
        """
        Rank chunks by relevance to query.

        Args:
            query: User query
            chunks: Chunks to rank

        Returns:
            List[DocumentChunk]: Ranked chunks
        """
        # Simple keyword-based ranking (vector similarity already done)
        query_terms = set(query.text.lower().split())

        scored_chunks = []
        for chunk in chunks:
            chunk_terms = set(chunk.text.lower().split())

            # Calculate overlap score
            overlap = len(query_terms & chunk_terms)
            score = overlap / len(query_terms) if query_terms else 0

            # Boost score for chunks with metadata matching query
            if query.metadata.fiscal_periods:
                if chunk.metadata.fiscal_period in query.metadata.fiscal_periods:
                    score += 0.3

            if chunk.metadata.has_numerical_data:
                score += 0.1

            scored_chunks.append((chunk, score))

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        ranked = [chunk for chunk, _ in scored_chunks]

        logger.debug("chunks_ranked", count=len(ranked))

        return ranked

    def _build_context(
        self,
        chunks: List[DocumentChunk],
        max_length: int,
    ) -> str:
        """
        Build context string from chunks within length limit.

        Args:
            chunks: Ranked chunks
            max_length: Maximum total length

        Returns:
            str: Formatted context
        """
        context_parts = []
        current_length = 0

        for i, chunk in enumerate(chunks, 1):
            # Format chunk with source
            chunk_text = self._format_chunk_with_source(chunk, i)
            chunk_length = len(chunk_text)

            # Check if adding this chunk exceeds limit
            if current_length + chunk_length > max_length:
                logger.debug(
                    "context_length_limit_reached",
                    chunks_included=i - 1,
                    total_chunks=len(chunks),
                )
                break

            context_parts.append(chunk_text)
            current_length += chunk_length

        return "\n\n---\n\n".join(context_parts)

    def _format_chunk_with_source(self, chunk: DocumentChunk, index: int) -> str:
        """
        Format chunk with source attribution.

        Args:
            chunk: Document chunk
            index: Source index

        Returns:
            str: Formatted chunk
        """
        metadata = chunk.metadata

        # Build source header
        source_parts = [f"[{index}] Source: {metadata.document_name}"]

        if metadata.section:
            source_parts.append(f"Section: {metadata.section}")

        if metadata.page_number:
            source_parts.append(f"Page: {metadata.page_number}")

        if metadata.fiscal_period:
            source_parts.append(f"Period: {metadata.fiscal_period.value}")

        source_header = ", ".join(source_parts)

        return f"{source_header}\n\n{chunk.text}"

    def get_chunk_summaries(self, chunks: List[DocumentChunk]) -> List[str]:
        """
        Get brief summaries of chunks for display.

        Args:
            chunks: Chunks to summarize

        Returns:
            List[str]: Chunk summaries
        """
        summaries = []

        for chunk in chunks:
            # First 150 characters
            text_preview = chunk.text[:150].strip()
            if len(chunk.text) > 150:
                text_preview += "..."

            summary = f"{chunk.metadata.document_name}: {text_preview}"
            summaries.append(summary)

        return summaries
