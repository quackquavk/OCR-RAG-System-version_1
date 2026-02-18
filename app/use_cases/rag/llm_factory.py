"""
LLM Factory for RAG Service.
Creates the appropriate LLM and rate limiter based on environment configuration.
"""

import os
import logging
from typing import Tuple, Any

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

from app.infrastructure.rate_limiter import get_rate_limiter, APIProvider
from app.core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory to create LLM + RateLimiter pair from environment config."""

    @staticmethod
    def create() -> Tuple[Any, Any]:
        """
        Build an LLM instance and its matching rate limiter.

        Reads from environment variables:
            RAG_LLM_PROVIDER  – "groq" or "gemini"  (default: "groq")
            RAG_LLM_MODEL     – model name           (default: "llama-3.3-70b-versatile")

        Returns:
            (llm, rate_limiter)
        """
        provider = os.getenv("RAG_LLM_PROVIDER", "groq").lower()
        model_name = os.getenv("RAG_LLM_MODEL", "llama-3.3-70b-versatile")

        logger.info(f"LLMFactory: creating LLM  provider={provider}  model={model_name}")

        if provider == "groq":
            return LLMFactory._create_groq(model_name)
        elif provider in ("gemini", "google"):
            return LLMFactory._create_gemini(model_name)
        else:
            raise ExternalServiceError(
                f"Unsupported RAG_LLM_PROVIDER: '{provider}'. Use 'groq' or 'gemini'.",
                service_name="LLMFactory",
            )

    # ------------------------------------------------------------------ #
    #  Groq
    # ------------------------------------------------------------------ #
    @staticmethod
    def _create_groq(model_name: str) -> Tuple[Any, Any]:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ExternalServiceError(
                "GROQ_API_KEY is not set", service_name="LLMFactory"
            )

        limiter = get_rate_limiter(provider=APIProvider.GROQ, name="rag_groq")
        llm = ChatGroq(
            model=model_name,
            groq_api_key=api_key,
            temperature=0,
            timeout=30,
            max_retries=2,
        )
        logger.info(f"LLMFactory: Groq LLM ready  model={model_name}")
        return llm, limiter

    # ------------------------------------------------------------------ #
    #  Gemini
    # ------------------------------------------------------------------ #
    @staticmethod
    def _create_gemini(model_name: str) -> Tuple[Any, Any]:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ExternalServiceError(
                "GEMINI_API_KEY / GOOGLE_API_KEY is not set",
                service_name="LLMFactory",
            )

        limiter = get_rate_limiter(
            provider=APIProvider.GEMINI_FREE, name="rag_gemini"
        )
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0,
            timeout=30,
            max_retries=2,
        )
        logger.info(f"LLMFactory: Gemini LLM ready  model={model_name}")
        return llm, limiter
