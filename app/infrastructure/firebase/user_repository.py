"""
Repository for user-related data access in Firestore.
"""

import logging
from typing import Optional

from .base import FirebaseBase

logger = logging.getLogger(__name__)

class FirestoreUserRepository(FirebaseBase):
    """
    Repository for accessing user settings and preferences.
    """

    async def get_groq_key(self, user_id: str) -> Optional[str]:
        """
        Retrieve the user's encrypted Groq API key from their settings.
        
        Args:
            user_id: The user's ID.
            
        Returns:
            The encrypted key string if found, None otherwise.
        """
        # Path: users/{user_id}/settings/groq_api_key
        path = f"users/{user_id}/settings/groq_api_key"
        
        try:
            ref = self.db.reference(path)
            # Use run_in_executor for blocking DB call
            encrypted_key = await self._run_in_executor(ref.get)
            return encrypted_key
        except Exception as e:
            logger.error(f"Failed to fetch Groq key for user {user_id}: {e}")
            return None
