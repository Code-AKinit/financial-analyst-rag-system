# AI Financial Analyst Chatbot

> **Production-grade AI Financial Analyst with Advanced RAG Capabilities**

An intelligent conversational AI system that understands financial documents, answers cross-document questions, maintains context across conversations, and generates professional reports in multiple formats.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Key Features

### Intelligence & Reasoning
- **Advanced RAG Pipeline**: Hybrid retrieval (vector + keyword), semantic reranking, context synthesis
- **Cross-Document Understanding**: Answers questions spanning multiple financial documents
- **Conversational Memory**: Maintains context across follow-up questions with entity tracking
- **Source Citation**: Every answer includes accurate citations to source documents

### Intelligent Output Generation
- **Markdown Responses**: Quick, concise answers for simple queries
- **Professional PDF Reports**: Analytical summaries, executive reports, trend analysis
- **Excel Exports**: Tabular data, financial comparisons, structured metrics
- **Smart Format Selection**: System automatically chooses the best output format

### Production-Grade Engineering
- **Clean Architecture**: Clear separation of concerns (Presentation → Application → Domain → Infrastructure)
- **SOLID Principles**: Modular, testable, maintainable codebase
- **Type-Safe**: Full type hints with Pydantic validation
- **Structured Logging**: JSON logging with contextual information
- **Security First**: Input validation, prompt injection defense, safe file handling

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                       │
│                    (Streamlit UI / CLI)                      │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                   APPLICATION LAYER                          │
│  • Chatbot Orchestrator    • Conversation Manager           │
│  • Output Format Decider   • Use Cases                      │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                      DOMAIN LAYER                            │
│  • Query Understanding     • Context Synthesis               │
│  • Financial Reasoning     • Citation Service                │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                         │
│  • Gemini LLM Gateway      • ChromaDB Vector Store           │
│  • Document Processors     • Report Generators               │
└─────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

- **Testability**: Each layer can be tested independently
- **Maintainability**: Changes in infrastructure don't affect business logic
- **Extensibility**: Easy to swap LLM providers, vector DBs, or UI frameworks
- **Clarity**: Clear boundaries and responsibilities

---

## 📋 Supported Documents

The system ingests and understands:

1. **Annual Report** (PDF)
2. **Quarterly Earnings Reports** (Q1-Q4 PDFs)
3. **Investor Data** (Excel spreadsheet)
4. **Stock Prices** (CSV time series)

