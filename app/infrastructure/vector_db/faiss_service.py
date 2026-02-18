"""
FAISS Vector Database Service
Manages document embeddings and similarity search using FAISS.
Refactored for SRP, simplicity, and readability.
"""

# import faiss
import numpy as np
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from app.core.exceptions import DatabaseError, NotFoundError

logger = logging.getLogger(__name__)

class FAISSPersistence:
    """Handles saving and loading of FAISS index and metadata from disk."""
    
    def __init__(self, base_path: Path):
        self.index_path = base_path / "index.faiss"
        self.pkl_path = base_path / "index.pkl"

    def save(self, index, state: Dict):
        """Persists the index and metadata state to disk."""
        try:
            # if index is not None:
            #     faiss.write_index(index, str(self.index_path))
            
            with open(self.pkl_path, "wb") as f:
                pickle.dump(state, f)
            logger.debug("FAISS index and metadata saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save FAISS data: {e}", exc_info=True)
            raise DatabaseError(f"Persistence error: {e}", operation="save")

    def load(self) -> Optional[Dict]:
        """Loads index and state from disk if they exist."""
        try:
            index = None
            # if self.index_path.exists():
            #     index = faiss.read_index(str(self.index_path))
            
            state = {}
            if self.pkl_path.exists():
                with open(self.pkl_path, "rb") as f:
                    state = pickle.load(f)
            
            if index is not None:
                state["index"] = index
                return state
            return None
        except Exception as e:
            logger.error(f"Error loading FAISS data: {e}", exc_info=True)
            raise DatabaseError(f"Load error: {e}", operation="load")

class FAISSSearcher:
    """Focuses on searching and filtering results from the FAISS index."""

    def search(
        index,
        query_embedding: np.ndarray,
        metadata: Dict[int, Dict],
        reverse_mapping: Dict[int, str],
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
    ) -> List[Tuple[str, float, Dict]]:
        """Performs search and applies multi-tenant filtering."""
        if index is None or index.ntotal == 0:
            return []

        # Prepare query
        query_array = query_embedding.reshape(1, -1).astype("float32")
        
        # We fetch more results than top_k to allow for filtering gaps
        search_limit = min(top_k * 5, index.ntotal)
        distances, indices = index.search(query_array, search_limit)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1: continue
            
            idx = int(idx)
            doc_meta = metadata.get(idx, {})

            # 1. Filter: Deleted
            if doc_meta.get("deleted", False): continue

            # 2. Filter: Multi-tenancy (User & Company)
            if user_id and doc_meta.get("user_id") != user_id: continue
            if company_id and doc_meta.get("company_id") != company_id: continue

            # 3. Filter: Score
            if score_threshold is not None and dist > score_threshold: continue

            # Format and add result
            doc_key = reverse_mapping.get(idx)
            if doc_key:
                results.append((doc_key, float(dist), doc_meta))
            
            if len(results) >= top_k: break

        return results

