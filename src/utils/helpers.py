"""
Utility helper functions.
"""

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def generate_chunk_id(document_name: str, chunk_index: int) -> str:
    """
    Generate a unique ID for a document chunk.

    Args:
        document_name: Name of the document
        chunk_index: Index of the chunk

    Returns:
        str: Unique chunk ID
    """
    content = f"{document_name}_{chunk_index}_{datetime.now().isoformat()}"
    return hashlib.md5(content.encode()).hexdigest()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.

    Args:
        filename: Original filename

    Returns:
        str: Sanitized filename
    """
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized.strip('_')


def extract_fiscal_period_from_text(text: str) -> str | None:
    """
    Extract fiscal period mentions from text.

    Args:
        text: Text to search

    Returns:
        str | None: Fiscal period if found (Q1, Q2, Q3, Q4, FY)
    """
    patterns = [
        r'\bQ[1-4]\b',
        r'\b(first|second|third|fourth)\s+quarter\b',
        r'\bFY\b',
        r'\bfiscal\s+year\b',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            matched_text = match.group()
            # Normalize to Q1-Q4 or FY
            if 'first' in matched_text.lower() or 'Q1' in matched_text:
                return 'Q1'
            elif 'second' in matched_text.lower() or 'Q2' in matched_text:
                return 'Q2'
            elif 'third' in matched_text.lower() or 'Q3' in matched_text:
                return 'Q3'
            elif 'fourth' in matched_text.lower() or 'Q4' in matched_text:
                return 'Q4'
            elif 'FY' in matched_text or 'fiscal year' in matched_text.lower():
                return 'FY'

    return None


def has_numerical_data(text: str) -> bool:
    """
    Check if text contains numerical/financial data.

    Args:
        text: Text to check

    Returns:
        bool: True if text has numbers
    """
    # Look for numbers, currency symbols, percentages
    patterns = [
        r'\$[\d,]+',  # Currency
        r'\d+\.\d+%',  # Percentages
        r'\d{1,3}(,\d{3})+',  # Numbers with commas
        r'\d+\s*(million|billion|thousand|M|B|K)',  # Large numbers
    ]

    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def detect_table_markers(text: str) -> bool:
    """
    Detect if text likely contains table data.

    Args:
        text: Text to check

    Returns:
        bool: True if text appears to have table structure
    """
    # Look for table markers
    indicators = [
        r'\|.*\|.*\|',  # Markdown tables
        r'\t.*\t',  # Tab-separated
        r'^[\s]*[-]+[\s]*$',  # Table dividers
        len(re.findall(r'\d+', text)) > 5,  # Many numbers
    ]

    return any(
        re.search(indicator, text, re.MULTILINE) if isinstance(indicator, str) else indicator
        for indicator in indicators
    )


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)].strip() + suffix


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        str: Formatted size (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def merge_dicts_deep(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)

    Returns:
        Dict: Merged dictionary
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts_deep(result[key], value)
        else:
            result[key] = value

    return result


def safe_get(dictionary: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary value.

    Args:
        dictionary: Dictionary to search
        *keys: Sequence of keys to traverse
        default: Default value if not found

    Returns:
        Any: Value if found, default otherwise

    Example:
        >>> safe_get({"a": {"b": {"c": 1}}}, "a", "b", "c")
        1
        >>> safe_get({"a": {}}, "a", "b", "c", default=0)
        0
    """
    current = dictionary

    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]

    return current
