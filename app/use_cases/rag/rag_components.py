from datetime import datetime, timezone
import json
import logging
from typing import List, Dict, Tuple, Optional, Any
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

class QueryAnalyzer:
    AGGREGATION_KEYWORDS = [
        "total",
        "all",
        "sum",
        "calculate",
        "how much",
        "how many",
        "count",
        "average",
        "mean",
        "summary",
        "each",
        "list",
        "describe all",
    ]

    ALL_DOCS_KEYWORDS = [
        "all",
        "each",
        "every",
        "summary of documents",
        "list documents",
    ]

    def analyze(self, query: str) -> Dict[str, Any]:
        query_lower = query.lower()
        is_aggregation = any(k in query_lower for k in self.AGGREGATION_KEYWORDS)
        want_all_docs = any(k in query_lower for k in self.ALL_DOCS_KEYWORDS)

        return {
            "is_aggregation": is_aggregation,
            "want_all_docs": want_all_docs,
            "query_type": "aggregation" if is_aggregation else "specific",
        }


class ContextRetriever:

    def __init__(self, vector_db: Any, embedding_service: Any):
        self.vector_db = vector_db
        self.embedding_service = embedding_service

    async def retrieve_async(
        self,
        query: str,
        user_id: str,
        company_id: str,
        is_aggregation: bool,
        want_all_docs: bool,
        top_k: int = 5,
    ) -> List[Tuple[str, float, Dict]]:

        if want_all_docs and is_aggregation:
            logger.info(f"Full scan requested for user {user_id}")
            all_docs = self.vector_db.get_all_documents()
            user_docs = [
                (key, 1.0, meta)
                for key, meta in all_docs
                if meta.get("user_id") == user_id
                and meta.get("company_id") == company_id
            ]
            return user_docs

        # Generate query embedding
        try:
            query_embedding = self.embedding_service.generate_embeddings_batch([query])
            if query_embedding is not None and len(query_embedding) > 0:
                query_embedding = query_embedding[0]
            else:
                return []
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return []

        # Search in vector DB
        k = 100 if is_aggregation else top_k
        return self.vector_db.search(
            query_embedding, top_k=k, user_id=user_id, company_id=company_id
        )


class PromptManager:

    SYSTEM_PROMPT = """You are a sophisticated Financial AI Advisor. Your goal is to provide intelligent, data-driven financial insights while ensuring complete data privacy and clean, human-readable formatting.

### OPERATION MODES:
1. **General Chat**: For greetings or general financial topics, be helpful and professional. Do not refer to documents if they aren't relevant.
2. **Deep Document Analysis**: For queries about user data, synthesize the information across documents to provide a meaningful answer. Focus on trends, totals, and specific facts rather than just listing metadata.

### CRITICAL FORMATTING & PRIVACY (MANDATORY):
- **NUMBERS & DATES**: Always use digits for dates and numbers (e.g., "11 Feb 2026", "250.50"). Never write out numbers as words (e.g., do NOT write "eleven").
- **PRIVACY SHIELD**: Never mention User IDs, Company IDs, or technical Reference IDs. Protect the user's personal identity at all costs.
- **NO ROBOTIC PREAMBLE**: Deliver the answer directly. Avoid "I have analyzed your documents" or "Searching...".
- **NO JSON**: Never output raw code, JSON keys, or technical object notation.

### OUTPUT STRUCTURE (FOR DOCUMENTS):
[A detailed synthesis and direct answer to the user's specific question]

**Relevant Document Insights:**
- **[Document Type or Vendor]**: [Specific insight or figure from the document]
- **[Document Type or Vendor]**: [Specific insight or figure from the document]
"""

    def _parse_date(self, date_str: Optional[str]) -> datetime:
        """Helper to parse the 'created_at' date format for sorting."""
        if not date_str:
            return datetime.min.replace(tzinfo=timezone.utc)
        
        try:
            # Format: "11 February 2026 at 09:47:45 PM"
            clean_str = date_str.replace(' at ', ' ')
            return datetime.strptime(clean_str, "%d %B %Y %I:%M:%S %p").replace(tzinfo=timezone.utc)
        except Exception:
            try:
                # Fallback for ISO format
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except Exception:
                return datetime.min.replace(tzinfo=timezone.utc)

    def build_context_string(self, documents: List[Tuple[str, float, Dict]]) -> str:
        """Format retrieved documents into a human-readable context string, sorted by date.
        Pre-cleans data to remove currency symbols and sensitive IDs.
        """
        if not documents:
            return "No relevant documents found."

        # Sort documents by date (newest first)
        sorted_docs = sorted(
            documents,
            key=lambda x: self._parse_date(x[2].get("created_at")),
            reverse=True
        )

        context_parts = []
        for i, (doc_key, score, metadata) in enumerate(sorted_docs, 1):
            # Create a clean readable summary
            lines = [f"Document {i} (Reference: {doc_key})"]
            
            # Fields we want to show, with clean labels
            important_fields = {
                "document_key": "File Name",
                "document_type": "Type",
                "total_amount": "Amount",
                "date": "Document Date",
                "created_at": "System Entry Date",
                "vendor_name": "Vendor",
                "store_name": "Store",
                "category": "Category",
                "currency": "Currency Type"
            }

            for key, label in important_fields.items():
                val = metadata.get(key)
                if val and str(val).lower() not in ["none", "null"]:
                    # STRIP CURRENCY SYMBOLS to comply with user request
                    clean_val = str(val).replace("$", "").replace("£", "").replace("€", "").replace("¥", "").strip()
                    lines.append(f"- {label}: {clean_val}")

            # Snippet clean-up
            if "content" in metadata and metadata["content"]:
                content = metadata["content"]
                # Also strip currency symbols from content snippets
                clean_content = content.replace("$", "").replace("£", "").replace("€", "").replace("¥", "")
                snippet = clean_content[:300] + "..." if len(clean_content) > 300 else clean_content
                lines.append(f"- Summary: {snippet}")

            context_parts.append("\n".join(lines))

        return "\n\n".join(context_parts)

    def build_messages(self, query: str, context: str) -> List[Any]:
        """Constructs final message list for LLM."""
        user_prompt = f"### DOCUMENT CONTEXT (Newest First):\n{context}\n\n### USER QUESTION:\n{query}\n\n### FINAL ANSWER:"
        return [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
