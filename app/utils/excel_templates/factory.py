from typing import Dict, Any
from .generator import ExcelGenerator
from .invoice import InvoiceTemplate
from .receipt import ReceiptTemplate
from .bank_statement import BankStatementTemplate
from .generic import GenericTemplate

class ExcelTemplateFactory:
    """Factory to select appropriate template based on document type"""

    @staticmethod
    def generate_excel(data: Dict[str, Any]) -> bytes:
        """
        Generate Excel file based on document type

        Args:
            data: Document data dictionary

        Returns:
            Excel file as bytes
        """
        generator = ExcelGenerator()
        generator.create_workbook()

        doc_type = data.get('document_type', '').lower()

        # Select template based on document type
        if 'invoice' in doc_type:
            InvoiceTemplate.generate(data, generator)
        elif 'receipt' in doc_type:
            ReceiptTemplate.generate(data, generator)
        elif 'bank' in doc_type or 'statement' in doc_type:
            BankStatementTemplate.generate(data, generator)
        else:
            GenericTemplate.generate(data, generator)

        return generator.get_bytes()
