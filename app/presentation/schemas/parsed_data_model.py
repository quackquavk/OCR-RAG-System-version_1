from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class LineItem(BaseModel):
    description: Optional[str] = Field(None, description="Description of the item")
    quantity: Optional[float] = Field(None, description="Quantity")
    price: Optional[float] = Field(None, description="Unit price")
    total: Optional[float] = Field(None, description="Line total")

class Transaction(BaseModel):
    date: Optional[str] = Field(None, description="Transaction date (YYYY-MM-DD)")
    description: Optional[str] = Field(None, description="Transaction description")
    debit: Optional[float] = Field(0, description="Debit amount")
    credit: Optional[float] = Field(0, description="Credit amount")

class ParsedData(BaseModel):
    document_type: str = Field(..., description="Category of the document (invoice, receipt, bank statement, bill, other)")
    total_amount: Optional[float] = Field(None, description="Final total amount extracted from the document")
    date: Optional[str] = Field(None, description="Document date (YYYY-MM-DD)")
    vendor_name: Optional[str] = Field(None, description="Name of the merchant or issuing company")
    customer_name: Optional[str] = Field(None, description="Name of the customer/client (for invoices)")
    account_number: Optional[str] = Field(None, description="Bank account number (for statements)")
    line_items: Optional[List[LineItem]] = Field(None, description="List of line items (for invoices/receipts)")
    transactions: Optional[List[Transaction]] = Field(None, description="List of transactions (for bank statements)")
    raw_text_length: Optional[int] = Field(None, description="Length of the extracted OCR text")

class ProcessDocumentResponse(BaseModel):
    status: str = "success"
    data: ParsedData
    # message: Optional[str] = None
