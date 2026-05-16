"""
Conversation manager for maintaining chat context and history.
"""

from typing import Dict, List, Optional

from src.config.logging_config import get_logger
from src.domain.interfaces.llm_gateway import LLMGateway
from src.domain.models.conversation import Conversation, Message
from src.domain.models.query import Query
from src.utils.constants import ConversationRole, MAX_CONVERSATION_HISTORY

logger = get_logger(__name__)


class ConversationManager:
    """
    Manages conversation state, history, and context across turns.

    Handles query rewriting, entity tracking, and context compression.
    """

    def __init__(self, llm_gateway: LLMGateway):
        """
        Initialize conversation manager.

        Args:
            llm_gateway: LLM gateway for query rewriting and summarization
        """
        self.llm = llm_gateway
        self.conversations: Dict[str, Conversation] = {}

        logger.info("conversation_manager_initialized")

    def get_or_create_conversation(self, conversation_id: str) -> Conversation:
        """
        Get existing conversation or create new one.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Conversation: Conversation object
        """
        if conversation_id not in self.conversations:
            logger.info("creating_new_conversation", conversation_id=conversation_id)
            self.conversations[conversation_id] = Conversation(
                conversation_id=conversation_id
            )

        return self.conversations[conversation_id]

    def add_user_message(self, conversation_id: str, message: str) -> None:
        """
        Add user message to conversation.

        Args:
            conversation_id: Conversation identifier
            message: User message content
        """
        conversation = self.get_or_create_conversation(conversation_id)
        conversation.add_message(ConversationRole.USER, message)

        logger.debug("user_message_added", conversation_id=conversation_id)

    def add_assistant_message(self, conversation_id: str, message: str) -> None:
        """
        Add assistant message to conversation.

        Args:
            conversation_id: Conversation identifier
            message: Assistant message content
        """
        conversation = self.get_or_create_conversation(conversation_id)
        conversation.add_message(ConversationRole.ASSISTANT, message)

        logger.debug("assistant_message_added", conversation_id=conversation_id)

    def enhance_query_with_context(
        self,
        query: Query,
        conversation_id: str,
    ) -> Query:
        """
        Enhance query with conversational context.

        Rewrites follow-up queries to be self-contained.

        Args:
            query: User query
            conversation_id: Conversation identifier

        Returns:
            Query: Enhanced query
        """
        conversation = self.get_or_create_conversation(conversation_id)

        # Check if this is a follow-up question
        if self._is_follow_up_query(query, conversation):
            logger.info("rewriting_follow_up_query", query=query.text[:100])

            query.is_follow_up = True

            # Get conversation history for context
            history = conversation.format_for_llm(max_messages=MAX_CONVERSATION_HISTORY)

            try:
                # Rewrite query to be self-contained
                rewritten = self.llm.rewrite_query(query, history)

                query.rewritten_text = rewritten

                logger.info(
                    "query_rewritten",
                    original=query.text[:50],
                    rewritten=rewritten[:50],
                )

            except Exception as e:
                logger.warning("query_rewriting_failed", error=str(e))
                # Continue with original query

        return query

    def _is_follow_up_query(self, query: Query, conversation: Conversation) -> bool:
        """
        Detect if query is a follow-up question.

        Args:
            query: User query
            conversation: Conversation object

        Returns:
            bool: True if follow-up
        """
        # If no history, it's not a follow-up
        if conversation.message_count < 2:
            return False

        # Check for follow-up indicators
        query_lower = query.text.lower()

        follow_up_indicators = [
            # Pronouns
            " it ",
            " they ",
            " them ",
            " that ",
            " this ",
            " those ",
            " these ",
            # Referential phrases
            "what about",
            "how about",
            "compared to",
            "same for",
            "also",
            "additionally",
            "and what",
            "tell me more",
            "explain",
            # Questions without context
            query_lower.startswith("and "),
            query_lower.startswith("but "),
            query_lower.startswith("how "),
            query_lower.startswith("why "),
            query_lower.startswith("when "),
            query_lower.startswith("what "),
        ]

        # Very short queries are likely follow-ups
        if len(query.text.split()) <= 5:
            return True

        # Check indicators
        return any(
            indicator in query_lower if isinstance(indicator, str) else indicator
            for indicator in follow_up_indicators
        )

    def get_conversation_context(
        self,
        conversation_id: str,
        max_messages: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """
        Get conversation context for LLM.

        Args:
            conversation_id: Conversation identifier
            max_messages: Maximum messages to include

        Returns:
            List[Dict]: Formatted conversation history
        """
        conversation = self.get_or_create_conversation(conversation_id)

        max_messages = max_messages or MAX_CONVERSATION_HISTORY

        return conversation.format_for_llm(max_messages=max_messages)

    def compress_old_messages(self, conversation_id: str) -> None:
        """
        Compress old messages in conversation to save context.

        Args:
            conversation_id: Conversation identifier
        """
        conversation = self.get_or_create_conversation(conversation_id)

        # Only compress if we have many messages
        if conversation.message_count <= MAX_CONVERSATION_HISTORY:
            return

        logger.info("compressing_conversation", conversation_id=conversation_id)

        try:
            # Get old messages to compress
            old_messages = conversation.messages[: -MAX_CONVERSATION_HISTORY]

            # Format for LLM
            formatted = [msg.to_dict() for msg in old_messages]

            # Summarize using LLM
            summary = self.llm.summarize_conversation(formatted)

            # Store summary
            conversation.context_summary = summary

            logger.info(
                "conversation_compressed",
                conversation_id=conversation_id,
                summary_length=len(summary),
            )

        except Exception as e:
            logger.error("compression_failed", error=str(e))

    def track_entities(
        self,
        conversation_id: str,
        entities: Dict[str, str],
    ) -> None:
        """
        Track entities mentioned in conversation.

        Args:
            conversation_id: Conversation identifier
            entities: Entity dictionary
        """
        conversation = self.get_or_create_conversation(conversation_id)
        conversation.update_entity_tracker(entities)

        logger.debug("entities_tracked", count=len(entities))

    def clear_conversation(self, conversation_id: str) -> None:
        """
        Clear a conversation from memory.

        Args:
            conversation_id: Conversation identifier
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info("conversation_cleared", conversation_id=conversation_id)

    def get_conversation_summary(self, conversation_id: str) -> str:
        """
        Get a summary of the conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            str: Conversation summary
        """
        conversation = self.get_or_create_conversation(conversation_id)

        if conversation.context_summary:
            return conversation.context_summary

        # Generate summary on the fly
        if conversation.message_count > 0:
            try:
                messages = conversation.format_for_llm()
                summary = self.llm.summarize_conversation(messages)
                return summary
            except Exception as e:
                logger.error("summary_generation_failed", error=str(e))
                return "Conversation in progress."

        return "No conversation yet."
