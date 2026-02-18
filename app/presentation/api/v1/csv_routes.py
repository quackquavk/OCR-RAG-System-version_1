from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response

from app.presentation.auth_middleware import get_current_user
from app.use_cases.export.export_service import ExportService

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Exports"])
export_service = ExportService()

@router.get("/generate-csv/{doc_id}")
async def generate_csv(doc_id: str, current_user: dict = Depends(get_current_user)):
    """
    Generate a CSV export for a specific document.
    """
    logger.info(f"CSV export request for doc {doc_id} by user {current_user['userId']}")
    try:
        return await export_service.generate_csv(
            user_id=current_user["userId"],
            company_id=current_user["activeCompany"],
            doc_id=doc_id
        )
    except Exception as e:
        logger.exception(f"Failed to generate CSV for {doc_id}")
        raise HTTPException(status_code=500, detail=f"Failed to generate CSV: {str(e)}")

@router.get("/generate-excel/{doc_id}")
async def generate_excel(doc_id: str, current_user: dict = Depends(get_current_user)):
    """
    Generate a professionally formatted Excel export for a specific document.
    """
    logger.info(f"Excel export request for doc {doc_id} by user {current_user['userId']}")
    try:
        excel_bytes, filename = await export_service.generate_excel(
            user_id=current_user["userId"],
            company_id=current_user["activeCompany"],
            doc_id=doc_id
        )
        
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        logger.exception(f"Failed to generate Excel for {doc_id}")
        raise HTTPException(status_code=500, detail=f"Failed to generate Excel: {str(e)}")
