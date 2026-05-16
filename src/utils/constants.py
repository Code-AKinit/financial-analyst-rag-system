"""
System-wide constants and enumerations.
"""

from enum import Enum


class DocumentType(str, Enum):
    """Types of financial documents supported."""

    ANNUAL_REPORT = "annual_report"
    QUARTERLY_EARNINGS = "quarterly_earnings"
    INVESTOR_DATA = "investor_data"
    STOCK_PRICES = "stock_prices"
    UNKNOWN = "unknown"


class QueryIntent(str, Enum):
    """Intent classification for user queries."""

    FACTUAL = "factual"  # Simple fact retrieval
    ANALYTICAL = "analytical"  # Analysis/comparison/trends
    COMPUTATIONAL = "computational"  # Calculations required
    CONVERSATIONAL = "conversational"  # Follow-up/clarification


class OutputFormat(str, Enum):
    """Output format for responses."""

    MARKDOWN = "markdown"  # Simple text response
    PDF = "pdf"  # Formatted PDF report
    EXCEL = "excel"  # Excel spreadsheet


class ConversationRole(str, Enum):
    """Roles in conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class FiscalPeriod(str, Enum):
    """Fiscal period identifiers."""

    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"
    FY = "FY"  # Full year
    UNKNOWN = "unknown"


# System Constants
DEFAULT_COLLECTION_NAME = "financial_documents"
MAX_CONVERSATION_HISTORY = 10
CITATION_FORMAT = "[{index}]"

# Chunk Processing
MIN_CHUNK_SIZE = 100
MAX_CHUNK_SIZE = 2000
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200

# Retrieval
DEFAULT_TOP_K = 5
MAX_TOP_K = 20
RERANK_TOP_K = 10

# LLM Generation
DEFAULT_TEMPERATURE = 0.1
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30

# File Processing
SUPPORTED_PDF_EXTENSIONS = [".pdf"]
SUPPORTED_EXCEL_EXTENSIONS = [".xlsx", ".xls"]
SUPPORTED_CSV_EXTENSIONS = [".csv"]
SUPPORTED_EXTENSIONS = (
    SUPPORTED_PDF_EXTENSIONS + SUPPORTED_EXCEL_EXTENSIONS + SUPPORTED_CSV_EXTENSIONS
)

# Security
DANGEROUS_PROMPT_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"disregard\s+above",
    r"system\s*:",
    r"<\|.*?\|>",  # Special tokens
    r"\\x[0-9a-fA-F]{2}",  # Hex escape sequences
]
