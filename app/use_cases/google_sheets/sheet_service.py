import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.infrastructure.firebase import TokenService, SheetHistoryService, CounterService
from .oauth_orchestrator import OAuthOrchestrator

logger = logging.getLogger(__name__)

class SheetService:
    """
    Manages active Google Sheets, historical sheets, and new sheet creation.
    Encapsulates all logic for determining connection status and handling 
    spreadsheet switches.
    """

    def __init__(self, oauth_orchestrator: OAuthOrchestrator):
        self.token_service = TokenService()
        self.sheet_history_service = SheetHistoryService()
        self.counter_service = CounterService()
        self.oauth_orchestrator = oauth_orchestrator

    async def get_connection_status(self, user_id: str, company_id: str) -> Dict[str, Any]:
        """
        Retrieves the connection status, active sheet info, and history for a user/company.
        """
        tokens = await self.token_service.get_google_tokens_async(user_id, company_id)

        if not tokens or not tokens.get("access_token"):
            return {"connected": False}

        # Format history list
        history = await self.sheet_history_service.get_sheet_history_async(user_id, company_id)
        history_list = []
        if history:
            for _, sheets in history.items():
                if isinstance(sheets, dict):
                    for _, s_info in sheets.items():
                        history_list.append(s_info)

        return {
            "connected": True,
            "spreadsheet_name": tokens.get("spreadsheet_name", "Google Sheet"),
            "spreadsheet_id": tokens.get("spreadsheet_id"),
            "spreadsheet_url": tokens.get("spreadsheet_url"),
            "history": history_list,
        }

    async def switch_active_sheet(self, user_id: str, company_id: str, spreadsheet_id: str) -> str:
        """
        Switches the active spreadsheet to one from the user's history.
        """
        tokens = await self.token_service.get_google_tokens_async(user_id, company_id)
        if not tokens or not tokens.get("access_token"):
            raise ValueError("Not connected to Google Sheets")

        history = await self.sheet_history_service.get_sheet_history_async(user_id, company_id)
        
        found_sheet = None
        if history:
            for _, sheets in history.items():
                if isinstance(sheets, dict) and spreadsheet_id in sheets:
                    found_sheet = sheets[spreadsheet_id]
                    break

        if not found_sheet:
            raise ValueError("Sheet not found in history")

        # Update active token data
        tokens.update({
            "spreadsheet_id": found_sheet["spreadsheet_id"],
            "spreadsheet_name": found_sheet["spreadsheet_name"],
            "spreadsheet_url": found_sheet["spreadsheet_url"]
        })

        await self.token_service.save_google_tokens_async(user_id, company_id, tokens)
        return found_sheet["spreadsheet_name"]

    async def create_new_sheet(self, user_id: str, company_id: str, company_name: str) -> str:
        """
        Creates a new Google Sheet, updates active tokens, and saves to history.
        """
        tokens = await self.token_service.get_google_tokens_async(user_id, company_id)
        if not tokens or not tokens.get("access_token"):
            raise ValueError("Not connected to Google Sheets")

        # 1. Ensure we have a valid access token
        access_token = await self.oauth_orchestrator.ensure_valid_token(user_id, company_id, tokens)

        # 2. Fetch Google Identity for history tracking
        user_info = self.oauth_orchestrator.get_user_identity(access_token)
        google_sub = user_info["id"]

        # 3. Generate name and create spreadsheet via OAuth service
        sheet_number = await self.counter_service.get_next_sheet_number_async(user_id, company_id)
        sheet_name = f"Receipt AI - {company_name} {sheet_number}"

        new_sheet = self.oauth_orchestrator.oauth_service.create_spreadsheet(access_token, sheet_name)
        new_sheet["created_at"] = datetime.utcnow().isoformat()

        # 4. Update active tokens and history
        tokens.update({
            "spreadsheet_id": new_sheet["spreadsheet_id"],
            "spreadsheet_name": new_sheet["spreadsheet_name"],
            "spreadsheet_url": new_sheet["spreadsheet_url"],
        })

        await self.token_service.save_google_tokens_async(user_id, company_id, tokens)
        await self.sheet_history_service.save_sheet_to_history_async(user_id, company_id, google_sub, new_sheet)

        return sheet_name

    async def delete_sheet(self, user_id: str, company_id: str, spreadsheet_id: str):
        """
        Deletes a spreadsheet from history and clears if active.
        """
        tokens = await self.token_service.get_google_tokens_async(user_id, company_id)
        if not tokens:
            return

        google_sub = tokens.get("google_sub")

        # Delete from history
        await self.sheet_history_service.delete_sheet_from_history_async(
            user_id, company_id, spreadsheet_id, google_sub
        )

        # Clear active if it matches
        if tokens.get("spreadsheet_id") == spreadsheet_id:
            tokens.update({
                "spreadsheet_id": None,
                "spreadsheet_name": None,
                "spreadsheet_url": None
            })
            await self.token_service.save_google_tokens_async(user_id, company_id, tokens)
