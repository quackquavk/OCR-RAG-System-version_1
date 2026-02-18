
"""
Orchestrates the synchronization of documents to Google Sheets.
Connects the RowMapper and WorksheetManager.
"""

import logging
from typing import Dict, Any, Optional

from app.infrastructure.sheets.client import SheetsClient
from app.infrastructure.sheets.worksheet import WorksheetManager
from app.infrastructure.sheets.row_mapper import RowMapper
from app.core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

class TransactionSyncService:
    """
    Service to decide where and how to sync a document.
    """

    def __init__(self, client: SheetsClient):
        self.client_manager = client
        self.row_mapper = RowMapper()

    def sync(
        self,
        doc_data: Dict[str, Any],
        user_category: Optional[str] = None,
        auto_category: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> None:
        """
        Main entry point for syncing a document.
        """
        try:
            # 1. Ensure connection
            spreadsheet = self.client_manager.sheet
            if not spreadsheet:
                # Attempt to reconnect if session lost (or just fail if not initialized)
                spreadsheet = self.client_manager.connect()
                
            if not spreadsheet:
                 raise ExternalServiceError("No active Google Sheets connection.", "Google Sheets")

            # 2. Determine document type and target sheet
            actual_doc_type = doc_data.get("document_type", "other").lower()
            is_bank_statement = "bank" in actual_doc_type and "statement" in actual_doc_type
            
            target_sheet_name = self._determine_sheet_name(
                actual_doc_type, user_category, auto_category, is_bank_statement, doc_data
            )
            
            logger.info(f"Syncing document type '{actual_doc_type}' to Sheet '{target_sheet_name}'")

            # 3. Get Worksheet
            ws_manager = WorksheetManager(self.client_manager.client, spreadsheet)
            account_number = doc_data.get("account_number", "Unknown") if is_bank_statement else ""
            
            worksheet = ws_manager.get_or_create(
                title=target_sheet_name,
                is_bank_statement=is_bank_statement,
                account_number=account_number
            )

            # 4. Map Data
            rows = self.row_mapper.map_document_to_rows(doc_data, actual_doc_type, target_sheet_name)

            # 5. Write Data
            ws_manager.append_rows(worksheet, rows)

        except Exception as e:
            logger.error(f"Sync failed: {e}", exc_info=True)
            raise

    def _determine_sheet_name(
        self, 
        doc_type: str, 
        user_category: Optional[str], 
        auto_category: Optional[str], 
        is_bank_statement: bool,
        doc_data: Dict
    ) -> str:
        """Logic to determine which sheet to write to."""
        if is_bank_statement:
            account_num = doc_data.get("account_number", "Unknown")
            return f"Bank Statement ({account_num})"

        # Priority: Auto -> User -> Type
        category = auto_category or user_category
        
        if category:
            if category.lower() == "purchase":
                return "Purchase"
            elif category.lower() == "sale":
                return "Sales"
            
        # Fallback to doc type
        if "invoice" in doc_type:
            return "Sales"
        if "receipt" in doc_type:
            return "Purchase"
            
        return "Other"
