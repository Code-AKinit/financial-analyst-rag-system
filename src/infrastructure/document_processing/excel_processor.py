"""
Excel document processor implementation.

Uses pandas for robust Excel file handling.
"""

from pathlib import Path
from typing import List

import pandas as pd

from src.config.logging_config import get_logger
from src.domain.interfaces.document_processor import DocumentProcessor
from src.domain.models.document import Document, DocumentChunk, ChunkMetadata, DocumentMetadata
from src.utils.constants import DocumentType
from src.utils.exceptions import DocumentProcessingError
from src.utils.helpers import generate_chunk_id

logger = get_logger(__name__)


class ExcelProcessor(DocumentProcessor):
    """
    Processes Excel documents (investor data, financial tables).

    Converts tabular data to text representation while preserving structure.
    """

    SUPPORTED_EXTENSIONS = [".xlsx", ".xls"]

    def can_process(self, file_path: Path) -> bool:
        """
        Check if this processor can handle the file.

        Args:
            file_path: Path to file

        Returns:
            bool: True if file is an Excel file
        """
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def process_document(self, file_path: Path) -> Document:
        """
        Process an Excel document and extract content.

        Args:
            file_path: Path to Excel file

        Returns:
            Document: Processed document with metadata

        Raises:
            DocumentProcessingError: If processing fails
        """
        logger.info("processing_excel", file_path=str(file_path))

        try:
            # Validate file exists
            if not file_path.exists():
                raise DocumentProcessingError(f"File not found: {file_path}")

            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            sheet_contents = []

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)

                # Skip empty sheets
                if df.empty:
                    continue

                # Convert to text representation
                sheet_text = self._dataframe_to_text(df, sheet_name)
                sheet_contents.append(sheet_text)

            content = "\n\n".join(sheet_contents)

            if not content.strip():
                raise DocumentProcessingError(f"No content extracted from {file_path}")

            # Create metadata
            metadata = DocumentMetadata(
                document_name=file_path.name,
                document_type=DocumentType.INVESTOR_DATA,
                file_path=str(file_path),
                file_size_bytes=file_path.stat().st_size,
                additional_metadata={"sheet_count": len(excel_file.sheet_names)},
            )

            logger.info(
                "excel_processed",
                file_path=str(file_path),
                sheets=len(excel_file.sheet_names),
                content_length=len(content),
            )

            return Document(content=content, metadata=metadata)

        except Exception as e:
            logger.error("excel_processing_failed", file_path=str(file_path), error=str(e))
            raise DocumentProcessingError(f"Failed to process Excel file {file_path}: {e}")

    def create_chunks(self, document: Document) -> List[DocumentChunk]:
        """
        Create chunks from Excel document.

        Excel data is typically already structured, so we chunk by logical sections.

        Args:
            document: Document to chunk

        Returns:
            List[DocumentChunk]: Document chunks with metadata

        Raises:
            DocumentProcessingError: If chunking fails
        """
        logger.info("chunking_excel", document_name=document.document_name)

        try:
            # Split by double newlines (sheet boundaries)
            sections = document.content.split("\n\n\n")
            chunks = []

            for idx, section in enumerate(sections):
                if not section.strip():
                    continue

                chunk_metadata = ChunkMetadata(
                    document_name=document.document_name,
                    document_type=document.document_type,
                    chunk_index=idx,
                    total_chunks=len(sections),
                    chunk_id=generate_chunk_id(document.document_name, idx),
                    has_table=True,
                    has_numerical_data=True,
                    section=self._extract_sheet_name(section),
                )

                chunk = DocumentChunk(text=section, metadata=chunk_metadata)
                chunks.append(chunk)

            logger.info(
                "excel_chunked",
                document_name=document.document_name,
                total_chunks=len(chunks),
            )

            return chunks

        except Exception as e:
            logger.error(
                "excel_chunking_failed",
                document_name=document.document_name,
                error=str(e),
            )
            raise DocumentProcessingError(f"Failed to chunk Excel document: {e}")

    def _dataframe_to_text(self, df: pd.DataFrame, sheet_name: str) -> str:
        """
        Convert DataFrame to readable text format.

        Args:
            df: DataFrame to convert
            sheet_name: Name of the sheet

        Returns:
            str: Text representation
        """
        lines = [f"=== Sheet: {sheet_name} ===", ""]

        # Add column headers
        headers = " | ".join(str(col) for col in df.columns)
        lines.append(headers)
        lines.append("-" * len(headers))

        # Add rows
        for _, row in df.iterrows():
            row_text = " | ".join(str(val) for val in row.values)
            lines.append(row_text)

        lines.append("")  # Empty line after sheet

        return "\n".join(lines)

    def _extract_sheet_name(self, text: str) -> str | None:
        """
        Extract sheet name from chunk text.

        Args:
            text: Chunk text

        Returns:
            str | None: Sheet name if found
        """
        # Look for sheet marker
        if text.startswith("=== Sheet:"):
            first_line = text.split("\n")[0]
            return first_line.replace("=== Sheet:", "").replace("===", "").strip()

        return None
