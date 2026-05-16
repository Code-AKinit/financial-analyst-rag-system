"""
PDF report generator.

Creates professional PDF reports from responses.
"""

from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.config.logging_config import get_logger
from src.domain.interfaces.report_generator import ReportGenerator
from src.domain.models.response import Response
from src.utils.exceptions import ReportGenerationError

logger = get_logger(__name__)


class PDFReportGenerator(ReportGenerator):
    """
    Generates professional PDF reports using ReportLab.
    """

    def __init__(self):
        """Initialize PDF generator."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

        logger.info("pdf_generator_initialized")

    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(
            ParagraphStyle(
                name="ReportTitle",
                parent=self.styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#1a365d"),
                spaceAfter=30,
                alignment=1,  # Center
            )
        )

        # Subtitle style
        self.styles.add(
            ParagraphStyle(
                name="ReportSubtitle",
                parent=self.styles["Normal"],
                fontSize=12,
                textColor=colors.HexColor("#4a5568"),
                spaceAfter=20,
                alignment=1,  # Center
            )
        )

        # Section header style
        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Heading2"],
                fontSize=14,
                textColor=colors.HexColor("#2d3748"),
                spaceBefore=20,
                spaceAfter=12,
            )
        )

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
        logger.info("generating_pdf_report", query=query_text[:50])

        try:
            # Create PDF document
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            # Build content
            story = []

            # Header
            story.extend(self._build_header(query_text))

            # Main content
            story.extend(self._build_content(response))

            # Citations
            if response.citations:
                story.extend(self._build_citations(response))

            # Footer metadata
            story.extend(self._build_footer(response, metadata))

            # Build PDF
            doc.build(story)

            pdf_bytes = buffer.getvalue()

            logger.info("pdf_report_generated", size_bytes=len(pdf_bytes))

            return pdf_bytes

        except Exception as e:
            logger.error("pdf_generation_failed", error=str(e))
            raise ReportGenerationError(f"Failed to generate PDF: {e}")

    def _build_header(self, query_text: str) -> list:
        """Build PDF header."""
        elements = []

        # Title
        elements.append(
            Paragraph("Financial Analysis Report", self.styles["ReportTitle"])
        )

        # Subtitle with timestamp
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        elements.append(
            Paragraph(f"Generated on {timestamp}", self.styles["ReportSubtitle"])
        )

        elements.append(Spacer(1, 0.3 * inch))

        # Query section
        elements.append(Paragraph("Query", self.styles["SectionHeader"]))
        elements.append(Paragraph(query_text, self.styles["Normal"]))

        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _build_content(self, response: Response) -> list:
        """Build main content section."""
        elements = []

        elements.append(Paragraph("Analysis", self.styles["SectionHeader"]))

        # Split content into paragraphs
        paragraphs = response.content.split("\n\n")

        for para in paragraphs:
            if para.strip():
                # Check if it's a header
                if para.strip().startswith("#"):
                    # Remove markdown header markers
                    header_text = para.strip().lstrip("#").strip()
                    elements.append(
                        Paragraph(header_text, self.styles["SectionHeader"])
                    )
                else:
                    # Regular paragraph
                    # Escape special characters
                    para_escaped = para.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    elements.append(Paragraph(para_escaped, self.styles["Normal"]))
                    elements.append(Spacer(1, 0.15 * inch))

        return elements

    def _build_citations(self, response: Response) -> list:
        """Build citations section."""
        elements = []

        elements.append(Spacer(1, 0.3 * inch))
        elements.append(Paragraph("Sources", self.styles["SectionHeader"]))

        # Build table data
        table_data = [["#", "Document", "Details"]]

        for i, citation in enumerate(response.citations, 1):
            details = []

            if citation.section:
                details.append(f"Section: {citation.section}")
            if citation.page_number:
                details.append(f"Page: {citation.page_number}")

            details_text = ", ".join(details) if details else "N/A"

            table_data.append([
                str(i),
                citation.source_document,
                details_text,
            ])

        # Create table
        table = Table(table_data, colWidths=[0.5 * inch, 3 * inch, 3 * inch])

        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4299e1")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )

        elements.append(table)

        return elements

    def _build_footer(self, response: Response, metadata: Dict[str, Any]) -> list:
        """Build footer with metadata."""
        elements = []

        elements.append(Spacer(1, 0.5 * inch))

        # Divider line
        elements.append(Paragraph("_" * 80, self.styles["Normal"]))

        # Metadata
        meta_text = f"Processing Time: {response.metadata.processing_time_ms:.0f}ms | "
        meta_text += f"Model: {response.metadata.model_used} | "
        meta_text += f"Sources: {response.metadata.retrieved_chunks_count}"

        elements.append(Paragraph(meta_text, self.styles["Normal"]))

        # Generated by
        elements.append(
            Paragraph(
                "<i>Generated by AI Financial Analyst</i>",
                self.styles["Normal"],
            )
        )

        return elements

    def generate_excel_report(
        self,
        data: Dict[str, Any],
        query_text: str,
        metadata: Dict[str, Any],
    ) -> bytes:
        """Not implemented in PDF generator."""
        raise NotImplementedError("Use ExcelReportGenerator for Excel reports")

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
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            file_path = output_path / filename

            with open(file_path, "wb") as f:
                f.write(content)

            logger.info("report_saved", file_path=str(file_path))

            return str(file_path)

        except Exception as e:
            logger.error("report_save_failed", error=str(e))
            raise ReportGenerationError(f"Failed to save report: {e}")
