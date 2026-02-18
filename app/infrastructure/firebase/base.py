"""
Base infrastructure for Firebase services.
Provides shared functionality and path builders.
"""

import asyncio
import logging
from typing import Any, Dict

from firebase_admin import db
from app.config.settings import init_firebase

logger = logging.getLogger(__name__)


class FirebaseBase:
    """
    Base class for Firebase services.
    Provides database initialization and shared utilities.
    """

    def __init__(self) -> None:
        self.db = init_firebase()

    # Path Helpers

    def _get_base_path(self, user_id: str, company_id: str) -> str:
        """Constructs the base path for a company."""
        return f"users/{user_id}/companies/{company_id}"

    def _get_documents_path(self, user_id: str, company_id: str) -> str:
        return f"{self._get_base_path(user_id, company_id)}/documents"

    def _get_document_path(
        self, user_id: str, company_id: str, document_key: str
    ) -> str:
        return f"{self._get_documents_path(user_id, company_id)}/{document_key}"

    def _get_tokens_path(self, user_id: str, company_id: str) -> str:
        return f"{self._get_base_path(user_id, company_id)}/google_tokens"

    def _get_history_path(self, user_id: str, company_id: str) -> str:
        return f"{self._get_base_path(user_id, company_id)}/sheet_history"

    # Internal Helpers

    def _clean_for_response(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove internal metadata before returning API response.
        """
        cleaned = payload.copy()
        remove_keys = {
            "business_path",
            "server_path",
            "status",
            "user_id",
        }
        for key in remove_keys:
            cleaned.pop(key, None)
        return cleaned

    async def _run_in_executor(self, func, *args):
        """Helper to run blocking DB calls in the default executor."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func, *args)
