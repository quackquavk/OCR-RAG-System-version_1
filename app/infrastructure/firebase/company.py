"""
Company-level operations for Firebase.
Handles company deletion and associated cleanup tasks.
"""

import logging
import os

from app.core.exceptions import DatabaseError
from .base import FirebaseBase

logger = logging.getLogger(__name__)


class CompanyService(FirebaseBase):
    """
    Service for company-level operations in Firebase.
    """

    FILE_KEYS = ("server_path", "path", "local_path", "file_path")

    async def delete_company_async(
        self, user_id: str, company_id: str, delete_local_files: bool = False
    ) -> None:
        base_path = self._get_base_path(user_id, company_id)
        docs_path = self._get_documents_path(user_id, company_id)

        try:
            if delete_local_files:
                await self._delete_company_files(docs_path)

            await self._delete_company_node(base_path)

            logger.info(f"Deleted company {company_id} for user {user_id}")

        except Exception as e:
            logger.error(f"Delete company failed for {company_id}: {e}")
            raise DatabaseError(
                f"Failed to delete company: {e}",
                operation="delete_company",
            )


    async def _delete_company_files(self, docs_path: str) -> None:
        ref = self.db.reference(docs_path)
        docs = await self._run_in_executor(ref.get) or {}

        if not isinstance(docs, dict):
            return

        for doc in docs.values():
            if isinstance(doc, dict):
                self._delete_files_from_doc(doc)

    def _delete_files_from_doc(self, doc: dict) -> None:
        for key in self.FILE_KEYS:
            path = doc.get(key)
            if not path:
                continue

            try:
                abs_path = path if os.path.isabs(path) else os.path.abspath(path)
                if os.path.exists(abs_path):
                    os.remove(abs_path)
                    logger.info(f"Removed file: {abs_path}")
            except Exception as e:
                logger.warning(f"Could not remove file {path}: {e}")

    async def _delete_company_node(self, base_path: str) -> None:
        ref = self.db.reference(base_path)
        await self._run_in_executor(ref.delete)
