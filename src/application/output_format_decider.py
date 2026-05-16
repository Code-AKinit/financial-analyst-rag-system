"""
Output format decision logic.

Intelligently decides whether to return markdown, PDF, or Excel.
"""

from typing import Any, Dict

from src.config.logging_config import get_logger
from src.domain.models.query import Query
from src.utils.constants import OutputFormat, QueryIntent

logger = get_logger(__name__)


class OutputFormatDecider:
    """
    Decides appropriate output format based on query and response.

    Makes intelligent decisions about markdown vs PDF vs Excel.
    """

    def __init__(self):
        """Initialize output format decider."""
        logger.info("output_format_decider_initialized")

    def decide_format(
        self,
        query: Query,
        response_text: str,
        structured_data: Dict[str, Any] = None,
    ) -> OutputFormat:
        """
        Decide the best output format for the response.

        Args:
            query: User query
            response_text: Generated response text
            structured_data: Optional structured data extracted

        Returns:
            OutputFormat: Chosen output format
        """
        logger.info("deciding_output_format", query_intent=query.intent.value)

        # Rule 1: Check for explicit tabular data
        if self._should_use_excel(query, response_text, structured_data):
            logger.info("format_decided", format="excel")
            return OutputFormat.EXCEL

        # Rule 2: Check for analytical/report content
        if self._should_use_pdf(query, response_text):
            logger.info("format_decided", format="pdf")
            return OutputFormat.PDF

        # Rule 3: Default to markdown
        logger.info("format_decided", format="markdown")
        return OutputFormat.MARKDOWN

    def _should_use_excel(
        self,
        query: Query,
        response_text: str,
        structured_data: Dict[str, Any],
    ) -> bool:
        """
        Check if Excel format is appropriate.

        Args:
            query: User query
            response_text: Response text
            structured_data: Structured data

        Returns:
            bool: True if Excel is appropriate
        """
        excel_indicators = []

        # Indicator 1: Structured data with multiple rows
        if structured_data:
            if "rows" in structured_data and len(structured_data["rows"]) > 3:
                excel_indicators.append(True)

            if "metrics" in structured_data and len(structured_data["metrics"]) > 5:
                excel_indicators.append(True)

        # Indicator 2: Query keywords
        query_lower = query.text.lower()
        excel_keywords = [
            "table",
            "list",
            "breakdown",
            "compare all",
            "all quarters",
            "spreadsheet",
            "data",
            "export",
        ]

        if any(keyword in query_lower for keyword in excel_keywords):
            excel_indicators.append(True)

        # Indicator 3: Response has many numbers in tabular format
        if self._has_tabular_structure(response_text):
            excel_indicators.append(True)

        # Decide: Need at least 2 indicators
        return sum(excel_indicators) >= 2

    def _should_use_pdf(self, query: Query, response_text: str) -> bool:
        """
        Check if PDF format is appropriate.

        Args:
            query: User query
            response_text: Response text

        Returns:
            bool: True if PDF is appropriate
        """
        pdf_indicators = []

        # Indicator 1: Analytical intent
        if query.intent == QueryIntent.ANALYTICAL:
            pdf_indicators.append(True)

        # Indicator 2: Long response
        if len(response_text) > 1500:
            pdf_indicators.append(True)

        # Indicator 3: Query keywords
        query_lower = query.text.lower()
        pdf_keywords = [
            "analyze",
            "analysis",
            "report",
            "summary",
            "overview",
            "trend",
            "comparison",
            "evaluate",
            "assessment",
            "review",
        ]

        if any(keyword in query_lower for keyword in pdf_keywords):
            pdf_indicators.append(True)

        # Indicator 4: Multiple sections in response
        if response_text.count("\n\n") > 3:
            pdf_indicators.append(True)

        # Indicator 5: Has headers/sections
        if self._has_section_headers(response_text):
            pdf_indicators.append(True)

        # Decide: Need at least 2 indicators
        return sum(pdf_indicators) >= 2

    def _has_tabular_structure(self, text: str) -> bool:
        """
        Check if text has tabular structure.

        Args:
            text: Text to check

        Returns:
            bool: True if tabular
        """
        # Look for markdown tables
        if "|" in text and text.count("|") > 6:
            return True

        # Look for consistent column structure
        lines = text.split("\n")
        potential_table_lines = [line for line in lines if "\t" in line or "  " in line]

        if len(potential_table_lines) > 3:
            return True

        return False

    def _has_section_headers(self, text: str) -> bool:
        """
        Check if text has section headers.

        Args:
            text: Text to check

        Returns:
            bool: True if has headers
        """
        # Look for markdown headers
        lines = text.split("\n")

        header_count = sum(1 for line in lines if line.strip().startswith("#"))

        return header_count >= 2

    def override_format(
        self,
        requested_format: str,
    ) -> OutputFormat:
        """
        Override format based on explicit user request.

        Args:
            requested_format: Requested format string

        Returns:
            OutputFormat: Chosen format
        """
        format_map = {
            "pdf": OutputFormat.PDF,
            "excel": OutputFormat.EXCEL,
            "markdown": OutputFormat.MARKDOWN,
            "text": OutputFormat.MARKDOWN,
        }

        requested_lower = requested_format.lower()

        return format_map.get(requested_lower, OutputFormat.MARKDOWN)
