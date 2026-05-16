"""
Query understanding service.

Analyzes and enhances user queries for better retrieval and reasoning.
"""

from typing import Dict, List

from src.config.logging_config import get_logger
from src.domain.interfaces.llm_gateway import LLMGateway
from src.domain.models.query import Query, QueryMetadata
from src.utils.constants import FiscalPeriod, QueryIntent
from src.utils.helpers import extract_fiscal_period_from_text

logger = get_logger(__name__)


class QueryUnderstandingService:
    """
    Service for understanding and enhancing user queries.

    Extracts intent, entities, and metadata to improve retrieval.
    """

    def __init__(self, llm_gateway: LLMGateway):
        """
        Initialize query understanding service.

        Args:
            llm_gateway: LLM gateway for query analysis
        """
        self.llm = llm_gateway
        logger.info("query_understanding_service_initialized")

    def analyze_query(self, query: Query) -> Query:
        """
        Analyze query and enhance with metadata.

        Args:
            query: Query to analyze

        Returns:
            Query: Enhanced query with metadata
        """
        logger.info("analyzing_query", query=query.text[:100])

        try:
            # Classify intent
            intent = self._classify_intent(query)
            query.intent = QueryIntent(intent)

            # Extract metadata
            metadata = self._extract_metadata(query)
            query.metadata = metadata

            logger.info(
                "query_analyzed",
                intent=query.intent.value,
                entities=len(metadata.entities),
            )

            return query

        except Exception as e:
            logger.error("query_analysis_failed", error=str(e))
            # Return query as-is on error
            return query

    def _classify_intent(self, query: Query) -> str:
        """
        Classify query intent.

        Args:
            query: Query to classify

        Returns:
            str: Intent classification
        """
        try:
            # Use LLM for intent classification
            intent = self.llm.classify_intent(query)
            return intent

        except Exception as e:
            logger.warning("llm_intent_classification_failed", error=str(e))
            # Fallback to rule-based classification
            return self._rule_based_intent(query.text)

    def _rule_based_intent(self, query_text: str) -> str:
        """
        Rule-based intent classification as fallback.

        Args:
            query_text: Query text

        Returns:
            str: Intent
        """
        text_lower = query_text.lower()

        # Computational indicators
        if any(word in text_lower for word in ["calculate", "compute", "growth rate", "percentage"]):
            return "computational"

        # Analytical indicators
        if any(
            word in text_lower
            for word in [
                "why",
                "how",
                "analyze",
                "compare",
                "trend",
                "correlation",
                "impact",
                "reason",
            ]
        ):
            return "analytical"

        # Conversational indicators
        if any(
            word in text_lower for word in ["more", "also", "additionally", "what about", "tell me"]
        ):
            return "conversational"

        # Default to factual
        return "factual"

    def _extract_metadata(self, query: Query) -> QueryMetadata:
        """
        Extract metadata from query.

        Args:
            query: Query to analyze

        Returns:
            QueryMetadata: Extracted metadata
        """
        text = query.text

        # Extract fiscal periods
        fiscal_periods = self._extract_fiscal_periods(text)

        # Extract entities using LLM
        entities_dict = {}
        try:
            entities_dict = self.llm.extract_entities(text)
        except Exception as e:
            logger.warning("llm_entity_extraction_failed", error=str(e))

        # Flatten entities
        entities = []
        for entity_list in entities_dict.values():
            if isinstance(entity_list, list):
                entities.extend(entity_list)

        # Extract keywords
        keywords = self._extract_financial_keywords(text)

        metadata = QueryMetadata(
            entities=entities,
            fiscal_periods=fiscal_periods,
            keywords=keywords,
        )

        return metadata

    def _extract_fiscal_periods(self, text: str) -> List[FiscalPeriod]:
        """
        Extract fiscal period mentions from text.

        Args:
            text: Text to search

        Returns:
            List[FiscalPeriod]: Found fiscal periods
        """
        periods = []

        text_lower = text.lower()

        # Check for specific quarters
        if "q1" in text_lower or "first quarter" in text_lower:
            periods.append(FiscalPeriod.Q1)
        if "q2" in text_lower or "second quarter" in text_lower:
            periods.append(FiscalPeriod.Q2)
        if "q3" in text_lower or "third quarter" in text_lower:
            periods.append(FiscalPeriod.Q3)
        if "q4" in text_lower or "fourth quarter" in text_lower:
            periods.append(FiscalPeriod.Q4)

        # Check for full year
        if any(term in text_lower for term in ["annual", "fiscal year", "fy", "full year"]):
            periods.append(FiscalPeriod.FY)

        return periods

    def _extract_financial_keywords(self, text: str) -> List[str]:
        """
        Extract financial keywords from text.

        Args:
            text: Text to analyze

        Returns:
            List[str]: Financial keywords
        """
        keywords = []

        # Financial term dictionary
        financial_terms = {
            "revenue": ["revenue", "sales", "income"],
            "profit": ["profit", "earnings", "net income"],
            "expenses": ["expenses", "costs", "expenditure"],
            "margin": ["margin", "profit margin", "operating margin"],
            "growth": ["growth", "increase", "expansion"],
            "decline": ["decline", "decrease", "reduction"],
            "assets": ["assets", "balance sheet"],
            "liabilities": ["liabilities", "debt"],
            "cash_flow": ["cash flow", "operating cash"],
            "equity": ["equity", "shareholders"],
            "stock": ["stock", "share price", "trading"],
        }

        text_lower = text.lower()

        for category, terms in financial_terms.items():
            if any(term in text_lower for term in terms):
                keywords.append(category)

        return keywords
