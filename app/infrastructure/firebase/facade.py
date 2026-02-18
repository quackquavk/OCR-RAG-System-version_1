"""
Unified facade for Firebase services.
Maintains backward compatibility by composing all specialized services.
"""

import logging
from typing import Any, Dict, Optional, Union

from .base import FirebaseBase
from .documents import DocumentService
from .tokens import TokenService
from .sheet_history import SheetHistoryService
from .counters import CounterService
from .company import CompanyService

logger = logging.getLogger(__name__)


class FirebaseService(FirebaseBase):
    """
    Service for Firebase Realtime Database operations.
    Enforces user and company isolation for all data access.
    
    This class acts as a facade, composing specialized services
    while maintaining the original public API for backward compatibility.
    """

    def __init__(self) -> None:
        super().__init__()
        
        self._documents = DocumentService()
        self._tokens = TokenService()
        self._sheet_history = SheetHistoryService()
        self._counters = CounterService()
        self._company = CompanyService()

    # Document Operations - Delegated to DocumentService

    async def save_async(
        self, data: Dict[str, Any], user_id: str, company_id: str
    ) -> Dict[str, Any]:
        """Save a document to Firebase."""
        return await self._documents.save_async(data, user_id, company_id)

    async def get_all_async(self, user_id: str, company_id: str) -> Dict[str, Any]:
        """Fetch all documents for a company."""
        return await self._documents.get_all_async(user_id, company_id)

    async def get_document_async(
        self, user_id: str, company_id: str, document_key: str
    ) -> Dict[str, Any]:
        """Fetch a single document."""
        return await self._documents.get_document_async(user_id, company_id, document_key)

    # Google Token Operations - Delegated to TokenService

    async def save_google_tokens_async(
        self, user_id: str, company_id: str, tokens: Dict[str, Any]
    ) -> None:
        """Save encrypted Google tokens."""
        return await self._tokens.save_google_tokens_async(user_id, company_id, tokens)

    async def get_google_tokens_async(
        self, user_id: str, company_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve encrypted Google tokens."""
        return await self._tokens.get_google_tokens_async(user_id, company_id)

    async def disconnect_google_tokens_async(
        self, user_id: str, company_id: str
    ) -> None:
        """Disconnect Google integration (delete tokens)."""
        return await self._tokens.disconnect_google_tokens_async(user_id, company_id)

    # Sheet History Operations - Delegated to SheetHistoryService

    async def save_sheet_to_history_async(
        self, user_id: str, company_id: str, google_sub: str, sheet_info: Dict[str, Any]
    ) -> None:
        """Save a sheet to history."""
        return await self._sheet_history.save_sheet_to_history_async(
            user_id, company_id, google_sub, sheet_info
        )

    async def get_sheet_history_async(
        self, user_id: str, company_id: str, google_sub: Optional[str] = None
    ) -> Union[Dict[str, Any], None]:
        """Get sheet history, optionally filtered by google account."""
        return await self._sheet_history.get_sheet_history_async(
            user_id, company_id, google_sub
        )

    async def delete_sheet_from_history_async(
        self,
        user_id: str,
        company_id: str,
        spreadsheet_id: str,
        google_sub: Optional[str] = None,
    ) -> None:
        """Delete from history."""
        return await self._sheet_history.delete_sheet_from_history_async(
            user_id, company_id, spreadsheet_id, google_sub
        )

    # Counter Operations - Delegated to CounterService

    async def get_next_sheet_number_async(self, user_id: str, company_id: str) -> int:
        """Get the next sheet number for a company."""
        return await self._counters.get_next_sheet_number_async(user_id, company_id)

    async def get_next_document_number_async(
        self, user_id: str, company_id: str, doc_prefix: str
    ) -> int:
        """Get the next document number for a specific document type."""
        return await self._counters.get_next_document_number_async(
            user_id, company_id, doc_prefix
        )

    # Company Operations - Delegated to CompanyService

    async def delete_company_async(
        self, user_id: str, company_id: str, delete_local_files: bool = False
    ) -> None:
        """Simple company deletion with optional file cleanup."""
        return await self._company.delete_company_async(
            user_id, company_id, delete_local_files
        )
