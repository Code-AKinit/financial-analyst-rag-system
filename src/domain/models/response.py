"""
Domain models for responses.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.domain.models.document import DocumentChunk
from src.utils.constants import OutputFormat


@dataclass
class Citation:
    """
    Source citation for a claim in the response.

    Attributes:
        source_document: Name of source document
        chunk_id: ID of the chunk
        page_number: Page number if applicable
        section: Section name if available
        excerpt: Short excerpt from source
        relevance_score: Relevance score (0-1)
    """

    source_document: str
    chunk_id: str
    excerpt: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    relevance_score: float = 1.0

    def format(self, index: int) -> str:
        """
        Format citation for display.

        Args:
            index: Citation number

        Returns:
            str: Formatted citation
        """
        parts = [f"[{index}] {self.source_document}"]

        if self.section:
            parts.append(f"Section: {self.section}")

        if self.page_number:
            parts.append(f"Page: {self.page_number}")

        return ", ".join(parts)


@dataclass
class ResponseMetadata:
    """
    Metadata about the response generation.

    Attributes:
        retrieved_chunks_count: Number of chunks retrieved
        processing_time_ms: Time taken to generate response
        model_used: LLM model used
        temperature: Temperature setting used
        reranked: Whether reranking was applied
    """

    retrieved_chunks_count: int = 0
    processing_time_ms: float = 0.0
    model_used: str = "unknown"
    temperature: float = 0.1
    reranked: bool = False


@dataclass
class Response:
    """
    Response to a user query.

    Attributes:
        content: Response text/content
        citations: Source citations
        retrieved_chunks: Chunks used for generation
        output_format: Format of response
        confidence: Confidence score (0-1)
        query_id: ID of query this responds to
        response_id: Unique identifier for response
        timestamp: When response was generated
        metadata: Response metadata
        structured_data: Structured data for Excel/PDF
        file_path: Path to generated file if applicable
    """

    content: str
    citations: List[Citation]
    query_id: str
    response_id: str = field(default_factory=lambda: datetime.now().isoformat())
    timestamp: datetime = field(default_factory=datetime.now)
    output_format: OutputFormat = OutputFormat.MARKDOWN
    confidence: float = 1.0
    retrieved_chunks: List[DocumentChunk] = field(default_factory=list)
    metadata: ResponseMetadata = field(default_factory=ResponseMetadata)
    structured_data: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None

    def __post_init__(self):
        """Validate response after initialization."""
        if not self.content or not self.content.strip():
            raise ValueError("Response content cannot be empty")

        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")

    def format_citations(self) -> str:
        """
        Format all citations as a bibliography.

        Returns:
            str: Formatted bibliography
        """
        if not self.citations:
            return ""

        lines = ["", "**Sources:**"]
        for i, citation in enumerate(self.citations, 1):
            lines.append(citation.format(i))

        return "\n".join(lines)

    def get_full_response(self) -> str:
        """
        Get complete response with citations.

        Returns:
            str: Response content with citations appended
        """
        return self.content + self.format_citations()
