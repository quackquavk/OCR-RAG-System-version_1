import logging
from io import BytesIO
from typing import Optional, Dict, Any
from PIL import Image

try:
    from pdf2image import convert_from_bytes
    PDF_READY = True
except ImportError:
    PDF_READY = False

from app.infrastructure.ocr.tesseract_service import OCRService
from app.infrastructure.parser.gemini_parser_service import GeminiParserService
from app.presentation.schemas.parsed_data_model import ParsedData

logger = logging.getLogger(__name__)

class AnonymousProcessor:
    """
    Handles standalone document processing (OCR + AI parsing) without persistence.
    """

    def __init__(self, ocr_service: Optional[OCRService] = None, parser_service: Optional[GeminiParserService] = None):
        self.ocr_service = ocr_service or OCRService()
        self.parser_service = parser_service or GeminiParserService()

    async def process_document(self, content: bytes, filename: str) -> ParsedData:
        """
        Takes raw file bytes and extracts structured data.
        """
        filename_lower = filename.lower()
        ocr_text = ""

        # 1. Extract Text (OCR)
        if filename_lower.endswith(".pdf"):
            ocr_text = await self._process_pdf(content)
        else:
            ocr_text = await self._process_image(content)

        if not ocr_text or len(ocr_text.strip()) < 5:
            raise ValueError("No readable text found in document")

        # 2. Parse with AI
        parsed_result = await self.parser_service.parse_async(ocr_text)
        
        # 3. Map to pydantic model
        return ParsedData(
            document_type=parsed_result.get("document_type", "other"),
            total_amount=parsed_result.get("total_amount"),
            date=parsed_result.get("date"),
            vendor_name=parsed_result.get("vendor_name"),
            customer_name=parsed_result.get("customer_name"),
            account_number=parsed_result.get("account_number"),
            line_items=parsed_result.get("line_items") or parsed_result.get("items"),
            transactions=parsed_result.get("transactions"),
            raw_text_length=len(ocr_text)
        )

    async def _process_pdf(self, content: bytes) -> str:
        if not PDF_READY:
            raise RuntimeError("PDF processing dependencies not installed")
        
        try:
            images = convert_from_bytes(content)
            text_parts = []
            for i, img in enumerate(images):
                page_text = self.ocr_service._process_single_image(img)
                if page_text:
                    text_parts.append(f"--- Page {i+1} ---\n{page_text}")
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"PDF OCR failed: {e}")
            raise ValueError(f"PDF processing failed: {str(e)}")

    async def _process_image(self, content: bytes) -> str:
        try:
            img = Image.open(BytesIO(content))
            return self.ocr_service._process_single_image(img, raw_bytes=content)
        except Exception as e:
            logger.error(f"Image OCR failed: {e}")
            raise ValueError(f"Image processing failed: {str(e)}")
