from app.infrastructure.firebase import CounterService

class KeyGenerator:
    """Async Key Generator using Firebase counters"""
    
    def __init__(self):
        self.counter_service = CounterService()

    async def generate_key_async(self, document_type: str, user_id: str, company_id: str) -> str:
        doc = document_type.lower()
        
        # Map document type to prefix
        if "invoice" in doc:
            prefix = "INV"
        elif "receipt" in doc:
            prefix = "RCT"
        elif "statement" in doc:
            prefix = "STM"
        elif "bill" in doc:
            prefix = "BIL"
        else:
            prefix = "GEN"

        # Get next number from Firebase
        number = await self.counter_service.get_next_document_number_async(
            user_id, company_id, prefix
        )

        # Return key format: INV1, RCT2, etc.
        return f"{prefix}{number}"
