from fastapi import APIRouter, UploadFile, BackgroundTasks, HTTPException, Depends, Response
from fastapi.responses import FileResponse
import logging
import os
from typing import Optional 
from pathlib import Path
from PIL import Image
import io

from app.use_cases.processing.upload_orchestrator import UploadOrchestrator
from app.presentation.auth_middleware import get_current_user
from app.presentation.schemas.parsed_data_model import ProcessDocumentResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Uploads"])

upload_orchestrator = UploadOrchestrator()

@router.post("/process-image")
async def process_image(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    Process uploaded image with user-specific data isolation.
    """
    try:
        return await upload_orchestrator.handle_upload(
            file=file,
            background_tasks=background_tasks,
            current_user=current_user
        )
    
    except ValueError as e:
        logger.warning(f"Validation error during upload: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.exception(f"Unexpected error during document processing: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred while processing the document.")


@router.post("/process-document", response_model=ProcessDocumentResponse)
async def process_document(file: UploadFile):
    """
    Standalone document processing API.
    Extracts text and parses data (total amount, vendor, date, etc.) without persistence.
    Supports Images and PDFs.
    """
    logger.info(f"Anonymous process-document request for file: {file.filename}")
    
    try:
        # 1. Read file content
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        # 2. Process via Use Case
        data = await upload_orchestrator.anonymous_processor.process_document(
            content=content, 
            filename=file.filename
        )

        return ProcessDocumentResponse(
            status="success",
            data=data
        )

    except ValueError as e:
        logger.warning(f"Processing error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        logger.error(f"System error during processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error in process-document: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.delete("/delete-image/{filename:path}")
async def delete_image(
    filename: str,
    doc_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an image from Supabase Storage, metadata from Firebase, and embeddings from Vector DB.
    """
    user_id = current_user.get("userId")
    company_id = current_user.get("activeCompany")
    
    logger.info(f"Full delete request for file: {filename}, doc_id: {doc_id} by user: {user_id}")
    
    try:
        # 1. Delete from Supabase Storage
        from app.infrastructure.storage.supabase_service import SupabaseStorageService
        storage_service = SupabaseStorageService()
        storage_success = await storage_service.delete_file(filename)
        
        # 2. Delete from Firebase if doc_id is provided
        firebase_success = True
        if doc_id:
            from app.infrastructure.firebase.documents import DocumentService
            doc_service = DocumentService()
            firebase_success = await doc_service.delete_async(user_id, company_id, doc_id)
            
            # 3. Permanent Delete from Vector DB
            try:
                from app.infrastructure.vector_db.supabase_vector_service import get_supabase_vector_service
                vector_service = get_supabase_vector_service()
                vector_service.delete_document_permanently(doc_id)
                logger.info(f"Permanently deleted document {doc_id} from Vector DB")
            except Exception as ve:
                logger.warning(f"Failed to permanently delete document {doc_id} from Vector DB: {ve}")

        if storage_success or (doc_id and firebase_success):
            return {
                "status": "success", 
                "message": f"Document {doc_id or filename} deleted successfully",
                "details": {
                    "storage": storage_success,
                    "firebase": firebase_success if doc_id else "skipped"
                }
            }
        else:
            raise HTTPException(status_code=404, detail=f"File {filename} not found or could not be deleted")
            
    except Exception as e:
        logger.error(f"Error during full deletion of {filename}: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")
