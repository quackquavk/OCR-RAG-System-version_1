import base64
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional

from app.infrastructure.oauth import GoogleOAuthService
from app.infrastructure.firebase import TokenService
from app.core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)

class OAuthOrchestrator:
    """
    Orchestrates the Google OAuth lifecycle:
    1. Authorization URL generation
    2. Code-to-token exchange
    3. Token health and refreshing
    4. Identity verification
    """

    def __init__(self):
        self.oauth_service = GoogleOAuthService()
        self.token_service = TokenService()

    def get_auth_url(self, user_id: str, company_id: str, company_name: str) -> str:
        """
        Generates the Google OAuth authorization URL with encoded state.
        """
        # Encode company name to base64 for safe transmission in the state parameter
        company_name_b64 = base64.urlsafe_b64encode(company_name.encode()).decode()
        state = f"{user_id}:{company_id}:{company_name_b64}"
        
        return self.oauth_service.get_authorization_url(state=state)

    def exchange_code(self, code: str) -> Dict[str, Any]:
        """
        Exchanges an authorization code for tokens.
        """
        return self.oauth_service.exchange_code_for_tokens(code)

    def get_user_identity(self, access_token: str) -> Dict[str, Any]:
        """
        Fetches the Google user info for a given access token.
        """
        return self.oauth_service.get_user_info(access_token)

    async def ensure_valid_token(self, user_id: str, company_id: str, tokens: Dict[str, Any]) -> str:
        """
        Checks if the access token is valid and refreshes it if necessary.
        Returns the valid (decrypted) access token.
        """
        expiry_str = tokens.get("token_expiry")
        if not expiry_str:
            return self.oauth_service.decrypt_token(tokens.get("access_token"))

        expiry_date = datetime.fromisoformat(expiry_str)
        if expiry_date < datetime.utcnow() + timedelta(minutes=5):
            logger.info(f"Refreshing expired token for user {user_id}")
            
            refresh_token_enc = tokens.get("refresh_token")
            if not refresh_token_enc:
                raise AuthenticationError("No refresh token available. Please reconnect Google Sheets.")

            refresh_token = self.oauth_service.decrypt_token(refresh_token_enc)
            new_access_token, new_expiry = self.oauth_service.refresh_access_token(refresh_token)

            tokens["access_token"] = self.oauth_service.encrypt_token(new_access_token)
            tokens["token_expiry"] = new_expiry.isoformat()
            
            await self.token_service.save_google_tokens_async(user_id, company_id, tokens)
            logger.info("Token refreshed and updated in Firebase.")
            
            return new_access_token

        return self.oauth_service.decrypt_token(tokens.get("access_token"))

    def parse_state(self, state: str) -> Tuple[str, str, str]:
        """
        Parses the OAuth state parameter back into its components.
        """
        if not state or ":" not in state:
            raise ValueError("Invalid state parameter")

        parts = state.split(":")
        user_id = parts[0]
        company_id = parts[1]
        
        company_name = "Company"
        if len(parts) >= 3:
            try:
                company_name = base64.urlsafe_b64decode(parts[2]).decode()
            except Exception:
                logger.warning("Failed to decode company name from state")

        return user_id, company_id, company_name
