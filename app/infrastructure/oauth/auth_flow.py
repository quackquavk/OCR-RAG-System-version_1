
"""
OAuth 2.0 Flow handler for Google Services.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from app.core.exceptions import ConfigurationError, ExternalServiceError

logger = logging.getLogger(__name__)

# Constants
AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"

SCOPES: List[str] = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

class OAuthFlowService:
    """
    Handles the OAuth 2.0 authentication flow (URL generation, code exchange, refresh).
    """

    def __init__(self) -> None:
        self._client_id: Optional[str] = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
        self._client_secret: Optional[str] = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
        self._redirect_uri: Optional[str] = os.getenv('GOOGLE_OAUTH_REDIRECT_URI')

        if not self._client_id or not self._client_secret:
            logger.warning(
                "Google OAuth credentials missing (GOOGLE_OAUTH_CLIENT_ID/SECRET). "
                "OAuth features will be disabled."
            )

    @property
    def _client_config(self) -> Dict[str, Any]:
        """Constructs the client configuration dictionary for OAuth Flow."""
        if not self._client_id or not self._client_secret:
            raise ConfigurationError("OAuth credentials not found", config_key="GOOGLE_OAUTH_CLIENT_ID")
            
        return {
            "web": {
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "auth_uri": AUTH_URI,
                "token_uri": TOKEN_URI,
                "redirect_uris": [self._redirect_uri] if self._redirect_uri else []
            }
        }

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate the OAuth 2.0 authorization URL.
        """
        try:
            flow = Flow.from_client_config(
                self._client_config,
                scopes=SCOPES,
                redirect_uri=self._redirect_uri
            )
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent',
                state=state
            )
            
            logger.info("Generated OAuth authorization URL.")
            return auth_url
            
        except ConfigurationError:
            raise
        except Exception as e:
            raise ExternalServiceError(
                f"Failed to generate auth URL: {e}", 
                service_name="GoogleOAuth"
            )

    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.
        """
        try:
            flow = Flow.from_client_config(
                self._client_config,
                scopes=SCOPES,
                redirect_uri=self._redirect_uri
            )
            
            flow.fetch_token(code=code)
            creds = flow.credentials
            
            # expiry_timestamp = (
            #     creds.expiry.timestamp() 
            #     if creds.expiry 
            #     else (datetime.utcnow() + timedelta(hours=1)).timestamp()
            # )
            
            # expiry_date = datetime.utcnow() + timedelta(seconds=expiry_timestamp - datetime.utcnow().timestamp())
            expiry_date = creds.expiry or (datetime.utcnow() + timedelta(hours=1))

            logger.info("Successfully exchanged code for tokens.")
            return {
                'access_token': creds.token,
                'refresh_token': creds.refresh_token,
                'token_expiry': expiry_date,
                'scopes': creds.scopes
            }
        except Exception as e:
            raise ExternalServiceError(
                f"Token exchange failed: {e}", 
                service_name="GoogleOAuth",
                original_error=e
            )

    def refresh_access_token(self, refresh_token: str) -> Tuple[str, datetime]:
        """
        Refresh an expired access token.
        """
        try:
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri=TOKEN_URI,
                client_id=self._client_id,
                client_secret=self._client_secret,
                scopes=SCOPES
            )
            
            creds.refresh(Request())
            
            new_token = creds.token
            new_expiry = creds.expiry or (datetime.utcnow() + timedelta(hours=1))

            logger.info("Successfully refreshed access token.")
            return new_token, new_expiry
            
        except Exception as e:
            raise ExternalServiceError(
                f"Token refresh failed: {e}", 
                service_name="GoogleOAuth",
                original_error=e
            )