class FAISSService:
    """
    Main entry point for FAISS operations.
    Acts as a simple facade for metadata management, persistence, and search.
    """

    def __init__(self, vector_db_path: str = "data/vector_db"):
        db_path = Path(vector_db_path)
        db_path.mkdir(parents=True, exist_ok=True)
        
        self.persistence = FAISSPersistence(db_path)
        
        # State
        self.index = None # Optional[faiss.Index]
        self.metadata: Dict[int, Dict] = {}        # FAISS ID -> metadata
        self.id_mapping: Dict[str, int] = {}       # document_key -> FAISS ID
        self.reverse_mapping: Dict[int, str] = {}  # FAISS ID -> document_key
        self.embedding_dim: Optional[int] = None
        self.next_id = 0

        self._load_from_disk()

    def _load_from_disk(self):
        """Internal load helper."""
        state = self.persistence.load()
        if state:
            self.index = state.get("index")
            self.metadata = state.get("metadata", {})
            self.id_mapping = state.get("id_mapping", {})
            self.reverse_mapping = state.get("reverse_mapping", {})
            self.next_id = state.get("next_id", 0)
            self.embedding_dim = state.get("embedding_dim")

    def _save_to_disk(self):
        """Internal save helper."""
        state = {
            "metadata": self.metadata,
            "id_mapping": self.id_mapping,
            "reverse_mapping": self.reverse_mapping,
            "next_id": self.next_id,
            "embedding_dim": self.embedding_dim,
        }
        self.persistence.save(self.index, state)

    def initialize_index(self, embedding_dim: int):
        """Initializes a new flat L2 index."""
        self.embedding_dim = embedding_dim
        try:
            # self.index = faiss.IndexFlatL2(embedding_dim)
            logger.info(f"Initialized FAISS index (dim={embedding_dim}) - [DISABLED]")
        except Exception as e:
            raise DatabaseError(f"Index initialization failed: {e}", operation="init")

    def add_document(self, document_key: str, embedding: np.ndarray, metadata: Dict) -> int:
        """Adds or updates a document in the vector store."""
        if self.index is None:
            self.initialize_index(len(embedding))

        if document_key in self.id_mapping:
            return self.update_document(document_key, embedding, metadata)

        try:
            # 1. Add to FAISS
            embedding_array = embedding.reshape(1, -1).astype("float32")
            self.index.add(embedding_array)

            # 2. Track internal state
            faiss_id = self.next_id
            self.metadata[faiss_id] = metadata
            self.id_mapping[document_key] = faiss_id
            self.reverse_mapping[faiss_id] = document_key
            self.next_id += 1

            self._save_to_disk()
            return faiss_id
        except Exception as e:
            logger.error(f"Failed to add document {document_key}: {e}")
            raise DatabaseError(f"Add document failed: {e}")

    def update_document(self, document_key: str, embedding: np.ndarray, metadata: Dict) -> int:
        """Updates metadata for an existing document (FAISS index is cumulative)."""
        if document_key not in self.id_mapping:
            raise NotFoundError(f"Document {document_key} not found", resource_id=document_key)

        faiss_id = self.id_mapping[document_key]
        self.metadata[faiss_id] = metadata
        self._save_to_disk()
        return faiss_id

    def delete_document(self, document_key: str):
        """Soft-deletes a document in metadata."""
        if document_key not in self.id_mapping:
            raise NotFoundError(f"Document {document_key} not found", resource_id=document_key)

        faiss_id = self.id_mapping[document_key]
        if faiss_id in self.metadata:
            self.metadata[faiss_id]["deleted"] = True
        
        self._save_to_disk()

    def delete_by_company(self, user_id: str, company_id: str) -> int:
        """Soft-deletes all documents belonging to a specific company."""
        count = 0
        for faiss_id, meta in self.metadata.items():
            if meta.get("user_id") == user_id and meta.get("company_id") == company_id:
                if not meta.get("deleted"):
                    meta["deleted"] = True
                    count += 1
        
        if count > 0:
            self._save_to_disk()
            logger.info(f"Soft-deleted {count} vectors for company {company_id}")
        
        return count

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
    ) -> List[Tuple[str, float, Dict]]:
        """Searches for similar documents using delegated searcher logic."""
        return FAISSSearcher.search(
            index=self.index,
            query_embedding=query_embedding,
            metadata=self.metadata,
            reverse_mapping=self.reverse_mapping,
            top_k=top_k,
            score_threshold=score_threshold,
            user_id=user_id,
            company_id=company_id
        )

    def get_all_documents(self) -> List[Tuple[str, Dict]]:
        """Returns all non-deleted documents."""
        results = []
        for faiss_id, meta in self.metadata.items():
            if meta.get("deleted"): continue
            
            key = self.reverse_mapping.get(faiss_id)
            if key: results.append((key, meta))
        return results

    def get_stats(self) -> Dict:
        """Returns simple database statistics."""
        return {
            "total_documents": self.index.ntotal if self.index else 0,
            "active_documents": len([m for m in self.metadata.values() if not m.get("deleted")]),
            "embedding_dimension": self.embedding_dim,
        }

# Singleton instance
_faiss_service = None

def get_faiss_service() -> FAISSService:
    """Factory for FAISSService singleton."""
    global _faiss_service
    if _faiss_service is None:
        _faiss_service = FAISSService()
    return _faiss_service