Questions can span multiple documents simultaneously.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Google Gemini API key ([Get one free](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd ai-financial-analyst
```

2. **Create virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your-actual-api-key-here
```

**⚠️ Important Note on Embeddings:**

The sample outputs in this repository were generated using **mock embeddings** due to Gemini API rate limits during development. The system successfully ingested all 1,804 document chunks but hit the free tier quota.

**If you have full Gemini API access:**
- Edit `.env` and ensure `EMBEDDING_PROVIDER=gemini` (default)
- Your `GEMINI_API_KEY` must have sufficient quota
- Re-run ingestion if needed: `python scripts/ingest_documents.py`

**Alternative Embedding Providers:**
```bash
# In .env file, choose one:
EMBEDDING_PROVIDER=gemini    # Google Gemini embeddings (requires API quota)
EMBEDDING_PROVIDER=openai    # OpenAI embeddings (requires credits)
EMBEDDING_PROVIDER=local     # Local sentence-transformers (no API needed)
EMBEDDING_PROVIDER=mock      # Mock embeddings for testing (used in samples)
```

For production use with no API limits, we recommend `local` (sentence-transformers) which runs completely offline.

5. **Place your documents**
```bash
# Put your financial documents in data/raw/
# - annual_report.pdf
# - q1_earnings.pdf, q2_earnings.pdf, etc.
# - investor_data.xlsx
# - stock_prices.csv
```

6. **Ingest documents**
```bash
python scripts/ingest_documents.py
```

7. **Run the application**
```bash
streamlit run src/presentation/streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

---

## 💡 Example Queries

### Simple Factual Questions
```
What was the total revenue in Q1 2024?
```

### Analytical Questions
```
Compare the profit margins across all quarters and explain the trend.
```

### Cross-Document Analysis
```
How did the stock price correlate with revenue growth in Q3?
```

### Follow-up Questions
```
User: What was the Q1 revenue?
Assistant: Q1 2024 revenue was $10M...
User: How does that compare to Q2?  ← System understands context
```

---

## 📊 Output Formats

### Markdown (Default)
- Quick answers
- Bullet points
- Simple comparisons

### PDF Reports
Generated automatically for:
- Analytical summaries
- Executive reports
- Trend analysis
- Multi-section deep dives

### Excel Spreadsheets
Generated automatically for:
- Financial metrics tables
- Multi-quarter comparisons
- Stock price data
- Structured calculations

**The system decides the format intelligently based on query type and response content.**

---

## 🛠️ Technology Stack

| Component | Technology | Reason |
|-----------|------------|--------|
| **LLM** | Google Gemini 1.5 Pro/Flash | Free tier, 1M context, excellent reasoning |
| **Vector DB** | ChromaDB | Lightweight, local, production-ready |
| **Embeddings** | Gemini Embeddings | Free, high quality, 768 dimensions |
| **PDF Processing** | PyMuPDF (fitz) | Fast, reliable, battle-tested |
| **PDF Generation** | ReportLab | Industry standard, full control |
| **Excel** | openpyxl | Rich formatting, multiple sheets |
| **UI** | Streamlit | Rapid development, AI-friendly |
| **Config** | Pydantic | Type-safe, validation |
| **Logging** | structlog | Structured JSON logs |

---

## 🧪 Testing

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=src --cov-report=html
```

### Run specific test suite
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/
```

---

## 📁 Project Structure

```
ai-financial-analyst/
├── src/
│   ├── presentation/          # UI layer (Streamlit)
│   ├── application/           # Application logic & orchestration
│   ├── domain/                # Business logic (models, services, interfaces)
│   ├── infrastructure/        # External adapters (LLM, DB, processors)
│   ├── config/                # Configuration management
│   └── utils/                 # Utilities and helpers
├── tests/
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── fixtures/              # Test fixtures and data
├── data/
│   ├── raw/                   # Original documents
│   ├── processed/             # Processed chunks
│   └── vector_store/          # ChromaDB persistence
├── outputs/
│   ├── reports/               # Generated PDF reports
│   ├── excel/                 # Generated Excel files
│   └── logs/                  # Application logs
├── docs/                      # Additional documentation
├── scripts/                   # Utility scripts
├── requirements.txt           # Python dependencies
├── .env.example              # Example environment variables
└── README.md                 # This file
```

---

## 🔒 Security Features

- ✅ Environment variable protection for API keys
- ✅ Input validation and sanitization
- ✅ Prompt injection defense
- ✅ Path traversal prevention
- ✅ File type and size validation
- ✅ Output sanitization
- ✅ Safe temporary file handling
- ✅ Structured error messages (no sensitive data leakage)

---

## 🎨 Design Decisions

### Why ChromaDB over FAISS?
- **Local deployment** required for assignment
- **Metadata filtering** essential for document type/fiscal period filtering
- **Built-in persistence** without manual management
- **Production-ready** with minimal setup

### Why Gemini over OpenAI?
- **Free tier** sufficient for assignment
- **1M context window** can handle entire documents
- **Structured output** support for reliable parsing
- **Excellent reasoning** for financial analysis

### Why Semantic Chunking?
- **Preserve structure** in financial documents
- **Better retrieval** quality than fixed-size chunks
- **Maintain context** at section boundaries

### Why Hybrid Retrieval?
- **Vector search** captures semantic similarity
- **Keyword search** catches exact term matches
- **Combined** provides best of both worlds

---

## 🚧 Known Limitations

- **Single company focus**: Designed for one company's documents
- **English only**: No multi-language support
- **Local deployment**: Not optimized for cloud scale
- **Synchronous processing**: No async/parallel document ingestion
- **Limited chart support**: Text-based analysis only (no chart generation)

---

## 🔮 Future Enhancements

### Short-term
- [ ] Multi-modal support for charts/graphs in PDFs
- [ ] Query suggestions and auto-complete
- [ ] Feedback loop for improving responses
- [ ] Export full conversation history
- [ ] Side-by-side document comparison mode

### Long-term
- [ ] Real-time stock price integration
- [ ] Multi-company support
- [ ] Predictive analytics and forecasting
- [ ] Collaborative mode (multiple users)
- [ ] REST API for external integrations

---

## 📖 Additional Documentation

- [PLAN.md](PLAN.md) - Detailed implementation plan and architecture
- [REFLECTION.md](REFLECTION.md) - Post-implementation reflection and learnings
- [docs/architecture.md](docs/architecture.md) - Detailed architecture documentation
- [docs/development_guide.md](docs/development_guide.md) - Development guidelines

---

## 🤝 Contributing

This is an assignment project, but feedback and suggestions are welcome!

1. Ensure all tests pass
2. Follow existing code style (Black formatter, pylint)
3. Add tests for new features
4. Update documentation

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

- **Google Gemini** for excellent free-tier LLM access
- **ChromaDB** for lightweight vector storage
- **Streamlit** for rapid UI development
- **Anthropic Claude** for architectural guidance

---

## 📞 Support

For issues or questions:
- Open an issue on GitHub
- Check existing documentation
- Review example queries

---

**Built with ❤️ using Clean Architecture, SOLID principles, and modern AI engineering practices.**
