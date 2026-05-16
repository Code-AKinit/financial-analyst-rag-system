"""
Interface for LLM Gateway (Port).

Defines the contract for interacting with Language Models.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.domain.models.query import Query
from src.domain.models.response import Response


class LLMGateway(ABC):
    """
    Abstract interface for LLM operations.

    This port defines how the domain layer interacts with LLMs,
    independent of the specific provider (Gemini, OpenAI, etc.).
    """

    @abstractmethod
    def generate_response(
        self,
        query: Query,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Generate a response to a query given context.

        Args:
            query: User query
            context: Retrieved context from documents
            conversation_history: Previous conversation messages
            temperature: Temperature for generation

        Returns:
            str: Generated response text

        Raises:
            LLMError: If generation fails
        """
        pass

    @abstractmethod
    def generate_structured_response(
        self,
        query: Query,
        context: str,
        schema: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a structured response (JSON) given a schema.

        Args:
            query: User query
            context: Retrieved context
            schema: JSON schema for response structure
            conversation_history: Previous conversation messages

        Returns:
            Dict: Structured response matching schema

        Raises:
            LLMError: If generation fails
        """
        pass

    @abstractmethod
    def classify_intent(self, query: Query) -> str:
        """
        Classify the intent of a query.

        Args:
            query: User query

        Returns:
            str: Intent classification

        Raises:
            LLMError: If classification fails
        """
        pass

    @abstractmethod
    def rewrite_query(
        self,
        query: Query,
        conversation_history: List[Dict[str, str]],
    ) -> str:
        """
        Rewrite a query to be self-contained.

        Args:
            query: User query
            conversation_history: Previous conversation messages

        Returns:
            str: Rewritten query

        Raises:
            LLMError: If rewriting fails
        """
        pass

    @abstractmethod
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text.

        Args:
            text: Text to process

        Returns:
            Dict: Entity types mapped to entity values

        Raises:
            LLMError: If extraction fails
        """
        pass

    @abstractmethod
    def summarize_conversation(
        self,
        messages: List[Dict[str, str]],
    ) -> str:
        """
        Summarize conversation history concisely.

        Args:
            messages: Conversation messages

        Returns:
            str: Concise summary

        Raises:
            LLMError: If summarization fails
        """
        pass
