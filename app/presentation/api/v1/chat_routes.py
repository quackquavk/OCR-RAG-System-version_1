from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.use_cases.rag.rag_service import get_rag_service
from app.presentation.auth_middleware import get_current_user
from app.core.exceptions import RateLimitExceededError
import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Chat"])

class ChatRequest(BaseModel):
    query: str

rag_service = get_rag_service()

@router.post("/chat")
async def chat(request: ChatRequest, 
               current_user: dict = Depends(get_current_user)
            ):
    """
    RAG-powered chat endpoint with user and company-specific data isolation
    Retrieves relevant documents and generates intelligent responses
    Only returns documents belonging to the authenticated user and their active company
    """
    logger.info(f"Chat request for user: {current_user['userId']}, company: {current_user['companyName']} (ID: {current_user['activeCompany']})")
    try:
        user_id = current_user["userId"]
        company_id = current_user["activeCompany"]

        # Get RAG service and perform user + company filtered search
        result = await rag_service.chat_async(request.query, user_id, company_id)

        return result
    except Exception as e:
        if isinstance(e, RateLimitExceededError):
            # User facing message for rate limit
            raise HTTPException(status_code=429, detail="rate liit exceed please try again in few minutes")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, 
                      current_user: dict = Depends(get_current_user)
                   ):
    """
    Streaming RAG-powered chat endpoint with user and company-specific data isolation
    """
    # logger.info(f"Streaming Chat request for user: {current_user['userId']}, company: {current_user['companyName']} (ID: {current_user['activeCompany']})")
    try:
        user_id = current_user["userId"]
        company_id = current_user["activeCompany"]

        return StreamingResponse(
            rag_service.chat_stream(request.query, user_id, company_id),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Error in streaming chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Streaming error: {str(e)}")
