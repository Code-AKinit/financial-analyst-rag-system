"""
Prompt templates for LLM interactions.

Defines system prompts and templates for various LLM tasks.
"""


class PromptTemplates:
    """
    Collection of prompt templates for financial analyst chatbot.
    """

    FINANCIAL_ANALYST_SYSTEM_PROMPT = """You are an expert financial analyst assistant with deep knowledge of financial documents, accounting principles, and business analysis.

Your role is to:
1. Answer questions based ONLY on the provided context from financial documents
2. Provide accurate, well-reasoned analysis with proper citations
3. Acknowledge uncertainty when information is insufficient
4. Use clear, professional language appropriate for financial analysis

Guidelines:
- Always cite your sources using [1], [2], etc. notation
- If the context doesn't contain enough information, say "I don't have sufficient information to answer that"
- When analyzing trends or comparisons, be specific with numbers and time periods
- Distinguish between facts from documents and your analytical interpretations
- For follow-up questions, use the conversation history to understand context

Remember: You are a financial analyst, not a general chatbot. Stay focused on financial analysis."""

    QUERY_UNDERSTANDING_PROMPT = """Analyze this financial query and extract key information.

Query: {query}

Extract and return in JSON format:
{{
    "intent": "factual|analytical|computational|conversational",
    "entities": ["list of specific entities mentioned like company names, metrics, etc."],
    "fiscal_periods": ["Q1", "Q2", "Q3", "Q4", "FY"],
    "document_types": ["annual_report", "quarterly_earnings", "investor_data", "stock_prices"],
    "keywords": ["key financial terms"],
    "requires_calculation": true/false,
    "requires_comparison": true/false
}}

Focus on financial context. Be precise."""

    QUERY_REWRITE_PROMPT = """Given this conversation history, rewrite the current query to be self-contained and clear.

Conversation History:
{conversation_history}

Current Query: {current_query}

Rewrite the query to:
1. Resolve all references (it, they, that, previous quarter, etc.)
2. Include necessary context from history
3. Be clear and specific
4. Maintain the user's intent

Return ONLY the rewritten query, nothing else."""

    ANSWER_GENERATION_PROMPT = """Answer the following financial question based ONLY on the provided context.

Question: {query}

Context from Financial Documents:
{context}

Instructions:
1. Provide a clear, accurate answer based on the context
2. Use specific numbers, dates, and facts from the context
3. Cite your sources using [1], [2], [3] format matching the context chunks
4. If information is insufficient, clearly state what's missing
5. For analytical questions, provide reasoned analysis
6. Use professional financial language

{conversation_context}

Answer:"""

    CONTEXT_SYNTHESIS_PROMPT = """You are given multiple chunks from financial documents. Synthesize them into a coherent context.

Chunks:
{chunks}

Tasks:
1. Remove duplicate information
2. Organize information logically
3. Preserve all specific numbers, dates, and facts
4. Maintain source attribution
5. Highlight contradictions if any

Return a clear, organized synthesis that preserves all important details."""

    CITATION_EXTRACTION_PROMPT = """Given a response and source chunks, identify which chunks support which claims.

Response:
{response}

Source Chunks:
{chunks}

Return JSON mapping each claim to supporting chunk IDs:
{{
    "claim_1": ["chunk_id_1", "chunk_id_2"],
    "claim_2": ["chunk_id_3"]
}}"""

    MULTI_QUERY_GENERATION_PROMPT = """Generate 3 different phrasings of this financial query to improve retrieval.

Original Query: {query}

Generate variations that:
1. Use different financial terminology
2. Focus on different aspects (causes, effects, comparisons)
3. Are more specific or more general

Return as JSON array:
["query_1", "query_2", "query_3"]"""

    RELEVANCE_SCORING_PROMPT = """Rate how relevant this passage is to the query on a scale of 0-10.

Query: {query}

Passage:
{passage}

Consider:
- Direct relevance to the question
- Specificity of information
- Presence of numbers/facts vs general statements

Return only the score (0-10)."""

    ENTITY_EXTRACTION_PROMPT = """Extract financial entities from this text.

Text: {text}

Extract:
{{
    "metrics": ["revenue", "profit", "expenses", etc.],
    "amounts": ["$10M", "20%", etc.],
    "time_periods": ["Q1 2024", "FY 2023", etc.],
    "departments": ["sales", "operations", etc.],
    "products": ["product names if any"]
}}

Return JSON only."""

    CONVERSATION_SUMMARY_PROMPT = """Summarize this conversation history concisely, preserving key facts and context.

Conversation:
{conversation}

Create a brief summary (2-3 sentences) that captures:
1. Main topics discussed
2. Key facts established
3. Important entities mentioned

Summary:"""

    INTENT_CLASSIFICATION_PROMPT = """Classify the intent of this financial query.

Query: {query}

Intents:
- factual: Simple fact retrieval (What was X? When did Y happen?)
- analytical: Analysis required (Why did X change? How do Y and Z compare?)
- computational: Calculation needed (What's the growth rate? Calculate X)
- conversational: Follow-up or clarification (What about...? Tell me more)

Return only the intent name."""

    STRUCTURED_DATA_EXTRACTION_PROMPT = """Extract structured data from the context for this query.

Query: {query}

Context:
{context}

Extract relevant data in this JSON structure:
{{
    "metrics": {{
        "metric_name": {{"value": "amount", "period": "time", "source": "doc"}}
    }},
    "comparisons": [
        {{"item1": "value1", "item2": "value2", "metric": "name"}}
    ],
    "trends": [
        {{"metric": "name", "direction": "up/down", "magnitude": "percentage"}}
    ]
}}

Be precise with numbers and sources."""

    @staticmethod
    def format_conversation_history(messages: list) -> str:
        """
        Format conversation history for prompts.

        Args:
            messages: List of message dictionaries

        Returns:
            str: Formatted conversation history
        """
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted.append(f"{role.upper()}: {content}")

        return "\n".join(formatted)

    @staticmethod
    def format_chunks_with_sources(chunks: list) -> str:
        """
        Format document chunks with source attribution.

        Args:
            chunks: List of DocumentChunk objects

        Returns:
            str: Formatted chunks with sources
        """
        formatted = []

        for i, chunk in enumerate(chunks, 1):
            source_info = f"[{i}] Source: {chunk.metadata.document_name}"

            if chunk.metadata.section:
                source_info += f", Section: {chunk.metadata.section}"
            if chunk.metadata.page_number:
                source_info += f", Page: {chunk.metadata.page_number}"

            formatted.append(f"{source_info}\n{chunk.text}\n")

        return "\n---\n".join(formatted)
