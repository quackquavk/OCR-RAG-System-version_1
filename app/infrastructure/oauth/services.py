
"""
Interactions with Google Remote APIs (Drive, Sheets, UserInfo).
"""

import logging
from typing import Dict, List, Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

from app.core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

SHEET_TITLES: List[str] = ['Purchase', 'Sales', 'Other']

SHEET_HEADERS: List[str] = [
    'Date',
    'Type',
    'Description',
    'Total Amount'
]

class GoogleRemoteService:
    """
    Handles interactions with Google Drive, Sheets, and UserInfo APIs.
    """

    def _get_authenticated_service(self, service_name: str, version: str, access_token: str) -> Resource:
        """Helper to build an authenticated Google API service."""
        try:
            creds = Credentials(token=access_token)
            return build(service_name, version, credentials=creds)
        except Exception as e:
            raise ExternalServiceError(
                f"Failed to build {service_name} service: {e}", 
                service_name=f"Google{service_name.capitalize()}"
            )

    def get_user_spreadsheets(self, access_token: str) -> List[Dict[str, Any]]:
        """
        Retrieve a list of spreadsheets owned by the user.
        """
        try:
            service = self._get_authenticated_service('drive', 'v3', access_token)
            
            results = service.files().list(
                q="mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
                pageSize=50,
                fields="files(id, name, createdTime)"
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"Retrieved {len(files)} spreadsheets.")
            
            return [
                {
                    'id': f['id'], 
                    'name': f['name'], 
                    'created': f.get('createdTime')
                } for f in files
            ]
        except HttpError as e:
            raise ExternalServiceError(
                f"Drive API error: {e}", 
                service_name="GoogleDrive", 
                original_error=e
            )

    def create_spreadsheet(self, access_token: str, title: str) -> Dict[str, str]:
        """
        Creates a new formatted spreadsheet with predefined sheets and headers.
        """
        try:
            service = self._get_authenticated_service('sheets', 'v4', access_token)
            
            # 1. Create the spreadsheet structure
            spreadsheet_body = {
                'properties': {'title': title},
                'sheets': [{'properties': {'title': name}} for name in SHEET_TITLES]
            }
            
            spreadsheet = service.spreadsheets().create(body=spreadsheet_body).execute()
            spreadsheet_id = spreadsheet['spreadsheetId']
            
            # 2. Add headers to all sheets
            self._add_headers(service, spreadsheet, spreadsheet_id)
            
            logger.info(f"Created spreadsheet: {title} ({spreadsheet_id})")
            return {
                'spreadsheet_id': spreadsheet_id,
                'spreadsheet_url': spreadsheet['spreadsheetUrl'],
                'spreadsheet_name': title
            }
        except HttpError as e:
            raise ExternalServiceError(
                f"Sheets API Create Error: {e}", 
                service_name="GoogleSheets", 
                original_error=e
            )

    def _add_headers(self, service: Resource, spreadsheet: Dict[str, Any], spreadsheet_id: str) -> None:
        """Helper to batch update headers for all sheets."""
        requests = []
        
        # Map sheet titles to their IDs
        sheet_ids = {
            s['properties']['title']: s['properties']['sheetId'] 
            for s in spreadsheet['sheets']
        }

        # Create Header Row Data
        header_row_data = {
            'values': [
                {'userEnteredValue': {'stringValue': h}} for h in SHEET_HEADERS
            ]
        }

        for title in SHEET_TITLES:
            if title in sheet_ids:
                requests.append({
                    'appendCells': {
                        'sheetId': sheet_ids[title],
                        'rows': [header_row_data],
                        'fields': 'userEnteredValue'
                    }
                })
        
        if requests:
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user profile info."""
        try:
            service = self._get_authenticated_service('oauth2', 'v2', access_token)
            return service.userinfo().get().execute()
        except HttpError as e:
            raise ExternalServiceError(
                f"UserInfo API error: {e}", 
                service_name="GoogleAuth", 
                original_error=e
            )
