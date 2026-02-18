import os
import logging
from typing import List, Dict, Tuple, Optional
import numpy as np
from app.infrastructure.storage.supabase_service import SupabaseService
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)

class SupabaseVectorService:
    """
    Adapter for Supabase PG Vector that mimics the FAISSService interface.
    This allows RAG components to work with cloud storage without modification.
    """

    def __init__(self):
        self.supabase_service = SupabaseService()
        self.client = self.supabase_service.supabase

    def add_document(self, document_key: str, embedding: np.ndarray, metadata: Dict) -> str:
        """
        Synchronous wrapper for document indexing to Supabase.
        """
        logger.info(f"SupabaseVectorService: Attempting to add document {document_key}")
        try:
            # metadata contains user_id, company_id, text_summary etc.
            user_id = metadata.get("user_id")
            company_id = metadata.get("company_id")
            content = metadata.get("text_summary", "")

            logger.info(f"SupabaseVectorService: Metadata - user_id={user_id}, company_id={company_id}, content_len={len(content)}")

            if not user_id or not company_id:
                logger.error(f"SupabaseVectorService: Missing required metadata for doc {document_key}")
                raise ValueError("user_id and company_id are required in metadata")

            # Convert numpy array to list for JSON serialization
            emb_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
            logger.info(f"SupabaseVectorService: Embedding size: {len(emb_list)}")

            data = {
                "document_key": document_key,
                "user_id": user_id,
                "company_id": company_id,
                "content": content,
                "embedding": emb_list,
                "deleted": False
            }

            # Upsert using document_key + user_id + company_id if you want to prevent duplicates
            logger.info(f"SupabaseVectorService: Executing insert into 'embeddings' table...")
            response = self.client.table("embeddings").insert(data).execute()
            
            # logger.info(f"SupabaseVectorService: Insert response: {response}")
            logger.info(f"Successfully stored embedding for doc {document_key} in Supabase")
            return document_key
        except Exception as e:
            logger.error(f"SupabaseVectorService: Failed to add document {document_key}: {str(e)}", exc_info=True)
            raise DatabaseError(f"Supabase Vector insert failed: {e}")

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
    ) -> List[Tuple[str, float, Dict]]:
        """
        Similarity search using the match_embeddings RPC function.
        """
        try:
            emb_list = query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding
            
            # Call RPC
            rpc_params = {
                "query_embedding": emb_list,
                "match_threshold": score_threshold or 0.1, # similarity score [0, 1]
                "match_count": top_k,
                "p_user_id": user_id,
                "p_company_id": company_id
            }

            response = self.client.rpc("match_embeddings", rpc_params).execute()
            results = response.data or []

            # Format to (doc_key, similarity, metadata)
            formatted_results = []
            for item in results:
                formatted_results.append((
                    item["document_key"],
                    float(item["similarity"]),
                    {
                        "content": item["content"],
                        "user_id": item["user_id"],
                        "company_id": item["company_id"]
                    }
                ))
            
            return formatted_results
        except Exception as e:
            logger.error(f"Supabase RPC search failed: {e}")
            raise DatabaseError(f"Supabase Vector search failed: {e}")

    def delete_document(self, document_key: str):
        """Soft deletes a document in Supabase."""
        try:
            self.client.table("embeddings").update({"deleted": True}).eq("document_key", document_key).execute()
        except Exception as e:
            logger.error(f"Failed to delete doc {document_key} from Supabase: {e}")

    def delete_document_permanently(self, document_key: str):
        """Permanently deletes a document in Supabase."""
        try:
            self.client.table("embeddings").delete().eq("document_key", document_key).execute()
        except Exception as e:
            logger.error(f"Failed to permanently delete doc {document_key} from Supabase: {e}")

    def delete_by_company(self, user_id: str, company_id: str) -> int:
        """Soft-deletes all documents for a company."""
        try:
            response = self.client.table("embeddings").update({"deleted": True}).eq("user_id", user_id).eq("company_id", company_id).execute()
            return len(response.data) if response.data else 0
        except Exception as e:
            logger.error(f"Failed to clear company {company_id} from Supabase: {e}")
            return 0

    def delete_permanently_by_company(self, user_id: str, company_id: str) -> int:
        """Permanently deletes all documents for a company."""
        try:
            response = self.client.table("embeddings").delete().eq("user_id", user_id).eq("company_id", company_id).execute()
            return len(response.data) if response.data else 0
        except Exception as e:
            logger.error(f"Failed to permanently delete company {company_id} from Supabase: {e}")
            return 0

    def get_all_documents(self) -> List[Tuple[str, Dict]]:
        """Not efficient for cloud, but kept for interface compatibility."""
        try:
            response = self.client.table("embeddings").select("*").eq("deleted", False).execute()
            return [
                (r["document_key"], {"content": r["content"], "user_id": r["user_id"], "company_id": r["company_id"]})
                for r in (response.data or [])
            ]
        except Exception as e:
            logger.error(f"Failed to fetch all docs from Supabase: {e}")
            return []

# Singleton instance management (similar to FAISS)
_supabase_vector_service = None

def get_supabase_vector_service() -> SupabaseVectorService:
    global _supabase_vector_service
    if _supabase_vector_service is None:
        _supabase_vector_service = SupabaseVectorService()
    return _supabase_vector_service
