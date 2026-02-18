
"""
Google Sheets Authentication and Client Management.
"""

import os
import logging
import gspread
from typing import Optional, Dict, Any
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as OAuthCredentials
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.exceptions import ExternalServiceError, AuthenticationError

logger = logging.getLogger(__name__)

class SheetsClient:
    """
    Handles authentication and connection to Google Sheets.
    Supports both Service Account and User OAuth credentials.
    """

    def __init__(
        self,
        credentials_file: str = "app/config/google_service_account.json",
        spreadsheet_id: str = "1aQsdIOl38P8Rr1uUSWAEtbBHrV-EAaja9KNkGL1fPT8",
        user_oauth_credentials: Optional[Dict[str, Any]] = None,
    ):
        self.spreadsheet_id = spreadsheet_id
        self._credentials_file = credentials_file
        self._user_credentials = user_oauth_credentials
        self.client: Optional[gspread.Client] = None
        self.sheet: Optional[gspread.Spreadsheet] = None

    def connect(self) -> gspread.Spreadsheet:
        """
        Establishes connection to the Google Sheet.
        """
        default_scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
        ]

        try:
            if self._user_credentials:
                creds = self._get_oauth_credentials(default_scopes)
                logger.info("Using user OAuth credentials.")
            else:
                # Check for environment variable first (JSON string)
                gcloud_json = os.getenv("GOOGLE_CLOUD_CREDENTIALS_JSON")
                if gcloud_json:
                    logger.info("Using google cloud credentials from GOOGLE_CLOUD_CREDENTIALS_JSON")
                    import json
                    cred_dict = json.loads(gcloud_json)
                    creds = ServiceAccountCredentials.from_service_account_info(
                        cred_dict, scopes=default_scopes
                    )
                else:
                    logger.info(f"Using service account credentials from file: {self._credentials_file}")
                    creds = ServiceAccountCredentials.from_service_account_file(
                        self._credentials_file, scopes=default_scopes
                    )

            self.client = self._authorize_client(creds)
            self.sheet = self.client.open_by_key(self.spreadsheet_id)
            
            logger.info(f"Connected to Google Sheet: {self.sheet.title}")
            return self.sheet

        except Exception as e:
            self._handle_connection_error(e)

    def _get_oauth_credentials(self, default_scopes: list) -> OAuthCredentials:
        """Constructs OAuth credentials from dictionary."""
        all_scopes = self._user_credentials.get("scopes", default_scopes)
        user_scopes = [
            scope for scope in all_scopes
            if "spreadsheets" in scope or "drive" in scope
        ]
        if not user_scopes:
            user_scopes = default_scopes

        return OAuthCredentials(
            token=self._user_credentials.get("access_token"),
            refresh_token=self._user_credentials.get("refresh_token"),
            token_uri=self._user_credentials.get("token_uri") or os.getenv("GOOGLE_OAUTH_TOKEN_URI", "https://oauth2.googleapis.com/token"),
            client_id=self._user_credentials.get("client_id") or os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
            client_secret=self._user_credentials.get("client_secret") or os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
            scopes=user_scopes,
        )

    def _authorize_client(self, creds) -> gspread.Client:
        """Authorizes and configures the gspread client with retry logic."""
        retry_strategy = Retry(
            total=10,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)

        client = gspread.authorize(creds)

        # Configure timeout and retry strategy
        if hasattr(client, "http_client"):
            client.http_client.timeout = 30
            if hasattr(client.http_client, "session"):
                client.http_client.session.mount("https://", adapter)
                client.http_client.session.mount("http://", adapter)
        
        return client

    def _handle_connection_error(self, e: Exception):
        """Standardizes error handling for connection issues."""
        if "invalid_grant" in str(e) or "unauthorized" in str(e).lower():
            raise AuthenticationError(f"Failed to authenticate with Google Sheets: {e}")
        
        raise ExternalServiceError(
            message=f"Failed to connect to Google Sheets: {e}",
            service_name="Google Sheets",
            original_error=e,
        )
