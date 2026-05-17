"""
Gemini LLM Gateway implementation.

Implements LLM Gateway interface using Google Gemini API.
"""

import json
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.logging_config import get_logger
from src.config.settings import get_settings
from src.domain.interfaces.llm_gateway import LLMGateway
from src.domain.models.query import Query
from src.infrastructure.llm.prompt_templates import PromptTemplates
from src.utils.exceptions import LLMError

logger = get_logger(__name__)


class GeminiGateway(LLMGateway):
    """
    Google Gemini implementation of LLM Gateway.

    Provides access to Gemini models for text generation and analysis.
    """

    def __init__(self):
        """Initialize Gemini gateway."""
        settings = get_settings()

        # Configure Gemini API with REST transport (avoids gRPC SSL issues)
        genai.configure(
            api_key=settings.gemini_api_key,
            transport="rest"  # Use REST instead of gRPC to avoid SSL issues
        )

        self.model_name = settings.gemini_model
        self.temperature = settings.gemini_temperature
        self.max_tokens = settings.gemini_max_tokens

        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=genai.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            ),
        )

        self.templates = PromptTemplates()

        logger.info("gemini_gateway_initialized", model=self.model_name, transport="rest")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
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
            temperature: Override temperature

        Returns:
            str: Generated response text

        Raises:
            LLMError: If generation fails
        """
        logger.info("generating_response", query=query.text[:100])

        try:
            # Format conversation context
            conv_context = ""
            if conversation_history:
                conv_context = f"\nConversation History:\n{self.templates.format_conversation_history(conversation_history)}\n"

            # Build prompt
            prompt = self.templates.ANSWER_GENERATION_PROMPT.format(
                query=query.effective_text,
                context=context,
                conversation_context=conv_context,
            )

            # Add system prompt
            full_prompt = f"{self.templates.FINANCIAL_ANALYST_SYSTEM_PROMPT}\n\n{prompt}"

            # Generate response
            generation_config = genai.GenerationConfig(
                temperature=temperature if temperature is not None else self.temperature,
                max_output_tokens=self.max_tokens,
            )

            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config,
            )

            if not response.text:
                raise LLMError("Empty response from Gemini")

            logger.info("response_generated", response_length=len(response.text))

            return response.text

        except Exception as e:
            logger.error("response_generation_failed", error=str(e))
            raise LLMError(f"Failed to generate response: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
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
        logger.info("generating_structured_response", query=query.text[:100])

        try:
            prompt = f"""Generate a JSON response for this query based on the context.

Query: {query.effective_text}

Context:
{context}

Required JSON Schema:
{json.dumps(schema, indent=2)}

Return ONLY valid JSON matching the schema."""

            response = self.model.generate_content(prompt)

            if not response.text:
                raise LLMError("Empty response from Gemini")

            # Parse JSON
            # Remove markdown code blocks if present
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            result = json.loads(text.strip())

            logger.info("structured_response_generated")

            return result

        except json.JSONDecodeError as e:
            logger.error("json_parsing_failed", error=str(e), response=response.text[:200])
            raise LLMError(f"Failed to parse JSON response: {e}")
        except Exception as e:
            logger.error("structured_response_failed", error=str(e))
            raise LLMError(f"Failed to generate structured response: {e}")

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
        logger.debug("classifying_intent", query=query.text[:100])

        try:
            prompt = self.templates.INTENT_CLASSIFICATION_PROMPT.format(query=query.text)

            response = self.model.generate_content(prompt)

            intent = response.text.strip().lower()

            # Validate intent
            valid_intents = ["factual", "analytical", "computational", "conversational"]
            if intent not in valid_intents:
                logger.warning("invalid_intent", intent=intent)
                intent = "factual"  # Default

            logger.debug("intent_classified", intent=intent)

            return intent

        except Exception as e:
            logger.error("intent_classification_failed", error=str(e))
            # Return default on error
            return "factual"

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
        logger.debug("rewriting_query", query=query.text[:100])

        try:
            prompt = self.templates.QUERY_REWRITE_PROMPT.format(
                conversation_history=self.templates.format_conversation_history(conversation_history),
                current_query=query.text,
            )

            response = self.model.generate_content(prompt)

            rewritten = response.text.strip()

            logger.debug("query_rewritten", original=query.text[:50], rewritten=rewritten[:50])

            return rewritten

        except Exception as e:
            logger.error("query_rewriting_failed", error=str(e))
            # Return original on error
            return query.text

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
        logger.debug("extracting_entities", text_length=len(text))

        try:
            prompt = self.templates.ENTITY_EXTRACTION_PROMPT.format(text=text[:2000])

            response = self.model.generate_content(prompt)

            # Parse JSON
            text_response = response.text.strip()
            if text_response.startswith("```json"):
                text_response = text_response[7:]
            if text_response.startswith("```"):
                text_response = text_response[3:]
            if text_response.endswith("```"):
                text_response = text_response[:-3]

            entities = json.loads(text_response.strip())

            logger.debug("entities_extracted", count=sum(len(v) for v in entities.values()))

            return entities

        except Exception as e:
            logger.error("entity_extraction_failed", error=str(e))
            return {}

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
        logger.debug("summarizing_conversation", message_count=len(messages))

        try:
            prompt = self.templates.CONVERSATION_SUMMARY_PROMPT.format(
                conversation=self.templates.format_conversation_history(messages)
            )

            response = self.model.generate_content(prompt)

            summary = response.text.strip()

            logger.debug("conversation_summarized", summary_length=len(summary))

            return summary

        except Exception as e:
            logger.error("conversation_summary_failed", error=str(e))
            raise LLMError(f"Failed to summarize conversation: {e}")
