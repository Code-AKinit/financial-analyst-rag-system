"""
Interface for Report Generator (Port).

Defines the contract for generating reports in various formats.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from src.domain.models.response import Response


class ReportGenerator(ABC):
    """
    Abstract interface for report generation.

    This port defines how the domain layer generates reports,
    independent of the output format.
    """

    @abstractmethod
    def generate_pdf_report(
        self,
        response: Response,
        query_text: str,
        metadata: Dict[str, Any],
    ) -> bytes:
        """
        Generate a PDF report from a response.

        Args:
            response: Response to format as PDF
            query_text: Original query
            metadata: Additional report metadata

        Returns:
            bytes: PDF file content

        Raises:
            ReportGenerationError: If generation fails
        """
        pass

    @abstractmethod
    def generate_excel_report(
        self,
        data: Dict[str, Any],
        query_text: str,
        metadata: Dict[str, Any],
    ) -> bytes:
        """
        Generate an Excel report from structured data.

        Args:
            data: Structured data to format as Excel
            query_text: Original query
            metadata: Additional report metadata

        Returns:
            bytes: Excel file content

        Raises:
            ReportGenerationError: If generation fails
        """
        pass

    @abstractmethod
    def save_report(
        self,
        content: bytes,
        filename: str,
        output_dir: str,
    ) -> str:
        """
        Save report to file system.

        Args:
            content: Report file content
            filename: Name for the file
            output_dir: Directory to save in

        Returns:
            str: Path to saved file

        Raises:
            FileOperationError: If save fails
        """
        pass
