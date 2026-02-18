import os
import json
import logging
from typing import Dict, Any, List, AsyncIterator

from app.infrastructure.embeddings.embedding_service import get_embedding_service
from app.infrastructure.vector_db.faiss_service import get_faiss_service
from app.infrastructure.vector_db.supabase_vector_service import get_supabase_vector_service

from app.infrastructure.rate_limiter import get_rate_limiter, APIProvider
from app.core.exceptions import ExternalServiceError, DatabaseError, RateLimitExceededError
from .rag_components import QueryAnalyzer, ContextRetriever, PromptManager
from .llm_factory import LLMFactory

logger = logging.getLogger(__name__)


class RAGService:

    def __init__(
        self,
        analyzer: QueryAnalyzer,
        retriever: ContextRetriever,
        prompt_manager: PromptManager,
        llm: Any,
        rate_limiter: Any
    ):

        self.analyzer = analyzer
        self.retriever = retriever
        self.prompt_manager = prompt_manager
        self.llm = llm
        self.rate_limiter = rate_limiter
        
        logger.info("RAG Service initialized successfully")

    async def chat_async(self, query: str, user_id: str, company_id: str) -> Dict[str, Any]:
 
        try:
            analysis = self.analyzer.analyze(query)
            logger.debug(f"Query analysis: {analysis}")
            
            documents = await self.retriever.retrieve_async(
                query=query,
                user_id=user_id,
                company_id=company_id,
                is_aggregation=analysis["is_aggregation"],
                want_all_docs=analysis["want_all_docs"]
            )
            logger.info(f"Retrieved {len(documents)} documents for query")
            
            context_str = self.prompt_manager.build_context_string(documents)
            messages = self.prompt_manager.build_messages(query, context_str)
            
            response = await self.rate_limiter.execute_with_retry(
                self.llm.ainvoke, messages, priority=0
            )
            
            bot_response = response.content or "I'm sorry, I couldn't generate a response. Please try rephrasing your question."
            
            sources = [
                {
                    "document_key": doc_key,
                    "store_name": meta.get("store_name", meta.get("vendor_name", "Unknown")),
                    "date": meta.get("date", "Unknown"),
                    "total_amount": meta.get("total_amount", "0.00"),
                }
                for doc_key, score, meta in documents
            ]
            
            return {
                "response": bot_response,
                "query_type": analysis["query_type"],
                "documents_retrieved": len(documents),
                "sources": sources,
            }

        except Exception as e:
            logger.error(f"Error in RAG chat_async: {e}", exc_info=True)
            
            if isinstance(e, (ExternalServiceError, DatabaseError, RateLimitExceededError)):
                raise
            
            raise ExternalServiceError(
                f"Unexpected error in RAG service: {e}",
                service_name="RAG_Service",
                original_error=e
            )

    async def chat_stream(self, query: str, user_id: str, company_id: str) -> AsyncIterator[str]:
      
        try:
            analysis = self.analyzer.analyze(query)
            
            documents = await self.retriever.retrieve_async(
                query=query,
                user_id=user_id,
                company_id=company_id,
                is_aggregation=analysis["is_aggregation"],
                want_all_docs=analysis["want_all_docs"]
            )
            logger.info(f"Streaming response for query with {len(documents)} documents")
            
            context_str = self.prompt_manager.build_context_string(documents)
            messages = self.prompt_manager.build_messages(query, context_str)

            sources = [
                {
                    "document_key": doc_key,
                    "store_name": meta.get("store_name", meta.get("vendor_name", "Unknown")),
                    "date": meta.get("date", "Unknown"),
                    "total_amount": meta.get("total_amount", "0.00"),
                }
                for doc_key, score, meta in documents
            ]

            metadata = {
                'query_type': analysis['query_type'],
                'sources': sources
            }
            yield f"metadata:{json.dumps(metadata)}\n"

            await self.rate_limiter._scheduler.wait_for_slot(priority=0)
            
            async for chunk in self.llm.astream(messages):
                yield f"data:{chunk}\n"

        except Exception as e:
            logger.error(f"Error in RAG chat_stream: {e}", exc_info=True)
            yield f"error:{str(e)}\n"


_rag_service = None

def get_rag_service() -> RAGService:
    global _rag_service
    
    if _rag_service is not None:
        return _rag_service
    
    try:
        logger.info("Initializing RAG Service dependencies...")
        
        embedding_service = get_embedding_service()
        logger.info("Embedding service initialized")
        
        vector_store_type = os.getenv("VECTOR_STORE", "supabase").lower()
        
        if vector_store_type == "supabase":
            vector_db = get_supabase_vector_service()
            logger.info("Using Supabase PG Vector as vector store")
        else:
            try:
                vector_db = get_faiss_service()
                logger.info("Using FAISS as vector store")
            except ImportError:
                logger.warning("FAISS not available, falling back to Supabase")
                vector_db = get_supabase_vector_service()
                logger.info("Using Supabase PG Vector as vector store (fallback)") 

        llm, rate_limiter = LLMFactory.create()
        logger.info(f"LLM and Rate Limiter initialized via Factory")

        _rag_service = RAGService(
            analyzer=QueryAnalyzer(),
            retriever=ContextRetriever(vector_db, embedding_service),
            prompt_manager=PromptManager(),
            llm=llm,
            rate_limiter=rate_limiter
        )
        
        logger.info("RAG Service fully initialized and ready")
        
    except Exception as e:
        logger.error(f"Failed to compose RAGService: {e}", exc_info=True)
        raise ExternalServiceError(
            "Failed to initialize RAG Service",
            service_name="RAG_Service",
            original_error=e
        )

    return _rag_service
