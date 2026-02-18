"""
Atomic counter operations for Firebase.
Provides thread-safe counter increments using transactions.
"""

import logging

from app.core.exceptions import DatabaseError
from .base import FirebaseBase

logger = logging.getLogger(__name__)


class CounterService(FirebaseBase):
    """
    Service for atomic counter operations in Firebase.
    Ensures thread-safe increments for document and sheet numbering.
    """

    async def _increment_counter(self, path: str) -> int:
        """Atomic increment helper."""

        def transaction_func(current_value):
            return 1 if current_value is None else current_value + 1

        ref = self.db.reference(path)
        try:
            # transaction is blocking, run in executor
            return await self._run_in_executor(
                lambda: ref.transaction(transaction_func)
            )
        except Exception as e:
            raise DatabaseError(
                f"Counter increment failed at {path}: {e}",
                operation="increment_counter",
            )

    async def get_next_sheet_number_async(self, user_id: str, company_id: str) -> int:
        """Get the next sheet number for a company."""
        path = f"{self._get_base_path(user_id, company_id)}/sheet_counter"
        return await self._increment_counter(path)

    async def get_next_document_number_async(
        self, user_id: str, company_id: str, doc_prefix: str
    ) -> int:
        """Get the next document number for a specific document type."""
        path = f"{self._get_base_path(user_id, company_id)}/counters/{doc_prefix}"
        return await self._increment_counter(path)
