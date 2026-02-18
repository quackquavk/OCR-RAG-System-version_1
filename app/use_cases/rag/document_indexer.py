"""Document Indexing Service
Generates structured summaries and indexes documents in vector DB.
This module provides a  entrypoint for converting parsed documents into vector embeddings and storing them in the vector database.
"""

from typing import Dict, List
import asyncio
import json
from datetime import datetime

from app.infrastructure.embeddings.embedding_service import get_embedding_service
from app.infrastructure.vector_db.faiss_service import get_faiss_service
from app.core.exceptions import DatabaseError, ExternalServiceError, BaseAppException

import logging
from dotenv import load_dotenv
import os
load_dotenv()
logger = logging.getLogger(__name__)


class DocumentIndexer:
    """Service for indexing documents in the vector database"""

    def __init__(self):
        self.embedding_service = get_embedding_service()
        
        # Switch between FAISS and Supabase
        vector_store_type = os.getenv("VECTOR_STORE", "supabase").lower()
        if vector_store_type == "supabase":
            from app.infrastructure.vector_db.supabase_vector_service import get_supabase_vector_service
            self.vector_db = get_supabase_vector_service()
        else:
            try:
                from app.infrastructure.vector_db.faiss_service import get_faiss_service
                self.vector_db = get_faiss_service()
            except ImportError:
                logger.warning("FAISS not available, falling back to Supabase")
                from app.infrastructure.vector_db.supabase_vector_service import get_supabase_vector_service
                self.vector_db = get_supabase_vector_service()

    def generate_structured_summary(self, parsed_data: Dict) -> str:
        """
        Generate structured summary from parsed OCR data

        Args:
            parsed_data: Parsed document data

        Returns:
            Structured summary string (JSON representation)
        """

        try:
            data_to_embed = parsed_data.copy()

            # Remove non-semantic/internal fields to save tokens
            for k in ("document_key", "image_url"):
                if k in data_to_embed:
                    data_to_embed.pop(k, None)

            summary = json.dumps(data_to_embed, indent=2)
            return summary
        except Exception as e:
            logger.error(f"generate_structured_summary failed: {e}", exc_info=True)
            raise BaseAppException(f"Failed to generate structured summary: {e}")

    async def index_document_async(self, document_key: str, parsed_data: Dict) -> bool:
        """
        Index a document in the vector database
        """
        logger.info(f"DocumentIndexer: Starting index_document_async for {document_key}")
        if "user_id" not in parsed_data or not parsed_data["user_id"]:
            logger.error(
                "Missing user_id for document indexing",
                extra={"document_key": document_key},
            )
            raise BaseAppException(
                "user_id is required for document indexing",
                status_code=400,
                details={"document_key": document_key},
            )

        if "company_id" not in parsed_data or not parsed_data["company_id"]:
            logger.error(
                "Missing company_id for document indexing",
                extra={"document_key": document_key},
            )
            raise BaseAppException(
                "company_id is required for document indexing",
                status_code=400,
                details={"document_key": document_key},
            )

        try:
            summary = self.generate_structured_summary(parsed_data)
            logger.info(f"DocumentIndexer: Summary length for {document_key}: {len(summary)}")

            embedding = await self._generate_embedding(summary)
            logger.info(f"DocumentIndexer: Embedding generated for {document_key}")

            metadata = self._prepare_metadata(document_key, parsed_data, summary)

            logger.info(f"DocumentIndexer: Dispatching to vector_db.add_document for {document_key} (Type: {type(self.vector_db).__name__})")
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                self._add_document_to_vector_db,
                document_key,
                embedding,
                metadata,
            )

            logger.info(
                "Successfully indexed document",
                extra={
                    "document_key": document_key,
                    "user_id": metadata.get("user_id"),
                    "company_id": metadata.get("company_id"),
                },
            )
            return True
        except BaseAppException:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error indexing document {document_key}: {e}", exc_info=True
            )
            raise DatabaseError(
                f"Unexpected error indexing document {document_key}: {e}",
                operation="index_document",
            )

    async def _generate_embedding(self, text: str):
        """Generate an embedding for the given text and wrap errors."""
        try:
            emb = await self.embedding_service.generate_embedding_async(text)
            if emb is None or getattr(emb, "size", 1) == 0:
                raise ExternalServiceError(
                    "Empty embedding returned", service_name="embedding"
                )
            return emb
        except ExternalServiceError:
            raise
        except Exception as e:
            logger.error("Embedding generation failed", exc_info=True)
            raise ExternalServiceError(
                f"Embedding generation failed: {e}",
                service_name="embedding",
                original_error=e,
            )

    def _prepare_metadata(
        self, document_key: str, parsed_data: Dict, summary: str
    ) -> Dict:
        """Prepare metadata dict to be stored along with the vector.

        This method centralizes how metadata is shaped so future additions
        (e.g., versioning, source attribution) are easy to add.
        """
        try:
            metadata = parsed_data.copy()
            metadata["document_key"] = document_key
            metadata["text_summary"] = summary
            metadata.setdefault("deleted", False)
            metadata.setdefault("created_at", datetime.utcnow().isoformat())
            return metadata
        except Exception as e:
            logger.error("Preparing metadata failed", exc_info=True)
            raise BaseAppException(f"Failed to prepare metadata: {e}")

    def _add_document_to_vector_db(self, document_key: str, embedding, metadata: Dict):
        """Add a document to the vector DB (blocking). Wraps DB errors."""
        try:
            self.vector_db.add_document(document_key, embedding, metadata)
        except DatabaseError:
            logger.error(
                f"Vector DB operation failed for {document_key}", exc_info=True
            )
            raise
        except Exception as e:
            logger.error(f"Failed to add document to vector DB: {e}", exc_info=True)
            raise DatabaseError(
                f"Failed to add document to vector DB: {e}", operation="add_document"
            )


# Singleton instance
_document_indexer = None

def get_document_indexer() -> DocumentIndexer:
    """Get or create the singleton document indexer instance"""
    global _document_indexer
    if _document_indexer is None:
        _document_indexer = DocumentIndexer()
    return _document_indexer
