import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Dict, Any, List, Optional, Tuple

from app.infrastructure.firebase import DocumentService

logger = logging.getLogger(__name__)

class SearchService:
    """
    Handles retrieval and filtering of documents.
    Encapsulates logic for:
    1. Date parsing and validation
    2. Firebase document retrieval
    3. Multi-criteria filtering (date range, type)
    """

    def __init__(self):
        self.document_service = DocumentService()
        self.nepal_tz = ZoneInfo("Asia/Kathmandu")

    def _parse_dates(self, start_date: Optional[str], end_date: Optional[str]) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Parses YYYY-MM-DD strings into localized datetime objects."""
        start_dt = None
        end_dt = None

        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=self.nepal_tz)
            except ValueError:
                raise ValueError("Invalid start_date format. Use YYYY-MM-DD")

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=self.nepal_tz)
            except ValueError:
                raise ValueError("Invalid end_date format. Use YYYY-MM-DD")
        
        return start_dt, end_dt

    def _get_document_datetime(self, doc_data: Dict[str, Any], doc_id: str) -> Optional[datetime]:
        """Attempts to parse the created_at field into a localized datetime."""
        created_at_str = doc_data.get("created_at")
        if not created_at_str:
            return None

        try:
            if 'Z' in created_at_str:
                dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            else:
                try:
                    dt = datetime.fromisoformat(created_at_str)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    dt = dt.astimezone(self.nepal_tz)
                except ValueError:
                    # Handle "DD Month YYYY at HH:MM:SS AM/PM" format
                    clean_str = created_at_str.replace(' at ', ' ')
                    dt = datetime.strptime(clean_str, "%d %B %Y %I:%M:%S %p")
                    dt = dt.replace(tzinfo=self.nepal_tz)
            return dt
        except Exception:
            logger.warning(f"Failed to parse date for {doc_id}: {created_at_str}")
            return None

    def _matches_filters(
        self, 
        doc_data: Dict[str, Any], 
        created_dt: Optional[datetime], 
        start_dt: Optional[datetime], 
        end_dt: Optional[datetime], 
        doc_type: Optional[str]
    ) -> bool:
        """Applies date range and document type filtering."""
        # 1. Date Range Filter
        if start_dt or end_dt:
            if not created_dt:
                return False
            if start_dt and created_dt < start_dt:
                return False
            if end_dt and created_dt > end_dt:
                return False

        # 2. Document Type Filter
        if doc_type and doc_type.lower() != "all":
            actual_type = doc_data.get("document_type", "").lower()
            target_type = doc_type.lower()

            if target_type == "bank_statement":
                if actual_type not in ["bank_statement", "bank statement"]:
                    return False
            elif target_type == "others":
                if actual_type in ["receipt", "invoice", "bank_statement", "bank statement"]:
                    return False
            else:
                if actual_type != target_type:
                    return False
        
        return True

    async def search_documents_async(
        self, 
        user_id: str, 
        company_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None, 
        doc_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the document search with filtering.
        """
        try:
            # 1. Setup filters
            start_dt, end_dt = self._parse_dates(start_date, end_date)
            
            # 2. Fetch documents
            user_docs = await self.document_service.get_all_async(user_id, company_id)
            
            all_results = []
            for doc_id, doc_data in user_docs.items():
                created_dt = self._get_document_datetime(doc_data, doc_id)
                
                if self._matches_filters(doc_data, created_dt, start_dt, end_dt, doc_type):
                    # Check multiple common field names for flexibility
                    image_url = doc_data.get("image_url") or doc_data.get("imageUrl") or doc_data.get("url")
                    if str(image_url) == "None":
                        image_url = None
                        
                    image_path = doc_data.get("image_path") or doc_data.get("imagePath") or doc_data.get("path")
                    if str(image_path) == "None":
                        image_path = None

                    all_results.append({
                        "doc_id": doc_id,
                        "created_at": doc_data.get("created_at"),
                        "image_url": image_url,
                        "image_path": image_path,
                        "document_type": doc_data.get("document_type", "").lower(),
                        "_sort_dt": created_dt or datetime.min.replace(tzinfo=timezone.utc)
                    })

            # 3. Sort by newest first
            all_results.sort(key=lambda x: x["_sort_dt"], reverse=True)

            # Clean helper sorting field
            for res in all_results:
                res.pop("_sort_dt", None)

            return {
                "documents": all_results,
                "total_count": len(all_results)
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error executing document search for user {user_id}: {e}", exc_info=True)
            raise
