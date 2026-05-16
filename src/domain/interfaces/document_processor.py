"""
Interface for Document Processor (Port).

Defines the contract for processing different document types.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from src.domain.models.document import Document, DocumentChunk


class DocumentProcessor(ABC):
    """
    Abstract interface for document processing operations.

    This port defines how the domain layer interacts with document processors,
    independent of the specific document type.
    """

    @abstractmethod
    def can_process(self, file_path: Path) -> bool:
        """
        Check if this processor can handle the file.

        Args:
            file_path: Path to file

        Returns:
            bool: True if processor can handle this file
        """
        pass

    @abstractmethod
    def process_document(self, file_path: Path) -> Document:
        """
        Process a document and extract content.

        Args:
            file_path: Path to document file

        Returns:
            Document: Processed document with metadata

        Raises:
            DocumentProcessingError: If processing fails
        """
        pass

    @abstractmethod
    def create_chunks(self, document: Document) -> List[DocumentChunk]:
        """
        Create chunks from a document.

        Args:
            document: Document to chunk

        Returns:
            List[DocumentChunk]: Document chunks with metadata

        Raises:
            DocumentProcessingError: If chunking fails
        """
        pass
