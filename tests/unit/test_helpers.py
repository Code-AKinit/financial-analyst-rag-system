"""
Unit tests for utility helpers.
"""

import pytest

from src.utils.helpers import (
    detect_table_markers,
    extract_fiscal_period_from_text,
    format_file_size,
    has_numerical_data,
    sanitize_filename,
    truncate_text,
)


class TestHelpers:
    """Tests for utility helper functions."""

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        assert sanitize_filename("test<file>.pdf") == "test_file_.pdf"
        assert sanitize_filename("normal_file.pdf") == "normal_file.pdf"
        assert sanitize_filename("file:with:colons.pdf") == "file_with_colons.pdf"

    def test_extract_fiscal_period(self):
        """Test fiscal period extraction."""
        assert extract_fiscal_period_from_text("Q1 2024 results") == "Q1"
        assert extract_fiscal_period_from_text("Second quarter earnings") == "Q2"
        assert extract_fiscal_period_from_text("Annual report FY 2023") == "FY"
        assert extract_fiscal_period_from_text("Random text") is None

    def test_has_numerical_data(self):
        """Test numerical data detection."""
        assert has_numerical_data("Revenue was $10M") is True
        assert has_numerical_data("Growth of 25%") is True
        assert has_numerical_data("Just text") is False

    def test_detect_table_markers(self):
        """Test table detection."""
        markdown_table = "| Col1 | Col2 |\n|------|------|\n| A | B |"
        assert detect_table_markers(markdown_table) is True

        plain_text = "This is just plain text"
        assert detect_table_markers(plain_text) is False

    def test_truncate_text(self):
        """Test text truncation."""
        long_text = "a" * 300
        truncated = truncate_text(long_text, max_length=100)

        assert len(truncated) <= 103  # 100 + "..."
        assert truncated.endswith("...")

        short_text = "short"
        assert truncate_text(short_text, max_length=100) == "short"

    def test_format_file_size(self):
        """Test file size formatting."""
        assert format_file_size(500) == "500.0 B"
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"
