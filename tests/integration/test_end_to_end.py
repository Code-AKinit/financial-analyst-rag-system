"""
End-to-end integration tests.

Note: These tests require the system to be properly configured with
API keys and indexed documents.
"""

import pytest

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class TestEndToEnd:
    """
    End-to-end integration tests.

    These tests verify the full system workflow but are skipped by default
    since they require:
    - Valid Gemini API key
    - Indexed documents in vector store
    - External API calls
    """

    @pytest.mark.skip(reason="Requires full system setup and API keys")
    def test_simple_query(self):
        """Test simple factual query."""
        from src.application.chatbot_orchestrator import ChatbotOrchestrator

        orchestrator = ChatbotOrchestrator()

        response = orchestrator.answer_query(
            query_text="What was the Q1 revenue?",
            conversation_id="test_001",
        )

        assert response.content
        assert len(response.citations) > 0

    @pytest.mark.skip(reason="Requires full system setup and API keys")
    def test_follow_up_query(self):
        """Test conversational follow-up."""
        from src.application.chatbot_orchestrator import ChatbotOrchestrator

        orchestrator = ChatbotOrchestrator()

        # First query
        response1 = orchestrator.answer_query(
            query_text="What was the Q1 revenue?",
            conversation_id="test_002",
        )

        assert response1.content

        # Follow-up
        response2 = orchestrator.answer_query(
            query_text="What about Q2?",
            conversation_id="test_002",
        )

        assert response2.content
        # Should have rewritten query
        assert "Q2" in response2.content.lower()

    @pytest.mark.skip(reason="Requires full system setup")
    def test_system_status(self):
        """Test system health check."""
        from src.application.chatbot_orchestrator import ChatbotOrchestrator

        orchestrator = ChatbotOrchestrator()

        status = orchestrator.check_system_status()

        assert status["status"] == "healthy"
        assert "vector_store" in status
        assert status["vector_store"]["document_count"] > 0
