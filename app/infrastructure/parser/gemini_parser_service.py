"""
Handles document parsing using Large Language Models (Gemini/Groq).
Includes optimized prompting, JSON extraction, and robust error handling.
Refactored for SRP, high cohesion, and loose coupling.
"""

import asyncio
import json
import re
import os
import logging
from typing import Optional, Dict, Any, Union, Tuple
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel

from app.infrastructure.rate_limiter import get_rate_limiter, APIProvider
from app.core.exceptions import ConfigurationError, ExternalServiceError
from app.infrastructure.firebase.user_repository import FirestoreUserRepository
from app.infrastructure.encryption_service import FernetEncryptionService

logger = logging.getLogger(__name__)
load_dotenv()

class ParserPromptManager:
    """Manages document analysis prompts."""
    
    DOCUMENT_PARSE_PROMPT = """
You are a document analysis assistant. Analyze the provided document text and extract all relevant information.

STEP 1: Classify the document into one of these categories:
- invoice
- receipt
- bank statement
- bill
- other

STEP 2: Extract all relevant data based on the document type.

You MUST return a JSON object with these REQUIRED top-level fields:

1. "document_type": The classified category (invoice, receipt, bank statement, bill, or other)
2. "total_amount": The final total amount (number). Look for: total, grand total, amount due, balance due.
3. "date": The transaction/invoice/receipt date in YYYY-MM-DD format.

4. For INVOICES, include:
   - "customer_name": Name of customer/client (REQUIRED)
   - "vendor_name": Name of issuing company (REQUIRED)
   - "line_items": List of items (HIGHLY RECOMMENDED). Each item:
       - "description": Item description
       - "quantity": Quantity (number)
       - "price": Unit price (number)
       - "total": Line total (number)

5. For RECEIPTS, include:
   - "vendor_name": Name of merchant (REQUIRED)
   - "items": List of purchased items.

6. For BANK STATEMENTS, include:
   - "account_number": Bank account number (REQUIRED)
   - "transactions": List of transaction objects:
       - "date": YYYY-MM-DD
       - "description": Full description
       - "debit": Amount (number, 0 if missing)
       - "credit": Amount (number, 0 if missing)

Output ONLY the raw JSON object. Do not include markdown formatting or explanations.
"""

    @classmethod
    def get_parse_template(cls) -> ChatPromptTemplate:
        """Returns the formatted prompt template."""
        return ChatPromptTemplate.from_messages([
            ("system", cls.DOCUMENT_PARSE_PROMPT),
            ("human", "{context}")
        ])
    
class LLMModelFactory:
    """Factory for initializing LLM providers with associated rate limiters."""

    @staticmethod
    def create(model_name: str, timeout: float, api_key: Optional[str] = None) -> Tuple[BaseChatModel, Any]:
        """Creates the appropriate LLM instance based on model name."""
        model_name_lower = model_name.lower()
        if any(x in model_name_lower for x in ["llama", "mixtral"]):
            return LLMModelFactory._init_groq(model_name, timeout, api_key)
        return LLMModelFactory._init_gemini(model_name)

    @staticmethod
    def _init_groq(model_name: str, timeout: float, api_key: Optional[str] = None) -> Tuple[ChatGroq, Any]:
        if not api_key:
            api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            raise ConfigurationError("GROQ_API_KEY missing", config_key="GROQ_API_KEY")

        limiter = get_rate_limiter(provider=APIProvider.GROQ, name="groq_processing")
        model = ChatGroq(
            model=model_name,
            groq_api_key=api_key,
            temperature=0,
            timeout=timeout,
            max_retries=2
        )
        return model, limiter
    
    @staticmethod
    def _init_gemini(model_name: str) -> Tuple[ChatGoogleGenerativeAI, Any]:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ConfigurationError("GEMINI_API_KEY missing", config_key="GEMINI_API_KEY")
        
        limiter = get_rate_limiter(provider=APIProvider.GEMINI_FREE, name="gemini_processing")
        model = ChatGoogleGenerativeAI(
            model=model_name,  # Use "gemini-2.5-flash" when calling the service
            google_api_key=api_key,
            temperature=0,
            max_retries=2
        )   
        return model, limiter

 


class ParserOutputProcessor:
    """Handles extraction, normalization, and cleaning of LLM output."""

    @staticmethod
    def extract_json(output: str) -> Dict[str, Any]:
        """Robustly extracts JSON from raw LLM strings."""
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", output, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
        
        logger.warning(f"Failed to extract JSON from: {output[:100]}...")
        return {"error": "JSON extraction failed", "raw_output": output}

    @staticmethod
    def normalize_doc_type(doc_type: Optional[str]) -> str:
        """Standardizes document type naming."""
        if not doc_type: return "other"
        normalized = doc_type.strip().lower()
        return "bank statement" if normalized == "statement" else normalized

class GeminiParserService:
    """
    Orchestrator for document parsing.
    Delegates prompts, model creation, and processing to internal components.
    """

    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
    # def __init__(self, model_name: str = "gemini-2.5-flash"):  
        self.model_name = model_name
        self.api_timeout = 120.0
        
        try:
            self.llm, self.rate_limiter = LLMModelFactory.create(model_name, self.api_timeout)
            logger.info(f"Parser Service ready with {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Parser Service: {e}")
            raise ConfigurationError(f"LLM initialization failed: {e}")

    async def parse_async(self, text: str, image_url: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Main parsing entry point."""
        if not text or not text.strip():
            return {"error": "Empty input text", "document_type": "other"}

        try:
            # Determine LLM instance to use
            current_llm = self.llm
            current_limiter = self.rate_limiter
            
            # If user_id is provided and we are using a Groq model, try to fetch user's key
            if user_id and any(x in self.model_name.lower() for x in ["llama", "mixtral"]):
                try:
                    # Resolve key dynamically
                    repo = FirestoreUserRepository()
                    encryption = FernetEncryptionService()
                    
                    encrypted_key = await repo.get_groq_key(user_id)
                    if encrypted_key:
                        decrypted_key = encryption.decrypt(encrypted_key)
                        # Create specific instance for this request
                        current_llm, current_limiter = LLMModelFactory.create(
                            self.model_name, self.api_timeout, api_key=decrypted_key
                        )
                        logger.info(f"Using custom Groq key for user {user_id}")
                except Exception as e:
                    logger.warning(f"Failed to load user Groq key, falling back to system key: {e}")

            template = ParserPromptManager.get_parse_template()
            chain = template | current_llm
            
            logger.debug(f"Invoking LLM {self.model_name} with priority queue.")
            result = await asyncio.wait_for(
                current_limiter.execute_with_retry(
                    chain.ainvoke, {"context": text}, priority=10
                ),
                timeout=self.api_timeout
            )
            
            parsed = ParserOutputProcessor.extract_json(result.content)
            
            # Post-process
            parsed["document_type"] = ParserOutputProcessor.normalize_doc_type(parsed.get("document_type"))
            if image_url:
                parsed["image_url"] = str(image_url)

            return parsed

        except asyncio.TimeoutError:
            logger.error(f"Timeout for {self.model_name}")
            raise ExternalServiceError("LLM API timeout", service_name="LLM_Parser")
        except Exception as e:
            logger.error(f"Parsing cycle failed: {e}")
            raise ExternalServiceError(f"Parsing failed: {e}", service_name="LLM_Parser")

