"""
Citation service.

Generates accurate source citations for responses.
"""

from typing import List

from src.config.logging_config import get_logger
from src.domain.models.document import DocumentChunk
from src.domain.models.response import Citation

logger = get_logger(__name__)


class CitationService:
    """
    Service for generating source citations.

    Creates accurate, traceable citations for all claims.
    """

    def __init__(self):
        """Initialize citation service."""
        logger.info("citation_service_initialized")

    def generate_citations(
        self,
        response_text: str,
        source_chunks: List[DocumentChunk],
    ) -> List[Citation]:
        """
        Generate citations for a response.

        Args:
            response_text: Generated response text
            source_chunks: Source chunks used

        Returns:
            List[Citation]: Generated citations
        """
        logger.info("generating_citations", source_count=len(source_chunks))

        citations = []

        for i, chunk in enumerate(source_chunks, 1):
            # Check if this source is referenced in response
            citation_marker = f"[{i}]"

            if citation_marker in response_text:
                # Create citation
                citation = Citation(
                    source_document=chunk.metadata.document_name,
                    chunk_id=chunk.chunk_id,
                    excerpt=self._create_excerpt(chunk.text),
                    page_number=chunk.metadata.page_number,
                    section=chunk.metadata.section,
                    relevance_score=1.0,  # Could be enhanced with relevance scoring
                )

                citations.append(citation)

        if not citations and source_chunks:
            # If no citations found but we have sources, add all sources
            logger.warning("no_citation_markers_found_adding_all_sources")

            for chunk in source_chunks:
                citation = Citation(
                    source_document=chunk.metadata.document_name,
                    chunk_id=chunk.chunk_id,
                    excerpt=self._create_excerpt(chunk.text),
                    page_number=chunk.metadata.page_number,
                    section=chunk.metadata.section,
                    relevance_score=1.0,
                )
                citations.append(citation)

        logger.info("citations_generated", count=len(citations))

        return citations

    def _create_excerpt(self, text: str, max_length: int = 150) -> str:
        """
        Create a short excerpt from text.

        Args:
            text: Full text
            max_length: Maximum excerpt length

        Returns:
            str: Excerpt
        """
        if len(text) <= max_length:
            return text

        # Try to break at sentence boundary
        excerpt = text[:max_length]

        # Find last period, question mark, or exclamation
        last_sentence_end = max(
            excerpt.rfind("."),
            excerpt.rfind("?"),
            excerpt.rfind("!"),
        )

        if last_sentence_end > max_length * 0.5:  # At least 50% of desired length
            excerpt = excerpt[: last_sentence_end + 1]
        else:
            excerpt = excerpt + "..."

        return excerpt.strip()

    def format_citations_for_display(self, citations: List[Citation]) -> str:
        """
        Format citations for user display.

        Args:
            citations: List of citations

        Returns:
            str: Formatted citations
        """
        if not citations:
            return ""

        lines = ["", "**Sources:**"]

        for i, citation in enumerate(citations, 1):
            formatted = citation.format(i)
            lines.append(formatted)

        return "\n".join(lines)

    def validate_citations(
        self,
        response_text: str,
        citations: List[Citation],
    ) -> bool:
        """
        Validate that citations are properly referenced.

        Args:
            response_text: Response text
            citations: Citations to validate

        Returns:
            bool: True if valid
        """
        # Check that each citation is referenced in text
        for i, citation in enumerate(citations, 1):
            marker = f"[{i}]"
            if marker not in response_text:
                logger.warning(
                    "citation_not_referenced",
                    index=i,
                    document=citation.source_document,
                )
                return False

        return True
