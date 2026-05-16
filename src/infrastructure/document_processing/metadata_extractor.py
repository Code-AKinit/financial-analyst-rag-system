"""
Metadata extraction utilities for documents.
"""

import re
from typing import Optional

from src.utils.constants import DocumentType, FiscalPeriod


def extract_document_type(filename: str) -> DocumentType:
    """
    Extract document type from filename.

    Args:
        filename: Document filename

    Returns:
        DocumentType: Detected document type
    """
    filename_lower = filename.lower()

    # Check for quarterly earnings
    if any(q in filename_lower for q in ["q1", "q2", "q3", "q4", "quarter"]):
        return DocumentType.QUARTERLY_EARNINGS

    # Check for annual report
    if any(term in filename_lower for term in ["annual", "10-k", "yearly", "fy"]):
        return DocumentType.ANNUAL_REPORT

    # Check for stock data
    if any(term in filename_lower for term in ["stock", "price", "trading"]):
        return DocumentType.STOCK_PRICES

    # Check for investor data
    if any(term in filename_lower for term in ["investor", "sharehol", "equity"]):
        return DocumentType.INVESTOR_DATA

    return DocumentType.UNKNOWN


def extract_fiscal_period(filename: str, content: Optional[str] = None) -> Optional[FiscalPeriod]:
    """
    Extract fiscal period from filename and optionally content.

    Args:
        filename: Document filename
        content: Optional document content to search

    Returns:
        FiscalPeriod | None: Fiscal period if found
    """
    # Check filename first
    filename_lower = filename.lower()

    if "q1" in filename_lower or "first quarter" in filename_lower:
        return FiscalPeriod.Q1
    elif "q2" in filename_lower or "second quarter" in filename_lower:
        return FiscalPeriod.Q2
    elif "q3" in filename_lower or "third quarter" in filename_lower:
        return FiscalPeriod.Q3
    elif "q4" in filename_lower or "fourth quarter" in filename_lower:
        return FiscalPeriod.Q4
    elif any(term in filename_lower for term in ["annual", "fy", "fiscal year", "full year"]):
        return FiscalPeriod.FY

    # Check content if provided
    if content:
        content_lower = content[:2000].lower()  # Check first 2000 chars

        # Look for fiscal period mentions
        quarter_patterns = [
            (r'\bq1\b', FiscalPeriod.Q1),
            (r'\bfirst quarter\b', FiscalPeriod.Q1),
            (r'\bq2\b', FiscalPeriod.Q2),
            (r'\bsecond quarter\b', FiscalPeriod.Q2),
            (r'\bq3\b', FiscalPeriod.Q3),
            (r'\bthird quarter\b', FiscalPeriod.Q3),
            (r'\bq4\b', FiscalPeriod.Q4),
            (r'\bfourth quarter\b', FiscalPeriod.Q4),
            (r'\bfiscal year\b', FiscalPeriod.FY),
            (r'\bannual report\b', FiscalPeriod.FY),
        ]

        for pattern, period in quarter_patterns:
            if re.search(pattern, content_lower):
                return period

    return None


def extract_year(filename: str, content: Optional[str] = None) -> Optional[int]:
    """
    Extract year from filename or content.

    Args:
        filename: Document filename
        content: Optional document content

    Returns:
        int | None: Year if found
    """
    # Look for 4-digit year in filename
    year_match = re.search(r'\b(20\d{2})\b', filename)
    if year_match:
        return int(year_match.group(1))

    # Check content if provided
    if content:
        year_match = re.search(r'\b(20\d{2})\b', content[:1000])
        if year_match:
            return int(year_match.group(1))

    return None


def extract_topics_from_text(text: str) -> list[str]:
    """
    Extract financial topics/keywords from text.

    Args:
        text: Text to analyze

    Returns:
        list[str]: List of detected topics
    """
    topics = []

    # Financial topics to look for
    topic_keywords = {
        "revenue": ["revenue", "sales", "income from operations"],
        "profit": ["profit", "earnings", "net income"],
        "expenses": ["expenses", "costs", "expenditure"],
        "cash_flow": ["cash flow", "operating cash", "free cash flow"],
        "assets": ["assets", "balance sheet", "total assets"],
        "liabilities": ["liabilities", "debt", "obligations"],
        "equity": ["equity", "shareholders equity", "stockholders equity"],
        "margins": ["margin", "gross margin", "operating margin"],
        "growth": ["growth", "increase", "expansion"],
        "risk": ["risk", "uncertainty", "challenges"],
    }

    text_lower = text.lower()

    for topic, keywords in topic_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            topics.append(topic)

    return topics
