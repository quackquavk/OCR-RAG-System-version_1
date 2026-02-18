from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from app.presentation.auth_middleware import get_current_user
from app.infrastructure.firebase.company import CompanyService
from app.infrastructure.vector_db.faiss_service import get_faiss_service
from app.core.exceptions import  DatabaseError

from app.infrastructure.vector_db.supabase_vector_service import get_supabase_vector_service
from app.infrastructure.firebase.documents import DocumentService
from app.infrastructure.storage.supabase_service import SupabaseStorageService


import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/companies", tags=["Companies"])

@router.delete("/{company_id}", status_code=status.HTTP_200_OK)
async def delete_company(
    company_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    RESTful API to delete a company and all its associated data.
    
    This includes:
    - All documents and metadata in Firebase
    - All local media files (images, processed documents)
    - All RAG/Vector embeddings
    """
    user_id = current_user.get("userId")
    
    try:
        logger.info(f"Initiating full permanent deletion for company {company_id} (User: {user_id})")

        # 1. Fetch all documents for this company to identify files in storage
        doc_service = DocumentService()
        documents = await doc_service.get_all_async(user_id, company_id)
        
        # 2. Delete files from Supabase Storage
        storage_service = SupabaseStorageService()
        files_deleted = 0
        
        if documents and isinstance(documents, dict):
            for doc_key, doc_data in documents.items():
                # Try to find file path/name in document metadata
                # Common keys: 'path', 'filename', 'file_path'
                file_to_delete = doc_data.get("path") or doc_data.get("filename") or doc_data.get("file_path")
                if file_to_delete:
                    try:
                        await storage_service.delete_file(file_to_delete)
                        files_deleted += 1
                    except Exception as se:
                        logger.warning(f"Failed to delete file {file_to_delete} from storage: {se}")

        # 3. Permanently delete vectors from Supabase Vector DB
        vector_service = get_supabase_vector_service()
        vectors_removed = vector_service.delete_permanently_by_company(user_id, company_id)
        logger.info(f"Permanently removed {vectors_removed} vector entries")

        # 4. Delete company data from Firebase and local files
        company_service = CompanyService()
        await company_service.delete_company_async(
            user_id=user_id,
            company_id=company_id,
            delete_local_files=True
        )

        return {
            "status": "success",
            "message": f"Company {company_id} and all associated data have been permanently deleted",
            "cleanup_details": {
                "documents_processed": len(documents) if documents else 0,
                "storage_files_removed": files_deleted,
                "vectors_permanently_removed": vectors_removed,
                "firebase_data_removed": True
            }
        }

    except DatabaseError as e:
        logger.error(f"Database error during company deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error during company deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
