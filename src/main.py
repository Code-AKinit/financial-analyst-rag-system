"""
Main application entry point.

Can be used to run the chatbot via CLI or as a module.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.application.chatbot_orchestrator import ChatbotOrchestrator
from src.config.logging_config import configure_logging, get_logger

# Configure logging
configure_logging()
logger = get_logger(__name__)


def main():
    """
    Main entry point for CLI mode.
    """
    print("=" * 60)
    print("📊 AI Financial Analyst Chatbot")
    print("=" * 60)
    print()

    try:
        # Initialize orchestrator
        print("Initializing system...")
        orchestrator = ChatbotOrchestrator()

        # Check system status
        status = orchestrator.check_system_status()

        if status["status"] != "healthy":
            print(f"❌ System Error: {status.get('error', 'Unknown')}")
            return

        print(f"✅ System ready!")
        print(f"📚 Indexed documents: {status['vector_store']['document_count']}")
        print()

        # CLI interaction loop
        conversation_id = "cli_session"

        print("Type 'exit' or 'quit' to end the conversation.")
        print("Type 'clear' to start a new conversation.")
        print()

        while True:
            # Get user input
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nGoodbye!")
                break

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ["exit", "quit"]:
                print("\nGoodbye!")
                break

            if user_input.lower() == "clear":
                orchestrator.clear_conversation(conversation_id)
                print("\n✨ Conversation cleared!\n")
                continue

            # Process query
            try:
                print("\n🤔 Thinking...\n")

                response = orchestrator.answer_query(
                    query_text=user_input,
                    conversation_id=conversation_id,
                )

                # Display response
                print(f"Assistant: {response.get_full_response()}")
                print()

                # Show metadata
                print(f"⏱️  {response.metadata.processing_time_ms:.0f}ms | "
                      f"📚 {response.metadata.retrieved_chunks_count} sources | "
                      f"💬 {response.output_format.value}")
                print()

            except Exception as e:
                print(f"\n❌ Error: {e}\n")
                logger.error("cli_query_failed", error=str(e))

    except KeyboardInterrupt:
        print("\n\nGoodbye!")

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.error("main_failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
