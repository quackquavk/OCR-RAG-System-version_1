import asyncio
import os
import logging
from typing import Dict, Any, Optional

from app.infrastructure.firebase import TokenService, DocumentService
from app.use_cases.rag.document_indexer import get_document_indexer
from app.infrastructure.sheets import GoogleSheetsService
from app.infrastructure.oauth import GoogleOAuthService
from app.core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)

class DocumentSyncService:
    """
    Coordinates post-upload synchronization tasks:
    1. Indexing in Vector DB
    2. Syncing to Google Sheets
    """

    def __init__(self):
        self.token_service = TokenService()
        self.document_service = DocumentService()
        self.document_indexer = get_document_indexer()
        self.oauth_service = GoogleOAuthService()

    async def index_document(self, document_key: str, data: Dict[str, Any], user_id: str, company_id: str, image_url: str):
        """
        Indexes the document in the vector database.
        """
        logger.info(f"Background task: Indexing document {document_key}")
        try:
            full_data_copy = data.copy()
            full_data_copy["image_url"] = image_url
            full_data_copy["document_key"] = document_key
            full_data_copy["user_id"] = user_id
            full_data_copy["company_id"] = company_id
            
            await self.document_indexer.index_document_async(document_key, full_data_copy)
            logger.info(f"Successfully indexed document {document_key}")
        except Exception as e:
            logger.error(f"Failed to index document {document_key}: {e}", exc_info=True)


    async def sync_to_google_sheets(self, document_key: str, auto_category: str, company_name: str, user_id: str, company_id: str):
        """
        Syncs document data to the user's Google Sheet.
        Gracefully handles expired tokens by skipping sync.
        """
        logger.info(f"Background task: Syncing document {document_key} to Google Sheets for user {user_id}")
        try:
            # 1. Fetch tokens from Firebase
            tokens = await self.token_service.get_google_tokens_async(user_id, company_id)

            if not tokens:
                logger.info(f"User {user_id} hasn't connected Google Sheets for company {company_id}. Skipping sync.")
                return

            # 2. Token expiry check removed to allow auto-refresh via refresh_token


            # 3. Decrypt tokens
            access_token = self.oauth_service.decrypt_token(tokens.get("access_token"))
            refresh_token = self.oauth_service.decrypt_token(tokens.get("refresh_token"))

            if not access_token:
                logger.error(f"Failed to decrypt access token for user {user_id}")
                return

            # 4. Fetch data from Firebase
            firebase_data = await self.document_service.get_document_async(user_id, company_id, document_key)

            if not firebase_data:
                logger.warning(f"No data found for document {document_key} in Firebase")
                return

            # 5. Prepare data for sheets
            sheets_data = firebase_data.copy()
            if "document_key" not in sheets_data:
                sheets_data["document_key"] = document_key
            sheets_data.pop("image_url", None)

            # 6. Initialize Google Sheets Service
            oauth_credentials = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
                "token_uri": "https://oauth2.googleapis.com/token",
                "scopes": tokens.get("scopes", []),
            }

            user_sheets_service = GoogleSheetsService(
                spreadsheet_id=tokens.get("spreadsheet_id"),
                user_oauth_credentials=oauth_credentials,
            )

            # 7. Sync document
            await user_sheets_service.sync_document_async(
                sheets_data,
                user_category=None,
                auto_category=auto_category,
                company_name=company_name,
            )
            logger.info(f"Successfully synced document {document_key} to Google Sheet: {tokens.get('spreadsheet_name')}")

        except AuthenticationError as e:
            # Handle authentication errors gracefully (token revoked, expired, etc.)
            logger.warning(
                f"Authentication failed for user {user_id} when syncing document {document_key}. "
                f"Document saved to Firebase but not synced to Google Sheets. "
                f"User needs to reconnect Google Sheets. Error: {e}"
            )
        except Exception as e:
            logger.error(f"Error syncing document {document_key} to Google Sheets: {e}", exc_info=True)
