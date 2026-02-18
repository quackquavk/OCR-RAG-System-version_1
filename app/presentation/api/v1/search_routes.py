from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.presentation.auth_middleware import get_current_user
from app.use_cases.filter_search.search_service import SearchService
import logging
logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/v1",tags=["Search"])
search_service = SearchService()

@router.get("/search-documents")

async def search_documents(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    doc_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user) 
):
    """
    Search documents for the authenticated user with flexible filters.
    - start_date: Filter by start date (YYYY-MM-DD format)
    - end_date: Filter by end date (YYYY-MM-DD format)
    - doc_type: Filter by document type (receipt, invoice, bank_statement, others)
    """
    try:
        return await search_service.search_documents_async(
            user_id=current_user['userId'],
            company_id=current_user["activeCompany"],
            start_date=start_date,
            end_date=end_date,
            doc_type=doc_type
        )
    except ValueError as e:
        logger.warning(f"Search validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during document search")
        raise HTTPException(status_code=500, detail="An internal error occurred while searching for documents.")
