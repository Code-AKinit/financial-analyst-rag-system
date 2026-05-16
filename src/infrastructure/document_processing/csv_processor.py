"""
CSV document processor implementation.

Specialized for time-series data like stock prices.
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


class CSVProcessor(DocumentProcessor):
    """
    Processes CSV documents (stock prices, time-series data).

    Handles time-series data with special chunking strategy.
    """

    SUPPORTED_EXTENSIONS = [".csv"]
    ROWS_PER_CHUNK = 30  # ~1 month of trading days per chunk

    def can_process(self, file_path: Path) -> bool:
        """
        Check if this processor can handle the file.

        Args:
            file_path: Path to file

        Returns:
            bool: True if file is a CSV
        """
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def process_document(self, file_path: Path) -> Document:
        """
        Process a CSV document and extract content.

        Args:
            file_path: Path to CSV file

        Returns:
            Document: Processed document with metadata

        Raises:
            DocumentProcessingError: If processing fails
        """
        logger.info("processing_csv", file_path=str(file_path))

        try:
            # Validate file exists
            if not file_path.exists():
                raise DocumentProcessingError(f"File not found: {file_path}")

            # Read CSV
            df = pd.read_csv(file_path)

            if df.empty:
                raise DocumentProcessingError(f"CSV file is empty: {file_path}")

            # Convert to text representation
            content = self._dataframe_to_text(df)

            # Create metadata
            metadata = DocumentMetadata(
                document_name=file_path.name,
                document_type=DocumentType.STOCK_PRICES,
                file_path=str(file_path),
                file_size_bytes=file_path.stat().st_size,
                additional_metadata={
                    "row_count": len(df),
                    "columns": list(df.columns),
                },
            )

            logger.info(
                "csv_processed",
                file_path=str(file_path),
                rows=len(df),
                columns=len(df.columns),
            )

            return Document(content=content, metadata=metadata)

        except Exception as e:
            logger.error("csv_processing_failed", file_path=str(file_path), error=str(e))
            raise DocumentProcessingError(f"Failed to process CSV file {file_path}: {e}")

    def create_chunks(self, document: Document) -> List[DocumentChunk]:
        """
        Create time-series aware chunks from CSV data.

        Chunks by fixed number of rows to maintain temporal coherence.

        Args:
            document: Document to chunk

        Returns:
            List[DocumentChunk]: Document chunks with metadata

        Raises:
            DocumentProcessingError: If chunking fails
        """
        logger.info("chunking_csv", document_name=document.document_name)

        try:
            # Split content into sections
            lines = document.content.split("\n")
            header = lines[0]
            data_lines = [line for line in lines[1:] if line.strip()]

            chunks = []
            total_chunks = (len(data_lines) + self.ROWS_PER_CHUNK - 1) // self.ROWS_PER_CHUNK

            for idx in range(0, len(data_lines), self.ROWS_PER_CHUNK):
                chunk_lines = data_lines[idx : idx + self.ROWS_PER_CHUNK]

                if not chunk_lines:
                    continue

                # Rebuild chunk with header
                chunk_text = header + "\n" + "\n".join(chunk_lines)

                # Extract date range for this chunk
                date_range = self._extract_date_range(chunk_lines)

                chunk_metadata = ChunkMetadata(
                    document_name=document.document_name,
                    document_type=document.document_type,
                    chunk_index=len(chunks),
                    total_chunks=total_chunks,
                    chunk_id=generate_chunk_id(document.document_name, len(chunks)),
                    has_table=True,
                    has_numerical_data=True,
                    date_range=date_range,
                )

                chunk = DocumentChunk(text=chunk_text, metadata=chunk_metadata)
                chunks.append(chunk)

            logger.info(
                "csv_chunked",
                document_name=document.document_name,
                total_chunks=len(chunks),
            )

            return chunks

        except Exception as e:
            logger.error(
                "csv_chunking_failed",
                document_name=document.document_name,
                error=str(e),
            )
            raise DocumentProcessingError(f"Failed to chunk CSV document: {e}")

    def _dataframe_to_text(self, df: pd.DataFrame) -> str:
        """
        Convert DataFrame to text format.

        Args:
            df: DataFrame to convert

        Returns:
            str: Text representation
        """
        # Use CSV format for preservation
        return df.to_csv(index=False)

    def _extract_date_range(self, lines: List[str]) -> str | None:
        """
        Extract date range from chunk lines.

        Args:
            lines: Chunk data lines

        Returns:
            str | None: Date range if found
        """
        try:
            if not lines:
                return None

            # Assume first column is date
            first_date = lines[0].split(",")[0]
            last_date = lines[-1].split(",")[0]

            return f"{first_date} to {last_date}"

        except Exception:
            return None
