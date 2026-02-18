import logging
from typing import Dict, Any, Optional, Tuple

from app.infrastructure.firebase import DocumentService
from app.utils.firebase_to_csv import FirebaseToCSV
from app.utils.excel_templates import ExcelTemplateFactory

logger = logging.getLogger(__name__)

class ExportService:
    """
    Handles document exports to various formats (CSV, Excel).
    Encapsulates data cleaning and utility coordination.
    """

    EXCLUDE_FIELDS = [
        "company_id",
        "image_url",
        "document_key",
        "user_id",
        "created_at",
        "document_type",
    ]

    def __init__(self):
        # self.document_service = DocumentService()
        self.csv_util = FirebaseToCSV()
        self.firebase_service = DocumentService()

    async def generate_csv(self, user_id: str, company_id: str, doc_id: str) -> Dict[str, str]:
        """
        Fetches document data and generates a flattened CSV.
        """
        data = await self.firebase_service.get_document_async(user_id, company_id, doc_id)
        
        flattened_rows = self.csv_util.flatten_for_csv(data)
        csv_text = self.csv_util.generate_csv_from_rows(flattened_rows, exclude_fields=self.EXCLUDE_FIELDS)
        
        return {
            "doc_id": doc_id, 
            "csv": csv_text, 
            "filename": f"{doc_id}.csv"
        }

    async def generate_excel(self, user_id: str, company_id: str, doc_id: str) -> Tuple[bytes, str]:
        """
        Fetches document data and generates a formatted Excel file.
        Returns a tuple of (excel_bytes, filename).
        """
        data = await self.firebase_service.get_document_async(user_id, company_id, doc_id)
        
        clean_data = {k: v for k, v in data.items() if k not in self.EXCLUDE_FIELDS}
        if "document_type" in data:
            clean_data["document_type"] = data["document_type"]

        excel_bytes = ExcelTemplateFactory.generate_excel(clean_data)
        
        doc_type = data.get("document_type", "document")
        filename = f"{doc_type}_{doc_id}.xlsx"
        
        return excel_bytes, filename

