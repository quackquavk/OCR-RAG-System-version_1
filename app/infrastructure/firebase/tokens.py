"""
Google OAuth token management for Firebase.
Handles encrypted token storage, retrieval, and disconnection.
"""

import logging
from typing import Any, Dict, Optional

from app.core.exceptions import DatabaseError
from .base import FirebaseBase

logger = logging.getLogger(__name__)


class TokenService(FirebaseBase):
    """
    Service for managing Google OAuth tokens in Firebase.
    Handles secure token storage and retrieval operations.
    """

    async def save_google_tokens_async(
        self, user_id: str, company_id: str, tokens: Dict[str, Any]
    ) -> None:
        """Save encrypted Google tokens."""
        path = self._get_tokens_path(user_id, company_id)
        try:
            ref = self.db.reference(path)
            await self._run_in_executor(ref.set, tokens)
        except Exception as e:
            logger.error(f"Failed to save tokens to {path}: {e}")
            raise DatabaseError(
                f"Failed to save Google tokens: {e}", operation="save_tokens"
            )

    async def get_google_tokens_async(
        self, user_id: str, company_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve encrypted Google tokens."""
        path = self._get_tokens_path(user_id, company_id)
        try:
            ref = self.db.reference(path)
            return await self._run_in_executor(ref.get)
        except Exception as e:
            logger.error(f"Failed to get tokens from {path}: {e}")
            raise DatabaseError(
                f"Failed to fetch Google tokens: {e}", operation="get_tokens"
            )

    async def disconnect_google_tokens_async(
        self, user_id: str, company_id: str
    ) -> None:
        """Disconnect Google integration (delete tokens)."""
        path = self._get_tokens_path(user_id, company_id)
        try:
            ref = self.db.reference(path)
            await self._run_in_executor(ref.delete)
            logger.info(f"Disconnected Google tokens for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to disconnect tokens at {path}: {e}")
            raise DatabaseError(
                f"Failed to disconnect Google tokens: {e}",
                operation="disconnect_tokens",
            )
