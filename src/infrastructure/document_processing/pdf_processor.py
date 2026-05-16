"""
PDF document processor implementation.

Uses PyMuPDF (fitz) for fast and reliable PDF processing.
"""

from pathlib import Path
from typing import List

import fitz  # PyMuPDF

from src.config.logging_config import get_logger
from src.domain.interfaces.document_processor import DocumentProcessor
from src.domain.models.document import Document, DocumentChunk, ChunkMetadata, DocumentMetadata
from src.infrastructure.document_processing.chunking_strategies import semantic_chunk_text
from src.infrastructure.document_processing.metadata_extractor import (
    extract_document_type,
    extract_fiscal_period,
)
from src.utils.constants import DocumentType
from src.utils.exceptions import DocumentProcessingError
from src.utils.helpers import generate_chunk_id, has_numerical_data, detect_table_markers

logger = get_logger(__name__)


class PDFProcessor(DocumentProcessor):
    """
    Processes PDF documents (annual reports, quarterly earnings).

    Extracts text, preserves structure, and creates semantically meaningful chunks.
    """

    SUPPORTED_EXTENSIONS = [".pdf"]

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize PDF processor.

        Args:
            chunk_size: Target size for chunks in characters
            chunk_overlap: Overlap between chunks to preserve context
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def can_process(self, file_path: Path) -> bool:
        """
        Check if this processor can handle the file.

        Args:
            file_path: Path to file

        Returns:
            bool: True if file is a PDF
        """
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def process_document(self, file_path: Path) -> Document:
        """
        Process a PDF document and extract content.

        Args:
            file_path: Path to PDF file

        Returns:
            Document: Processed document with metadata

        Raises:
            DocumentProcessingError: If processing fails
        """
        logger.info("processing_pdf", file_path=str(file_path))

        try:
            # Validate file exists
            if not file_path.exists():
                raise DocumentProcessingError(f"File not found: {file_path}")

            # Open PDF
            doc = fitz.open(file_path)

            # Extract text from all pages
            full_text = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                full_text.append(text)

            content = "\n\n".join(full_text)

            if not content.strip():
                raise DocumentProcessingError(f"No text content extracted from {file_path}")

            # Extract metadata
            document_type = extract_document_type(file_path.name)
            fiscal_period = extract_fiscal_period(file_path.name, content)

            metadata = DocumentMetadata(
                document_name=file_path.name,
                document_type=document_type,
                file_path=str(file_path),
                file_size_bytes=file_path.stat().st_size,
                fiscal_period=fiscal_period,
                total_pages=len(doc),
            )

            doc.close()

            logger.info(
                "pdf_processed",
                file_path=str(file_path),
                pages=len(doc),
                content_length=len(content),
            )

            return Document(content=content, metadata=metadata)

        except fitz.FileDataError as e:
            raise DocumentProcessingError(f"Invalid PDF file {file_path}: {e}")
        except Exception as e:
            logger.error("pdf_processing_failed", file_path=str(file_path), error=str(e))
            raise DocumentProcessingError(f"Failed to process PDF {file_path}: {e}")

    def create_chunks(self, document: Document) -> List[DocumentChunk]:
        """
        Create semantic chunks from a PDF document.

        Preserves document structure and adds rich metadata.

        Args:
            document: Document to chunk

        Returns:
            List[DocumentChunk]: Document chunks with metadata

        Raises:
            DocumentProcessingError: If chunking fails
        """
        logger.info("chunking_document", document_name=document.document_name)

        try:
            # Use semantic chunking strategy
            text_chunks = semantic_chunk_text(
                document.content,
                chunk_size=self.chunk_size,
                overlap=self.chunk_overlap,
            )

            chunks = []
            total_chunks = len(text_chunks)

            for idx, text in enumerate(text_chunks):
                # Generate chunk metadata
                chunk_metadata = ChunkMetadata(
                    document_name=document.document_name,
                    document_type=document.document_type,
                    chunk_index=idx,
                    total_chunks=total_chunks,
                    chunk_id=generate_chunk_id(document.document_name, idx),
                    fiscal_period=document.metadata.fiscal_period,
                    has_table=detect_table_markers(text),
                    has_numerical_data=has_numerical_data(text),
                    section=self._extract_section_name(text),
                )

                chunk = DocumentChunk(text=text, metadata=chunk_metadata)
                chunks.append(chunk)

            logger.info(
                "document_chunked",
                document_name=document.document_name,
                total_chunks=total_chunks,
            )

            return chunks

        except Exception as e:
            logger.error(
                "chunking_failed",
                document_name=document.document_name,
                error=str(e),
            )
            raise DocumentProcessingError(f"Failed to chunk document: {e}")

    def _extract_section_name(self, text: str) -> str | None:
        """
        Extract section name from chunk text.

        Looks for common section headers in financial documents.

        Args:
            text: Chunk text

        Returns:
            str | None: Section name if found
        """
        # Common section headers in financial documents
        section_markers = [
            "Executive Summary",
            "Financial Highlights",
            "Revenue",
            "Expenses",
            "Operating Income",
            "Net Income",
            "Cash Flow",
            "Balance Sheet",
            "Risk Factors",
            "Management Discussion",
            "MD&A",
            "Outlook",
            "Guidance",
        ]

        # Check first few lines for section headers
        first_lines = text.split("\n")[:5]
        first_text = " ".join(first_lines)

        for marker in section_markers:
            if marker.lower() in first_text.lower():
                return marker

        return None
