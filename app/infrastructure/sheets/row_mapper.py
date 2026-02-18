
"""
Logic for mapping document data to Google Sheet rows.
Handles complex extraction of dates, descriptions, and amounts.
"""

import logging
from datetime import datetime as dt
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class RowMapper:
    """
    Transforms raw document JSON into formatted rows for Google Sheets.
    """

    def map_document_to_rows(self, doc_data: Dict[str, Any], doc_type: str, sheet_name: str) -> List[List[Any]]:
        """
        Maps a document to a list of rows (for multiple transactions) or a single row.
        """
        # 1. Bank Statements (Multiple Transactions)
        if "bank" in doc_type and "statement" in doc_type:
            return self._map_bank_statement(doc_data)

        # 2. Standard Documents (Single Row)
        date = self._extract_date(doc_data)
        description = self._extract_description(doc_data, sheet_name)
        total_amount = self._extract_total_amount(doc_data)
        
        # Format: [Date, Type, Description, Total Amount]
        row = [
            date,
            doc_type.capitalize(),
            description,
            str(total_amount)
        ]
        return [row]

    def _map_bank_statement(self, doc_data: Dict[str, Any]) -> List[List[Any]]:
        """Maps bank statement transactions to rows."""
        transactions = doc_data.get("transactions", [])
        rows = []

        if not transactions:
            # Fallback for empty transactions array
            rows.append([
                doc_data.get("date"),
                doc_data.get("description", "No description"),
                float(doc_data.get("debit", 0)),
                float(doc_data.get("credit", 0))
            ])
            return rows

        for tx in transactions:
            rows.append([
                tx.get("date", doc_data.get("date")),
                tx.get("description", ""),
                float(tx.get("debit", 0)),
                float(tx.get("credit", 0))
            ])
        return rows

    def _extract_date(self, doc_data: Dict[str, Any]) -> str:
        """Robust date extraction logic."""
        # 1. Try created_at (Firebase format)
        if doc_data.get("created_at"):
            try:
                created_at_str = doc_data["created_at"]
                date_part = created_at_str.split(" at ")[0] if " at " in created_at_str else created_at_str
                return dt.strptime(date_part, "%d %B %Y").strftime("%Y-%m-%d")
            except Exception:
                pass

        # 2. Fallback to document fields
        return (
            doc_data.get("date") 
            or self._get_nested(doc_data, "transaction_info", "date")
            or self._get_nested(doc_data, "invoice_details", "date")
            or self._get_nested(doc_data, "invoice_details", "invoice_date")
            or doc_data.get("invoice_date")
            or datetime.now().strftime("%Y-%m-%d")
        )

    def _extract_description(self, doc_data: Dict[str, Any], sheet_name: str) -> str:
        """Extracts description based on the target sheet (Sales vs Purchase)."""
        if sheet_name == "Sales":
            return (
                doc_data.get("customer_name")
                or self._get_nested(doc_data, "customer_info", "name")
                or self._get_nested(doc_data, "bill_to", "name")
                or doc_data.get("bill_to")
                or doc_data.get("client_name")
                or doc_data.get("description", "Unknown Customer")
            )
        elif sheet_name == "Purchase":
            return (
                doc_data.get("vendor_name")
                or doc_data.get("store_name")
                or doc_data.get("merchant_name")
                or self._get_nested(doc_data, "store_info", "name")
                or self._get_nested(doc_data, "supplier_info", "name")
                or self._get_nested(doc_data, "vendor", "name")
                or doc_data.get("vendor")
                or doc_data.get("description", "Unknown Vendor")
            )
        
        return (
            doc_data.get("description")
            or doc_data.get("name")
            or doc_data.get("title", "Unclassified Document")
        )

    def _extract_total_amount(self, doc_data: Dict[str, Any]) -> str:
        """Complex fallback logic for finding the total amount."""
        amount = (
            doc_data.get("total_amount")
            or self._get_nested(doc_data, "summary", "total_amount")
            or self._get_nested(doc_data, "summary", "amount_due")
            or self._get_nested(doc_data, "summary", "grand_total")
            or self._get_nested(doc_data, "summary", "total")
            or self._get_nested(doc_data, "totals", "total_amount")
            or self._get_nested(doc_data, "totals", "grand_total")
            or self._get_nested(doc_data, "totals", "total")
            or self._get_payment_info_amount(doc_data)
            or self._get_nested(doc_data, "invoice_details", "total_amount")
            or self._get_nested(doc_data, "invoice_details", "grand_total")
            or doc_data.get("amount_due")
            or doc_data.get("grand_total")
            or doc_data.get("total")
            or doc_data.get("amount")
            or "0.00"
        )
        return str(amount)

    def _get_nested(self, data: Dict, parent: str, field: str) -> Any:
        """Helper to safely get nested dictionary values."""
        parent_obj = data.get(parent)
        return parent_obj.get(field) if isinstance(parent_obj, dict) else None

    def _get_payment_info_amount(self, data: Dict) -> Any:
        """Helper for list-based payment info."""
        payment_info = data.get("payment_info")
        if isinstance(payment_info, list) and len(payment_info) > 0:
            return payment_info[0].get("amount")
        return None
