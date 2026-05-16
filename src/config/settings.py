"""
Application configuration using Pydantic settings.

This module provides type-safe configuration management with validation,
loading values from environment variables and .env files.
"""

from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with validation.

    All settings can be overridden via environment variables.
    """

    # Application Metadata
    app_name: str = Field(default="AI Financial Analyst", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug_mode: bool = Field(default=False, description="Enable debug mode")

    # LLM Configuration
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    gemini_model: str = Field(
        default="gemini-1.5-pro",
        description="Gemini model to use (pro for complex, flash for simple)"
    )
    gemini_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="LLM temperature for response generation"
    )
    gemini_max_tokens: int = Field(
        default=8192,
        ge=1,
        le=30000,
        description="Maximum tokens in LLM response"
    )

    # Vector Store Configuration
    chroma_persist_directory: str = Field(
        default="./data/vector_store",
        description="ChromaDB persistence directory"
    )
    embedding_model: str = Field(
        default="models/embedding-001",
        description="Gemini embedding model"
    )
    chunk_size: int = Field(
        default=1000,
        ge=100,
        le=2000,
        description="Document chunk size in characters"
    )
    chunk_overlap: int = Field(
        default=200,
        ge=0,
        le=500,
        description="Overlap between chunks"
    )

    # Retrieval Configuration
    retrieval_top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of chunks to retrieve"
    )
    rerank_enabled: bool = Field(
        default=True,
        description="Enable reranking of retrieved chunks"
    )
    hybrid_search_enabled: bool = Field(
        default=True,
        description="Enable hybrid vector+keyword search"
    )

    # Security Configuration
    max_query_length: int = Field(
        default=2000,
        description="Maximum allowed query length"
    )
    max_file_size_mb: int = Field(
        default=50,
        description="Maximum file size in MB"
    )
    allowed_file_types: str = Field(
        default=".pdf,.xlsx,.csv",
        description="Comma-separated allowed file extensions"
    )

    # Output Configuration
    output_dir: str = Field(
        default="./outputs",
        description="Directory for generated outputs"
    )
    pdf_report_enabled: bool = Field(
        default=True,
        description="Enable PDF report generation"
    )
    excel_report_enabled: bool = Field(
        default=True,
        description="Enable Excel report generation"
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or console)"
    )
    log_file: str = Field(
        default="./outputs/logs/app.log",
        description="Log file path"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @field_validator("gemini_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate that API key is set and not placeholder."""
        if not v or v in ["your-gemini-api-key-here", "your-api-key-here"]:
            raise ValueError(
                "Valid Gemini API key required. "
                "Get one at https://makersuite.google.com/app/apikey"
            )
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()

    @property
    def allowed_file_types_list(self) -> List[str]:
        """Parse allowed file types into list."""
        return [ext.strip() for ext in self.allowed_file_types.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        """Convert max file size to bytes."""
        return self.max_file_size_mb * 1024 * 1024

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.chroma_persist_directory,
            self.output_dir,
            f"{self.output_dir}/reports",
            f"{self.output_dir}/excel",
            f"{self.output_dir}/logs",
            "data/raw",
            "data/processed",
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Get or create global settings instance.

    Returns:
        Settings: Application settings
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_directories()
    return _settings


def reload_settings() -> Settings:
    """
    Force reload settings from environment.

    Useful for testing or when environment variables change.

    Returns:
        Settings: Reloaded application settings
    """
    global _settings
    _settings = Settings()
    _settings.ensure_directories()
    return _settings
