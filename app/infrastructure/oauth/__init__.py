
"""
Google OAuth Service Facade.
Maintains backward compatibility by exposing the consolidated GoogleOAuthService class.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from app.infrastructure.oauth.encryption import EncryptionService
from app.infrastructure.oauth.auth_flow import OAuthFlowService
from app.infrastructure.oauth.services import GoogleRemoteService

class GoogleOAuthService:
    """
    Facade class for Google OAuth 2.0 interactions.
    Delegates responsibility to specialized services:
    - EncryptionService: Token encryption/decryption
    - OAuthFlowService: Auth flow handling
    - GoogleRemoteService: API interactions
    """

    def __init__(self) -> None:
        self._encryption = EncryptionService()
        self._auth_flow = OAuthFlowService()
        self._remote_services = GoogleRemoteService()

    # --- Auth Flow Delegation ---

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Delegate URL generation."""
        return self._auth_flow.get_authorization_url(state)

    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Delegate token exchange."""
        return self._auth_flow.exchange_code_for_tokens(code)

    def refresh_access_token(self, refresh_token: str) -> Tuple[str, datetime]:
        """Delegate token refresh."""
        return self._auth_flow.refresh_access_token(refresh_token)

    # --- Encryption Delegation ---

    def encrypt_token(self, token: Optional[str]) -> Optional[str]:
        """Delegate encryption."""
        return self._encryption.encrypt_token(token)

    def decrypt_token(self, encrypted_token: Optional[str]) -> Optional[str]:
        """Delegate decryption."""
        return self._encryption.decrypt_token(encrypted_token)

    # --- Remote Service Delegation ---

    def get_user_spreadsheets(self, access_token: str) -> List[Dict[str, Any]]:
        """Delegate spreadsheet retrieval."""
        return self._remote_services.get_user_spreadsheets(access_token)

    def create_spreadsheet(self, access_token: str, title: str) -> Dict[str, str]:
        """Delegate spreadsheet creation."""
        return self._remote_services.create_spreadsheet(access_token, title)

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Delegate user info retrieval."""
        return self._remote_services.get_user_info(access_token)
