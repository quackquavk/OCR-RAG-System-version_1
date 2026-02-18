"""
This class orchestrates the end-to-end processing of an uploaded
document. It delegates OCR, parsing and persistence to dedicated
services and converts low-level errors into application exceptions
that are easier to handle at the API layer.
"""

from pathlib import Path
from datetime import datetime

from app.utils.key_generator import KeyGenerator
from fastapi import UploadFile
from app.infrastructure.firebase import DocumentService
from app.infrastructure.parser.gemini_parser_service import GeminiParserService
from app.infrastructure.ocr.tesseract_service import OCRService
from app.core.exceptions import BaseAppException, ExternalServiceError, DatabaseError

import logging
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Main coordinator: OCR -> Gemini Parser -> Save JSON in Firebase
    """

    def __init__(self, ocr: OCRService, parser: GeminiParserService):
        self.ocr = ocr
        self.parser = parser
        self.key_gen = KeyGenerator()
        self.document_service = DocumentService()

    async def _extract_text(self, image_path: str) -> str:
        logger.info(f"Extracting text from: {image_path}")
        try:
            if str(image_path).startswith("http"):
                text = await self.ocr.extract_text_from_url_async(image_path)
            else:
                text = await self.ocr.extract_text_from_file_async(Path(image_path))

            logger.info(f"Text extraction complete. Length: {len(text) if text else 0}")

            if not text or not text.strip():
                logger.warning("No text extracted from document")
                raise BaseAppException(
                    "No text could be extracted from the document.",
                    status_code=400,
                    details={"reason": "empty_ocr"},
                )

            return text
        except BaseAppException:
            raise
        except Exception as e:
            logger.exception("OCR extraction failed")
            raise ExternalServiceError(
                "OCR extraction failed", service_name="ocr", original_error=e
            )

    async def _parse_text(self, ocr_text: str, image_ref: str, user_id: str = None) -> dict:
        logger.info("Parsing OCR text with parser service")
        try:
            parsed = await self.parser.parse_async(ocr_text, image_ref, user_id=user_id)
            logger.info("Parsing complete")
            return parsed
        except Exception as e:
            logger.exception("Parser service failed")
            raise ExternalServiceError(
                "Parser service failed", service_name="parser", original_error=e
            )

    async def _generate_document_key(
        self, parsed_data: dict, user_id: str, company_id: str
    ) -> str:
        try:
            return await self.key_gen.generate_key_async(
                parsed_data.get("document_type", "other"), user_id, company_id
            )
        except Exception:
            logger.exception("Key generation failed; using timestamp fallback")
            return f"DOC{int(datetime.utcnow().timestamp())}"

    async def _save_to_firebase(
        self, parsed_data: dict, user_id: str, company_id: str
    ) -> dict:
        logger.info("Saving parsed document to Firebase")
        try:
            result = await self.document_service.save_async(
                data=parsed_data, user_id=user_id, company_id=company_id
            )
            logger.info(f"Saved to Firebase with key: {result.get('document_key')}")
            return result
        except Exception as e:
            logger.exception("Firebase save failed")
            raise ExternalServiceError(
                "Failed to save document to Firebase",
                service_name="firebase",
                original_error=e,
            )

    async def process_image_async(
        self, 
        image_path: str, 
        user_id: str, 
        company_id: str, 
        image_url: str = None,
        file: UploadFile = None
    ) -> dict:
        """Process image or PDF asynchronously: OCR → Parser → Firebase save
        """
        try:
            # Prioritize direct file content if available to avoid redundant downloads/local reads
            if file:
                logger.info(f"Extracting text directly from uploaded file: {file.filename}")
                content = await file.read()
                ocr_text = await self.ocr.extract_text_from_bytes_async(content, file.filename)
                # Ensure we reset for any other potential consumers
                await file.seek(0)
            else:
                # Fallback to URL or local path
                source_path = image_url if image_url else image_path
                ocr_text = await self._extract_text(source_path)

            parsed_data = await self._parse_text(ocr_text, image_url or image_path, user_id=user_id)

            # Generate or fallback document key
            parsed_data["document_key"] = await self._generate_document_key(
                parsed_data, user_id, company_id
            )

            if image_url:
                parsed_data["image_url"] = image_url

            saved_result = await self._save_to_firebase(
                parsed_data, user_id, company_id
            )
            saved_result.pop("status")
            return saved_result
        except (BaseAppException, ExternalServiceError, DatabaseError):
            raise
        except Exception as e:
            logger.exception("Unexpected error in document processing")
            raise DatabaseError(
                f"Unexpected error processing document: {e}", operation="process_image"
            )
