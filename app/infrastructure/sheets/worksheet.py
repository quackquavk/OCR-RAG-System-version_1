
"""
Worksheet management operations (Find, Create, Header Maintenance).
"""

import logging
import gspread
from typing import Optional, List, Any
from app.core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

class WorksheetManager:
    """
    Manages individual worksheets within a Google Spreadsheet.
    """

    def __init__(self, client: gspread.Client, spreadsheet: gspread.Spreadsheet):
        self.client = client
        self.spreadsheet = spreadsheet

    def get_or_create(self, title: str, is_bank_statement: bool = False, account_number: str = "Unknown") -> gspread.Worksheet:
        """
        Retrieves a worksheet by title (case-insensitive) or creates it if missing.
        """
        # 1. Try to find existing
        worksheet = self._find_worksheet(title)
        if worksheet:
            if is_bank_statement:
                self._ensure_bank_headers(worksheet)
            return worksheet

        # 2. Create new if not found
        return self._create_worksheet(title, is_bank_statement, account_number)

    def _find_worksheet(self, title: str) -> Optional[gspread.Worksheet]:
        """Case-insensitive search for a worksheet."""
        try:
            target_title = title.lower()
            for ws in self.spreadsheet.worksheets():
                if ws.title.lower() == target_title:
                    return ws
            return None
        except Exception as e:
            raise ExternalServiceError(f"Failed to list worksheets: {e}", "Google Sheets", e)

    def _create_worksheet(self, title: str, is_bank_statement: bool, account_number: str) -> gspread.Worksheet:
        """Creates a new worksheet with appropriate headers."""
        try:
            logger.info(f"Creating new worksheet: '{title}'")
            worksheet = self.spreadsheet.add_worksheet(title=title, rows=1000, cols=10)
            
            if is_bank_statement:
                # Bank Statement Headers
                worksheet.append_row([f"Account Number: {account_number}"])
                worksheet.append_row(["Date", "Description", "Debit", "Credit"])
            else:
                # Standard Headers
                worksheet.append_row(["Date", "Type", "Description", "Total Amount"])
            
            logger.info(f"Created worksheet '{title}' with headers.")
            return worksheet
        except Exception as e:
            # Handle possible race condition if sheet was created in parallel
            if "already exists" in str(e).lower():
                return self.spreadsheet.worksheet(title)
                
            raise ExternalServiceError(f"Error creating worksheet '{title}': {e}", "Google Sheets", e)

    def _ensure_bank_headers(self, worksheet: gspread.Worksheet) -> None:
        """
        Checks for legacy header formats in bank statements and fixes them.
        """
        try:
            all_values = worksheet.get_all_values()
            if not all_values:
                return 

            # Identify header row (Row 1 or Row 2)
            header_row_index = 0
            header_row = all_values[0]
            
            if len(all_values) > 1 and "Account Number" in str(header_row[0]):
                header_row_index = 1
                header_row = all_values[1]

            # Logic to detect "Wrong" headers (from old generic implementation)
            if len(header_row) >= 3 and "Type" in str(header_row) and "Total Amount" in str(header_row):
                 logger.warning("Detected outdated headers in Bank Statement. Fixing...")
                 row_num = header_row_index + 1
                 worksheet.update(
                     f"A{row_num}:D{row_num}",
                     [["Date", "Description", "Debit", "Credit"]]
                 )
                 logger.info("Headers updated successfully.")
        except Exception as e:
            logger.warning(f"Header check failed: {e}")

    def append_rows(self, worksheet: gspread.Worksheet, rows: List[List[Any]]) -> None:
        """Appends rows with error handling."""
        try:
            if rows:
                worksheet.append_rows(rows)
                logger.info(f"Appended {len(rows)} row(s) to '{worksheet.title}'.")
        except Exception as e:
            if "timeout" in str(e).lower():
                 raise ExternalServiceError("Timeout syncing to Google Sheets.", "Google Sheets", e)
            raise ExternalServiceError(f"Failed to append rows: {e}", "Google Sheets", e)
