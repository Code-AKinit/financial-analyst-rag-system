"""
Main chatbot orchestrator.

Coordinates all services to answer queries intelligently.
"""

import time
from typing import Optional

from src.application.conversation_manager import ConversationManager
from src.application.output_format_decider import OutputFormatDecider
from src.config.logging_config import get_logger
from src.config.settings import get_settings
from src.domain.models.query import Query
from src.domain.models.response import Response, ResponseMetadata
from src.domain.services.citation_service import CitationService
from src.domain.services.context_synthesis_service import ContextSynthesisService
from src.domain.services.query_understanding_service import QueryUnderstandingService
from src.infrastructure.llm.gemini_gateway import GeminiGateway
from src.infrastructure.vector_store.chroma_store import ChromaVectorStore
from src.infrastructure.vector_store.retrieval_strategies import RetrievalStrategy
from src.utils.exceptions import FinancialAnalystError

logger = get_logger(__name__)


class ChatbotOrchestrator:
    """
    Main orchestrator for the financial analyst chatbot.

    Coordinates all services to provide intelligent responses.
    """

    def __init__(self):
        """Initialize chatbot orchestrator with all dependencies."""
        logger.info("initializing_chatbot_orchestrator")

        settings = get_settings()

        # Initialize infrastructure
        self.llm = GeminiGateway()
        self.vector_store = ChromaVectorStore()

        # Initialize domain services
        self.query_service = QueryUnderstandingService(self.llm)
        self.context_service = ContextSynthesisService()
        self.citation_service = CitationService()

        # Initialize retrieval
        self.retrieval = RetrievalStrategy(self.vector_store)

        # Initialize application services
        self.conversation_manager = ConversationManager(self.llm)
        self.format_decider = OutputFormatDecider()

        self.settings = settings

        logger.info("chatbot_orchestrator_initialized")

    def answer_query(
        self,
        query_text: str,
        conversation_id: str,
    ) -> Response:
        """
        Answer a user query with full intelligence.

        Args:
            query_text: User query text
            conversation_id: Conversation identifier

        Returns:
            Response: Generated response with citations

        Raises:
            FinancialAnalystError: If answering fails
        """
        start_time = time.time()

        logger.info("processing_query", query=query_text[:100], conversation_id=conversation_id)

        try:
            # Step 1: Create query object
            query = Query(
                text=query_text,
                conversation_id=conversation_id,
            )

            # Step 2: Add to conversation history
            self.conversation_manager.add_user_message(conversation_id, query_text)

            # Step 3: Understand query (intent, entities)
            query = self.query_service.analyze_query(query)

            # Step 4: Enhance with conversational context
            query = self.conversation_manager.enhance_query_with_context(
                query, conversation_id
            )

            # Step 5: Retrieve relevant chunks
            retrieved_chunks = self.retrieval.retrieve(
                query=query,
                top_k=self.settings.retrieval_top_k,
            )

            if not retrieved_chunks:
                return self._create_no_results_response(query)

            # Step 6: Synthesize context
            context = self.context_service.synthesize_context(
                query=query,
                chunks=retrieved_chunks,
            )

            # Step 7: Get conversation history for LLM
            conversation_history = self.conversation_manager.get_conversation_context(
                conversation_id
            )

            # Step 8: Generate response
            response_text = self.llm.generate_response(
                query=query,
                context=context,
                conversation_history=conversation_history,
            )

            # Step 9: Generate citations
            citations = self.citation_service.generate_citations(
                response_text=response_text,
                source_chunks=retrieved_chunks,
            )

            # Step 10: Decide output format
            output_format = self.format_decider.decide_format(
                query=query,
                response_text=response_text,
            )

            # Step 11: Create response object
            processing_time = (time.time() - start_time) * 1000  # Convert to ms

            response = Response(
                content=response_text,
                citations=citations,
                query_id=query.query_id,
                output_format=output_format,
                retrieved_chunks=retrieved_chunks,
                metadata=ResponseMetadata(
                    retrieved_chunks_count=len(retrieved_chunks),
                    processing_time_ms=processing_time,
                    model_used=self.settings.gemini_model,
                    temperature=self.settings.gemini_temperature,
                    reranked=self.settings.rerank_enabled,
                ),
            )

            # Step 12: Add assistant response to conversation
            self.conversation_manager.add_assistant_message(
                conversation_id, response.get_full_response()
            )

            logger.info(
                "query_processed",
                query_id=query.query_id,
                processing_time_ms=processing_time,
                output_format=output_format.value,
            )

            return response

        except Exception as e:
            # Get more details about the error
            import traceback
            error_details = traceback.format_exc()
            logger.error("query_processing_failed", error=str(e), query=query_text[:100], traceback=error_details)

            # Extract more helpful error message
            error_msg = str(e)
            if "RetryError" in error_msg:
                error_msg = "LLM API call failed after retries. Check API key and network connectivity."

            raise FinancialAnalystError(f"Failed to process query: {error_msg}")

    def _create_no_results_response(self, query: Query) -> Response:
        """
        Create response when no relevant documents found.

        Args:
            query: User query

        Returns:
            Response: No results response
        """
        logger.warning("no_results_found", query=query.text[:100])

        response_text = (
            "I couldn't find relevant information in the financial documents to answer "
            "your question. This might be because:\n\n"
            "1. The information isn't in the documents I have access to\n"
            "2. The query is too specific or uses different terminology\n"
            "3. The documents haven't been indexed yet\n\n"
            "Try rephrasing your question or asking about a different topic."
        )

        return Response(
            content=response_text,
            citations=[],
            query_id=query.query_id,
            confidence=0.0,
        )

    def clear_conversation(self, conversation_id: str) -> None:
        """
        Clear conversation history.

        Args:
            conversation_id: Conversation identifier
        """
        self.conversation_manager.clear_conversation(conversation_id)
        logger.info("conversation_cleared", conversation_id=conversation_id)

    def get_conversation_summary(self, conversation_id: str) -> str:
        """
        Get summary of conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            str: Conversation summary
        """
        return self.conversation_manager.get_conversation_summary(conversation_id)

    def check_system_status(self) -> dict:
        """
        Check system health and statistics.

        Returns:
            dict: System status
        """
        try:
            stats = self.vector_store.get_collection_stats()

            return {
                "status": "healthy",
                "vector_store": {
                    "collection": stats["collection_name"],
                    "document_count": stats["document_count"],
                },
                "settings": {
                    "model": self.settings.gemini_model,
                    "retrieval_top_k": self.settings.retrieval_top_k,
                    "rerank_enabled": self.settings.rerank_enabled,
                },
            }

        except Exception as e:
            logger.error("system_check_failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
            }
