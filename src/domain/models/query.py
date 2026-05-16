"""
Domain models for queries.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from src.utils.constants import FiscalPeriod, QueryIntent


@dataclass
class QueryMetadata:
    """
    Metadata extracted from a query.

    Attributes:
        entities: Named entities mentioned
        fiscal_periods: Fiscal periods mentioned
        document_types: Document types referenced
        keywords: Key financial terms
        date_range: Date range if specified
    """

    entities: List[str] = field(default_factory=list)
    fiscal_periods: List[FiscalPeriod] = field(default_factory=list)
    document_types: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    date_range: Optional[str] = None


@dataclass
class Query:
    """
    Represents a user query with metadata.

    Attributes:
        text: Original query text
        intent: Classified intent
        metadata: Extracted query metadata
        conversation_id: ID of conversation this query belongs to
        query_id: Unique identifier for this query
        timestamp: When query was received
        rewritten_text: Rewritten query for better retrieval
        is_follow_up: Whether this is a follow-up question
    """

    text: str
    conversation_id: str
    query_id: str = field(default_factory=lambda: datetime.now().isoformat())
    timestamp: datetime = field(default_factory=datetime.now)
    intent: QueryIntent = QueryIntent.FACTUAL
    metadata: QueryMetadata = field(default_factory=QueryMetadata)
    rewritten_text: Optional[str] = None
    is_follow_up: bool = False

    def __post_init__(self):
        """Validate query after initialization."""
        if not self.text or not self.text.strip():
            raise ValueError("Query text cannot be empty")

    @property
    def effective_text(self) -> str:
        """
        Get the text to use for retrieval.

        Returns rewritten text if available, otherwise original.
        """
        return self.rewritten_text if self.rewritten_text else self.text
