"""
Google Sheets history tracking for Firebase.
Manages sheet creation history and metadata.
"""

import logging
from typing import Any, Dict, Optional, Union

from app.core.exceptions import DatabaseError
from .base import FirebaseBase

logger = logging.getLogger(__name__)


class SheetHistoryService(FirebaseBase):
    """
    Service for tracking Google Sheets history in Firebase.
    Maintains records of created sheets per user/company.
    """

    async def save_sheet_to_history_async(
        self, user_id: str, company_id: str, google_sub: str, sheet_info: Dict[str, Any]
    ) -> None:
        """Save a sheet to history."""
        sheet_id = sheet_info["spreadsheet_id"]
        # users/{uid}/companies/{cid}/sheet_history/{google_sub}/{sheet_id}
        path = f"{self._get_history_path(user_id, company_id)}/{google_sub}/{sheet_id}"

        try:
            ref = self.db.reference(path)
            await self._run_in_executor(ref.set, sheet_info)
        except Exception as e:
            raise DatabaseError(
                f"Failed to save sheet history: {e}", operation="save_sheet_history"
            )

    async def get_sheet_history_async(
        self, user_id: str, company_id: str, google_sub: Optional[str] = None
    ) -> Union[Dict[str, Any], None]:
        """Get sheet history, optionally filtered by google account."""
        path = self._get_history_path(user_id, company_id)
        if google_sub:
            path = f"{path}/{google_sub}"

        try:
            ref = self.db.reference(path)
            return await self._run_in_executor(ref.get)
        except Exception as e:
            raise DatabaseError(
                f"Failed to fetch sheet history: {e}", operation="get_sheet_history"
            )

    async def delete_sheet_from_history_async(
        self,
        user_id: str,
        company_id: str,
        spreadsheet_id: str,
        google_sub: Optional[str] = None,
    ) -> None:
        """Delete from history."""
        base_history_path = self._get_history_path(user_id, company_id)

        try:
            if google_sub:
                path = f"{base_history_path}/{google_sub}/{spreadsheet_id}"
                ref = self.db.reference(path)
                await self._run_in_executor(ref.delete)
            else:
                ref = self.db.reference(base_history_path)
                all_history = await self._run_in_executor(ref.get)

                if all_history:
                    for sub, sheets in all_history.items():
                        if isinstance(sheets, dict) and spreadsheet_id in sheets:
                            path = f"{base_history_path}/{sub}/{spreadsheet_id}"
                            del_ref = self.db.reference(path)
                            await self._run_in_executor(del_ref.delete)
                            break
        except Exception as e:
            raise DatabaseError(
                f"Failed to delete sheet history: {e}", operation="delete_sheet_history"
            )
