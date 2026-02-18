import logging
from typing import Dict, Any, Optional
from fastapi import UploadFile, BackgroundTasks

from app.infrastructure.storage.supabase_service import SupabaseStorageService
from app.infrastructure.ocr.tesseract_service import OCRService
from app.infrastructure.parser.gemini_parser_service import GeminiParserService
from app.infrastructure.sheets.transaction_categorizer import TransactionCategorizer
from .document_processor import DocumentProcessor
from .sync_service import DocumentSyncService
from .anonymous_processor import AnonymousProcessor

logger = logging.getLogger(__name__)

class UploadOrchestrator:
    """
    Orchestrates the entire upload process:
    1. Save file to storage (Supabase)
    2. Process document (OCR + Parse)
    3. Categorize transactions
    4. Queue background synchronization
    """

    def __init__(self):
        self.storage_service = SupabaseStorageService()
        
        self.ocr_service = OCRService()
        self.parser_service = GeminiParserService()
        self.document_processor = DocumentProcessor(self.ocr_service, self.parser_service)
        self.anonymous_processor = AnonymousProcessor(self.ocr_service, self.parser_service)
        
        self.categorizer = TransactionCategorizer()
        self.sync_service = DocumentSyncService()

    async def handle_upload(
        self, 
        file: UploadFile, 
        background_tasks: BackgroundTasks, 
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handles the full upload and processing lifecycle.
        """
        user_id = current_user["userId"]
        company_name = current_user["companyName"]
        company_id = current_user["activeCompany"]
        
        logger.info(f"Uploading document for user: {user_id}, company: {company_name}")

        # 1. Save uploaded file
        storage_result = await self.storage_service.save_file(file)
        image_url = storage_result["url"]
        image_path = storage_result["path"]

        # 2. Process file (OCR + parsing + saving to Firebase)
        processing_result = await self.document_processor.process_image_async(
            image_path=image_path,
            user_id=user_id,
            company_id=company_id,
            image_url=image_url,
            file=file
        )
        
        document_key = processing_result["document_key"]
        full_data = processing_result.get("full_data", {})

        # 3. Categorize transaction
        categorization_result = None
        auto_category = None
        
        if company_name:
            categorization_result = self.categorizer.categorize_transaction(
                full_data, company_name
            )
            auto_category = categorization_result.get("category")
            
            logger.info(f"Categorization: {auto_category} (Confidence: {categorization_result.get('confidence', 0):.2%})")

        # 4. Schedule background tasks
        # Index document
        background_tasks.add_task(
            self.sync_service.index_document,
            document_key,
            full_data,
            user_id,
            company_id,
            image_url
        )
        
        # Sync to Google Sheets
        background_tasks.add_task(
            self.sync_service.sync_to_google_sheets,
            document_key,
            auto_category,
            company_name,
            user_id,
            company_id
        )

        response = {
            "status": "success",
            "image_url": image_url,
            "document_key": document_key,
            "parsed": processing_result,
        }

        if categorization_result:
            response["categorization"] = categorization_result

        return response
