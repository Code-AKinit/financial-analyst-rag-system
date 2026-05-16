"""
Unit tests for domain models.
"""

import pytest
from datetime import datetime

from src.domain.models.conversation import Conversation, Message
from src.domain.models.document import Document, DocumentChunk, ChunkMetadata, DocumentMetadata
from src.domain.models.query import Query, QueryMetadata
from src.domain.models.response import Response, Citation
from src.utils.constants import (
    ConversationRole,
    DocumentType,
    FiscalPeriod,
    OutputFormat,
    QueryIntent,
)


class TestDocumentModels:
    """Tests for document domain models."""

    def test_document_chunk_creation(self):
        """Test creating a document chunk."""
        metadata = ChunkMetadata(
            document_name="test.pdf",
            document_type=DocumentType.ANNUAL_REPORT,
            chunk_index=0,
            total_chunks=10,
            chunk_id="test-chunk-1",
            page_number=1,
        )

        chunk = DocumentChunk(
            text="This is a test chunk.",
            metadata=metadata,
        )

        assert chunk.text == "This is a test chunk."
        assert chunk.chunk_id == "test-chunk-1"
        assert chunk.document_name == "test.pdf"

    def test_document_chunk_empty_text_raises_error(self):
        """Test that empty text raises ValueError."""
        metadata = ChunkMetadata(
            document_name="test.pdf",
            document_type=DocumentType.ANNUAL_REPORT,
            chunk_index=0,
            total_chunks=10,
            chunk_id="test-chunk-1",
        )

        with pytest.raises(ValueError, match="Chunk text cannot be empty"):
            DocumentChunk(text="", metadata=metadata)

    def test_document_creation(self):
        """Test creating a document."""
        doc_metadata = DocumentMetadata(
            document_name="test.pdf",
            document_type=DocumentType.ANNUAL_REPORT,
            file_path="/path/to/test.pdf",
            file_size_bytes=1024,
        )

        doc = Document(
            content="Full document content",
            metadata=doc_metadata,
        )

        assert doc.document_name == "test.pdf"
        assert doc.document_type == DocumentType.ANNUAL_REPORT
        assert len(doc.chunks) == 0


class TestQueryModels:
    """Tests for query domain models."""

    def test_query_creation(self):
        """Test creating a query."""
        query = Query(
            text="What was the Q1 revenue?",
            conversation_id="conv-123",
        )

        assert query.text == "What was the Q1 revenue?"
        assert query.conversation_id == "conv-123"
        assert query.intent == QueryIntent.FACTUAL
        assert query.is_follow_up is False

    def test_query_effective_text(self):
        """Test effective text returns rewritten if available."""
        query = Query(
            text="What about Q2?",
            conversation_id="conv-123",
            rewritten_text="What was the Q2 revenue?",
        )

        assert query.effective_text == "What was the Q2 revenue?"

    def test_query_empty_text_raises_error(self):
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError, match="Query text cannot be empty"):
            Query(text="", conversation_id="conv-123")


class TestResponseModels:
    """Tests for response domain models."""

    def test_response_creation(self):
        """Test creating a response."""
        citation = Citation(
            source_document="test.pdf",
            chunk_id="chunk-1",
            excerpt="Revenue was $10M",
            page_number=5,
        )

        response = Response(
            content="The Q1 revenue was $10M.",
            citations=[citation],
            query_id="query-123",
            output_format=OutputFormat.MARKDOWN,
        )

        assert response.content == "The Q1 revenue was $10M."
        assert len(response.citations) == 1
        assert response.output_format == OutputFormat.MARKDOWN

    def test_response_format_citations(self):
        """Test formatting citations as bibliography."""
        citation = Citation(
            source_document="annual_report.pdf",
            chunk_id="chunk-1",
            excerpt="Revenue increased 20%",
            page_number=10,
            section="Financial Results",
        )

        response = Response(
            content="Revenue grew significantly.",
            citations=[citation],
            query_id="query-123",
        )

        formatted = response.format_citations()

        assert "**Sources:**" in formatted
        assert "annual_report.pdf" in formatted
        assert "Page: 10" in formatted


class TestConversationModels:
    """Tests for conversation domain models."""

    def test_conversation_creation(self):
        """Test creating a conversation."""
        conv = Conversation(conversation_id="conv-123")

        assert conv.conversation_id == "conv-123"
        assert conv.message_count == 0

    def test_conversation_add_message(self):
        """Test adding messages to conversation."""
        conv = Conversation(conversation_id="conv-123")

        conv.add_message(ConversationRole.USER, "Hello!")
        conv.add_message(ConversationRole.ASSISTANT, "Hi there!")

        assert conv.message_count == 2
        assert conv.last_message.content == "Hi there!"

    def test_conversation_get_recent_messages(self):
        """Test retrieving recent messages."""
        conv = Conversation(conversation_id="conv-123")

        # Add 15 messages
        for i in range(15):
            conv.add_message(ConversationRole.USER, f"Message {i}")

        recent = conv.get_recent_messages(count=5)

        assert len(recent) == 5
        assert recent[-1].content == "Message 14"

    def test_message_empty_content_raises_error(self):
        """Test that empty message raises ValueError."""
        with pytest.raises(ValueError, match="Message content cannot be empty"):
            Message(role=ConversationRole.USER, content="")
