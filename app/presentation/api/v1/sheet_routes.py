from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from app.presentation.auth_middleware import get_current_user
from app.use_cases.google_sheets.oauth_orchestrator import OAuthOrchestrator
from app.use_cases.google_sheets.sheet_service import SheetService
from app.infrastructure.firebase import TokenService, SheetHistoryService, CounterService
from app.core.exceptions import AuthenticationError, ExternalServiceError

from dotenv import load_dotenv

import os
import logging
logger = logging.getLogger(__name__)
load_dotenv()

router = APIRouter(prefix="/api/sheets", tags=["Sheets"])

oauth_orchestrator = OAuthOrchestrator()
sheet_service = SheetService(oauth_orchestrator)
token_service = TokenService()
sheet_history_service = SheetHistoryService()
counter_service = CounterService()

UPLOAD_PAGE_URL = os.getenv("UPLOAD_PAGE_URL")
SHEETS_PAGE_URL = os.getenv("SHEETS_PAGE_URL")

@router.get("/status")
async def get_sheets_status(current_user: dict = Depends(get_current_user)):
    """Check connection status and return active sheet + history"""
    return await sheet_service.get_connection_status(
        current_user["userId"], current_user["activeCompany"]
    )

@router.get("/connect")
async def connect_sheets(current_user: dict = Depends(get_current_user)):
    """Initiate Google OAuth flow"""
    auth_url = oauth_orchestrator.get_auth_url(
        user_id=current_user["userId"],
        company_id=current_user["activeCompany"],
        company_name=current_user.get("companyName", "My Company")
    )
    return {"auth_url": auth_url}

@router.post("/disconnect")
async def disconnect_sheets(current_user: dict = Depends(get_current_user)):
    """Disconnect Google Sheets (Remove active tokens)"""
    await token_service.disconnect_google_tokens_async(
        current_user["userId"], current_user["activeCompany"]
    )
    return {"status": "disconnected"}

class SwitchSheetRequest(BaseModel):
    spreadsheet_id: str

@router.post("/switch_sheet")
async def switch_sheet(
    request: SwitchSheetRequest, current_user: dict = Depends(get_current_user)
):
    """Switch active Google Sheet to one from history"""
    try:
        sheet_name = await sheet_service.switch_active_sheet(
            current_user["userId"], current_user["activeCompany"], request.spreadsheet_id
        )
        return {"status": "switched", "sheet_name": sheet_name}
    except (ValueError, AuthenticationError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/create_new_sheet")
async def create_new_sheet(current_user: dict = Depends(get_current_user)):
    """Create a new Google Sheet for the active company"""
    try:
        sheet_name = await sheet_service.create_new_sheet(
            current_user["userId"], 
            current_user["activeCompany"], 
            current_user.get("companyName", "My Company")
        )
        return {"status": "created", "sheet_name": sheet_name}
    except (ValueError, AuthenticationError) as e:
        # Handle authentication/token errors - user needs to reconnect
        logger.warning(f"Authentication error creating sheet for user {current_user['userId']}: {e}")
        raise HTTPException(
            status_code=401, 
            detail="Google Sheets connection expired. Please reconnect your Google account."
        )
    except ExternalServiceError as e:
        # Token refresh failed - likely expired refresh token
        if "Token refresh failed" in str(e) or "invalid_grant" in str(e):
            logger.warning(f"Token refresh failed for user {current_user['userId']}: {e}")
            raise HTTPException(
                status_code=401,
                detail="Google Sheets connection expired. Please reconnect your Google account."
            )
        logger.exception("External service error creating sheet")
        raise HTTPException(status_code=502, detail=f"Failed to create Google Sheet: {str(e)}")
    except Exception as e:
        logger.exception("Failed to create new sheet")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/oauth/callback")
async def oauth_callback(code: str = None, state: str = None, error: str = None):
    """Handle OAuth callback from Google"""
    if error:
        return RedirectResponse(url=f"{UPLOAD_PAGE_URL}?sheets_error=true&error={error}")
    if not code:
        return RedirectResponse(url=f"{UPLOAD_PAGE_URL}?sheets_cancelled=true")

    try:
        # 1. Exchange code and parse state
        token_data = oauth_orchestrator.exchange_code(code)
        user_id, company_id, company_name = oauth_orchestrator.parse_state(state)
        
        # 2. Identify user and check status/history
        access_token = token_data["access_token"]
        user_info = oauth_orchestrator.get_user_identity(access_token)
        google_sub = user_info["id"]

        status = await sheet_service.get_connection_status(user_id, company_id)
        
        # 3. Use existing sheet from history or create new one
        target_sheet = None
        if status.get("history"):
            target_sheet = status["history"][0] 
        else:
            # Create first sheet
            sheet_number = await counter_service.get_next_sheet_number_async(user_id, company_id)
            spreadsheet_name = f"AI Receipt - {company_name} {sheet_number}"
            
            target_sheet = oauth_orchestrator.oauth_service.create_spreadsheet(access_token, spreadsheet_name)
            target_sheet["created_at"] = datetime.utcnow().isoformat()
            
            await sheet_history_service.save_sheet_to_history_async(user_id, company_id, google_sub, target_sheet)

        # 4. Save active tokens
        save_data = {
            "access_token": oauth_orchestrator.oauth_service.encrypt_token(token_data["access_token"]),
            "refresh_token": oauth_orchestrator.oauth_service.encrypt_token(token_data["refresh_token"]),
            "token_expiry": token_data["token_expiry"].isoformat(),
            "scopes": token_data.get("scopes", []),
            "google_sub": google_sub,
            "google_email": user_info.get("email"),
            "spreadsheet_id": target_sheet["spreadsheet_id"],
            "spreadsheet_name": target_sheet["spreadsheet_name"],
            "spreadsheet_url": target_sheet["spreadsheet_url"],
            "updated_at": datetime.utcnow().isoformat(),
        }
        await token_service.save_google_tokens_async(user_id, company_id, save_data)

        return RedirectResponse(
            url=f"{UPLOAD_PAGE_URL}?sheets_connected=true&sheet_name={target_sheet['spreadsheet_name']}"
        )
    except Exception as e:
        logger.exception("OAuth callback failed")
        return RedirectResponse(url=f"{SHEETS_PAGE_URL}?sheets_error=true&error=internal_processing_error")


@router.post("/delete_sheet")
async def delete_sheet(
    spreadsheet_id: str, current_user: dict = Depends(get_current_user)
):
    """Delete a spreadsheet from history"""
    await sheet_service.delete_sheet(
        current_user["userId"], current_user["activeCompany"], spreadsheet_id
    )
    return {"status": "deleted", "spreadsheet_id": spreadsheet_id}

