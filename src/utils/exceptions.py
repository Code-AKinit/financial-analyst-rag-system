"""
Custom exceptions for the application.

Provides specific exception types for different error scenarios.
"""


class FinancialAnalystError(Exception):
    """Base exception for all application errors."""

    pass


class ConfigurationError(FinancialAnalystError):
    """Raised when configuration is invalid or missing."""

    pass


class ValidationError(FinancialAnalystError):
    """Raised when input validation fails."""

    pass


class SecurityError(FinancialAnalystError):
    """Raised when security check fails."""

    pass


class DocumentProcessingError(FinancialAnalystError):
    """Raised when document processing fails."""

    pass


class VectorStoreError(FinancialAnalystError):
    """Raised when vector store operations fail."""

    pass


class LLMError(FinancialAnalystError):
    """Raised when LLM operations fail."""

    pass


class RetrievalError(FinancialAnalystError):
    """Raised when retrieval operations fail."""

    pass


class ReportGenerationError(FinancialAnalystError):
    """Raised when report generation fails."""

    pass


class ConversationError(FinancialAnalystError):
    """Raised when conversation management fails."""

    pass


class FileOperationError(FinancialAnalystError):
    """Raised when file operations fail."""

    pass
