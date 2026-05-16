"""
Domain models for documents and chunks.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.utils.constants import DocumentType, FiscalPeriod


@dataclass
class DocumentMetadata:
    """
    Metadata associated with a document.

    Attributes:
        document_name: Original file name
        document_type: Type of document
        fiscal_period: Fiscal period if applicable
        file_path: Path to source file
        file_size_bytes: Size of file in bytes
        processed_at: When document was processed
        total_pages: Number of pages (for PDFs)
        additional_metadata: Any other metadata
    """

    document_name: str
    document_type: DocumentType
    file_path: str
    file_size_bytes: int
    processed_at: datetime = field(default_factory=datetime.now)
    fiscal_period: Optional[FiscalPeriod] = None
    total_pages: Optional[int] = None
    additional_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChunkMetadata:
    """
    Metadata for a document chunk.

    Attributes:
        document_name: Source document name
        document_type: Type of source document
        chunk_index: Index of this chunk
        total_chunks: Total chunks in document
        chunk_id: Unique identifier for chunk
        page_number: Page number (for PDFs)
        section: Section name if extracted
        fiscal_period: Fiscal period if applicable
        has_table: Whether chunk contains table data
        has_numerical_data: Whether chunk has numbers
        topics: Extracted topics/keywords
        date_range: Date range if applicable
    """

    document_name: str
    document_type: DocumentType
    chunk_index: int
    total_chunks: int
    chunk_id: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    fiscal_period: Optional[FiscalPeriod] = None
    has_table: bool = False
    has_numerical_data: bool = False
    topics: List[str] = field(default_factory=list)
    date_range: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for vector store."""
        return {
            "document_name": self.document_name,
            "document_type": self.document_type.value,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "chunk_id": self.chunk_id,
            "page_number": self.page_number,
            "section": self.section,
            "fiscal_period": self.fiscal_period.value if self.fiscal_period else None,
            "has_table": self.has_table,
            "has_numerical_data": self.has_numerical_data,
            "topics": self.topics,
            "date_range": self.date_range,
        }


@dataclass
class DocumentChunk:
    """
    A chunk of a document with metadata.

    Attributes:
        text: The chunk text content
        metadata: Chunk metadata
        embedding: Vector embedding (optional)
    """

    text: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = None

    def __post_init__(self):
        """Validate chunk after initialization."""
        if not self.text or not self.text.strip():
            raise ValueError("Chunk text cannot be empty")

    @property
    def chunk_id(self) -> str:
        """Get chunk unique identifier."""
        return self.metadata.chunk_id

    @property
    def document_name(self) -> str:
        """Get source document name."""
        return self.metadata.document_name


@dataclass
class Document:
    """
    Represents a complete financial document.

    Attributes:
        content: Full text content
        metadata: Document metadata
        chunks: List of document chunks
    """

    content: str
    metadata: DocumentMetadata
    chunks: List[DocumentChunk] = field(default_factory=list)

    def __post_init__(self):
        """Validate document after initialization."""
        if not self.content or not self.content.strip():
            raise ValueError("Document content cannot be empty")

    @property
    def document_name(self) -> str:
        """Get document name."""
        return self.metadata.document_name

    @property
    def document_type(self) -> DocumentType:
        """Get document type."""
        return self.metadata.document_type

    def add_chunk(self, chunk: DocumentChunk) -> None:
        """
        Add a chunk to this document.

        Args:
            chunk: Document chunk to add
        """
        self.chunks.append(chunk)
