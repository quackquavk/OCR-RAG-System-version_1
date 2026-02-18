
"""
Google Sheets Service Facade.
Exposes the simplified interface for syncing documents while hiding the complexity of
connection management, header maintenance, and row mapping.
"""

import asyncio
from typing import Optional, Dict, Any

from app.infrastructure.sheets.client import SheetsClient
from app.infrastructure.sheets.transaction_sync import TransactionSyncService

class GoogleSheetsService:
    """
    Facade for interacting with Google Sheets.
    Maintains backward compatibility with the previous API.
    """

    def __init__(
        self,
        credentials_file: str = "app/config/google_service_account.json",
        spreadsheet_id: str = "1aQsdIOl38P8Rr1uUSWAEtbBHrV-EAaja9KNkGL1fPT8",
        user_oauth_credentials: Optional[Dict[str, Any]] = None,
    ):
        # Initialize Client
        self.client = SheetsClient(credentials_file, spreadsheet_id, user_oauth_credentials)
        self.client.connect()
        
        # Initialize Sync Service with the connected client
        self.sync_service = TransactionSyncService(self.client)

    def sync_document(
        self,
        doc_data: dict,
        user_category: str = None,
        auto_category: str = None,
        company_name: str = None,
    ):
        """
        Synchronous entry point for document sync.
        """
        self.sync_service.sync(
            doc_data=doc_data,
            user_category=user_category,
            auto_category=auto_category,
            company_name=company_name
        )

    async def sync_document_async(
        self,
        doc_data: dict,
        user_category: str = None,
        auto_category: str = None,
        company_name: str = None,
    ):
        """
        Asynchronous wrapper for document sync.
        Runs the blocking sync operation in a separate thread.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.sync_document,
            doc_data,
            user_category,
            auto_category,
            company_name,
        )
