"""
Domain models for conversations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from src.utils.constants import ConversationRole


@dataclass
class Message:
    """
    A single message in a conversation.

    Attributes:
        role: Role of the message sender
        content: Message content
        timestamp: When message was created
        metadata: Additional message metadata
    """

    role: ConversationRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Validate message after initialization."""
        if not self.content or not self.content.strip():
            raise ValueError("Message content cannot be empty")

    def to_dict(self) -> Dict[str, str]:
        """
        Convert message to dictionary format.

        Returns:
            Dict: Message as dictionary
        """
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Conversation:
    """
    Represents a conversation between user and assistant.

    Attributes:
        conversation_id: Unique conversation identifier
        messages: List of messages in conversation
        created_at: When conversation started
        updated_at: When conversation was last updated
        entity_tracker: Entities mentioned in conversation
        context_summary: Compressed summary of old messages
    """

    conversation_id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    messages: List[Message] = field(default_factory=list)
    entity_tracker: Dict[str, str] = field(default_factory=dict)
    context_summary: Optional[str] = None

    def add_message(self, role: ConversationRole, content: str) -> Message:
        """
        Add a message to the conversation.

        Args:
            role: Role of the message sender
            content: Message content

        Returns:
            Message: The created message
        """
        message = Message(role=role, content=content)
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message

    def get_recent_messages(self, count: int = 10) -> List[Message]:
        """
        Get the most recent messages.

        Args:
            count: Number of recent messages to return

        Returns:
            List[Message]: Recent messages
        """
        return self.messages[-count:] if len(self.messages) > count else self.messages

    def get_context_window(self, max_messages: int = 10) -> List[Message]:
        """
        Get context window for current query.

        Includes context summary if available, plus recent messages.

        Args:
            max_messages: Maximum number of recent messages

        Returns:
            List[Message]: Messages for context
        """
        context_messages = []

        # Add context summary as system message if available
        if self.context_summary:
            context_messages.append(
                Message(
                    role=ConversationRole.SYSTEM,
                    content=f"Previous conversation summary: {self.context_summary}",
                )
            )

        # Add recent messages
        recent = self.get_recent_messages(max_messages)
        context_messages.extend(recent)

        return context_messages

    def format_for_llm(self, max_messages: int = 10) -> List[Dict[str, str]]:
        """
        Format conversation for LLM API.

        Args:
            max_messages: Maximum number of recent messages

        Returns:
            List[Dict]: Formatted messages for LLM
        """
        context_window = self.get_context_window(max_messages)
        return [msg.to_dict() for msg in context_window]

    def update_entity_tracker(self, entities: Dict[str, str]) -> None:
        """
        Update tracked entities from a message.

        Args:
            entities: Dictionary of entity type to value
        """
        self.entity_tracker.update(entities)
        self.updated_at = datetime.now()

    @property
    def message_count(self) -> int:
        """Get total number of messages."""
        return len(self.messages)

    @property
    def last_message(self) -> Optional[Message]:
        """Get the last message in conversation."""
        return self.messages[-1] if self.messages else None
