"""
Document storage and retrieval operations for Firebase.
Manages document CRUD operations with user and company isolation.
"""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Dict

from app.core.exceptions import DatabaseError, NotFoundError
from .base import FirebaseBase

logger = logging.getLogger(__name__)


class DocumentService(FirebaseBase):
    """
    Service for document operations in Firebase Realtime Database.
    Handles saving, fetching, and managing document data.
    """

    async def save_async(
        self, data: Dict[str, Any], user_id: str, company_id: str
    ) -> Dict[str, Any]:
        """
        Save a document to Firebase.

        Args:
            data: Document data (must include 'document_key').
            user_id: User UID.
            company_id: Company ID.

        Returns:
            Dict containing save status and cleaned data.
        """
        if "document_key" not in data:
            raise ValueError("Data must include 'document_key'.")

        doc_key = data["document_key"]

        now_nepal = datetime.now(ZoneInfo("Asia/Kathmandu"))
        created_at = now_nepal.strftime("%d %B %Y at %I:%M:%S %p")

        payload = {
            **data,
            "created_at": created_at,
            "user_id": user_id,
            "company_id": company_id,
        }

        path = self._get_document_path(user_id, company_id, doc_key)

        try:
            doc_ref = self.db.reference(path)
            await self._run_in_executor(doc_ref.set, payload)

            logger.info(f"Saved document {doc_key} to {path}")

            return {
                "status": "saved",
                "document_key": doc_key,
                "created_at": created_at,
                "document_path": path,
                "full_data": self._clean_for_response(payload),
            }
        except Exception as e:
            logger.error(f"Firebase save failed for {doc_key}: {e}")
            raise DatabaseError(
                f"Failed to save document: {e}", operation="save_document"
            )

    async def get_all_async(self, user_id: str, company_id: str) -> Dict[str, Any]:
        """Fetch all documents for a company."""
        path = self._get_documents_path(user_id, company_id)
        try:
            ref = self.db.reference(path)
            docs = await self._run_in_executor(ref.get)
            return docs or {}
        except Exception as e:
            logger.error(f"Failed to fetch documents from {path}: {e}")
            raise DatabaseError(
                f"Failed to fetch all documents: {e}", operation="get_all_documents"
            )

    async def get_document_async(
        self, user_id: str, company_id: str, document_key: str
    ) -> Dict[str, Any]:
        """Fetch a single document."""
        path = self._get_document_path(user_id, company_id, document_key)
        try:
            ref = self.db.reference(path)
            doc = await self._run_in_executor(ref.get)
            if not doc:
                raise NotFoundError(
                    f"Document {document_key} not found", "Document", document_key
                )
            return doc
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch document {document_key}: {e}")
            raise DatabaseError(
                f"Failed to fetch document: {e}", operation="get_document"
            )

    async def delete_async(
        self, user_id: str, company_id: str, document_key: str
    ) -> bool:
        """
        Delete a document from Firebase.

        Args:
            user_id: User UID.
            company_id: Company ID.
            document_key: The key of the document to delete.

        Returns:
            True if successful, False otherwise.
        """
        path = self._get_document_path(user_id, company_id, document_key)
        try:
            ref = self.db.reference(path)
            await self._run_in_executor(ref.delete)
            logger.info(f"Deleted document {document_key} from {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {document_key} from {path}: {e}")
            raise DatabaseError(
                f"Failed to delete document: {e}", operation="delete_document"
            )
