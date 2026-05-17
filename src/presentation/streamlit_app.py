"""
Streamlit UI for AI Financial Analyst Chatbot.

Interactive web interface for the chatbot.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

from src.application.chatbot_orchestrator import ChatbotOrchestrator
from src.config.logging_config import configure_logging
from src.infrastructure.report_generation.excel_generator import ExcelReportGenerator
from src.infrastructure.report_generation.pdf_generator import PDFReportGenerator
from src.utils.constants import OutputFormat
from src.utils.exceptions import FinancialAnalystError

# Configure logging
configure_logging()

# Page config
st.set_page_config(
    page_title="AI Financial Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a365d;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #4a5568;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e6f3ff;
        border-left: 4px solid #4299e1;
    }
    .assistant-message {
        background-color: #f7fafc;
        border-left: 4px solid #48bb78;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Initialize session state
if "orchestrator" not in st.session_state:
    try:
        st.session_state.orchestrator = ChatbotOrchestrator()
        st.session_state.pdf_generator = PDFReportGenerator()
        st.session_state.excel_generator = ExcelReportGenerator()
    except Exception as e:
        st.error(f"Failed to initialize system: {e}")
        st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = "session_001"


def main():
    """Main application entry point."""

    # Header
    st.markdown('<div class="main-header">📊 AI Financial Analyst</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Ask questions about your financial documents</div>',
        unsafe_allow_html=True,
    )

    # Sidebar
    with st.sidebar:
        st.header("Settings")

        # System status
        with st.expander("📈 System Status", expanded=False):
            try:
                status = st.session_state.orchestrator.check_system_status()

                if status["status"] == "healthy":
                    st.success("✅ System Healthy")

                    st.metric(
                        "Indexed Documents",
                        status["vector_store"]["document_count"],
                    )

                    st.info(f"Model: {status['settings']['model']}")
                else:
                    st.error(f"❌ System Error: {status.get('error', 'Unknown')}")

            except Exception as e:
                st.error(f"Status check failed: {e}")

        # Example queries
        st.header("💡 Example Queries")

        examples = [
            "What was the total revenue in Q1 2024?",
            "Compare profit margins across all quarters",
            "How did stock price correlate with revenue?",
            "Analyze the revenue trend over the year",
            "Show me a breakdown of all quarterly earnings",
        ]

        for example in examples:
            if st.button(example, key=f"example_{example[:20]}"):
                st.session_state.current_query = example

        st.divider()

        # Clear conversation
        if st.button("🗑️ Clear Conversation"):
            st.session_state.messages = []
            st.session_state.orchestrator.clear_conversation(
                st.session_state.conversation_id
            )
            st.rerun()

        # About
        with st.expander("ℹ️ About"):
            st.markdown(
                """
                **AI Financial Analyst**

                Built with:
                - Google Gemini LLM
                - ChromaDB Vector Store
                - Advanced RAG Pipeline
                - Conversational Memory

                Features:
                - Cross-document Q&A
                - Follow-up questions
                - Source citations
                - PDF/Excel reports
                """
            )

    # Main chat area
    chat_container = st.container()

    with chat_container:
        # Display conversation history
        for message in st.session_state.messages:
            role = message["role"]
            content = message["content"]

            if role == "user":
                st.markdown(
                    f'<div class="chat-message user-message"><b>You:</b><br>{content}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="chat-message assistant-message"><b>Assistant:</b><br>{content}</div>',
                    unsafe_allow_html=True,
                )

                # Show download buttons if available
                if "response_obj" in message:
                    response_obj = message["response_obj"]

                    col1, col2, col3 = st.columns([1, 1, 4])

                    # PDF download
                    if response_obj.output_format in [OutputFormat.PDF, OutputFormat.MARKDOWN]:
                        with col1:
                            if st.button("📄 Download PDF", key=f"pdf_{message['timestamp']}"):
                                try:
                                    pdf_bytes = st.session_state.pdf_generator.generate_pdf_report(
                                        response_obj,
                                        message.get("query", ""),
                                        {},
                                    )

                                    st.download_button(
                                        label="💾 Save PDF",
                                        data=pdf_bytes,
                                        file_name=f"report_{message['timestamp']}.pdf",
                                        mime="application/pdf",
                                    )

                                except Exception as e:
                                    st.error(f"PDF generation failed: {e}")

                    # Show metadata
                    with st.expander("📊 Response Details"):
                        # Handle output_format - it might be enum or string
                        output_fmt = response_obj.output_format
                        if hasattr(output_fmt, 'value'):
                            output_fmt_str = output_fmt.value
                        else:
                            output_fmt_str = str(output_fmt)

                        st.json({
                            "Processing Time": f"{response_obj.metadata.processing_time_ms:.0f}ms",
                            "Sources Used": response_obj.metadata.retrieved_chunks_count,
                            "Model": response_obj.metadata.model_used,
                            "Output Format": output_fmt_str,
                            "Citations": len(response_obj.citations),
                        })

    # Chat input
    st.divider()

    # Use session state for query if set from example buttons
    query_text = st.session_state.get("current_query", "")

    # Text input
    user_input = st.chat_input(
        "Ask a question about your financial documents...",
        key="chat_input",
    )

    # Use either direct input or example query
    if user_input or query_text:
        query = user_input if user_input else query_text

        # Clear current_query from session state
        if "current_query" in st.session_state:
            del st.session_state.current_query

        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": query,
            "timestamp": str(hash(query)),
        })

        # Show processing
        with st.spinner("🤔 Thinking..."):
            try:
                # Get response
                response = st.session_state.orchestrator.answer_query(
                    query_text=query,
                    conversation_id=st.session_state.conversation_id,
                )

                # Format response with citations
                response_text = response.get_full_response()

                # Add assistant message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "timestamp": response.response_id,
                    "response_obj": response,
                    "query": query,
                })

                st.rerun()

            except FinancialAnalystError as e:
                st.error(f"❌ Error: {e}")

            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")
                st.exception(e)


if __name__ == "__main__":
    main()
