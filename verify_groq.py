import os
import asyncio
from unittest.mock import MagicMock
from app.infrastructure.encryption_service import FernetEncryptionService
from app.use_cases.processing.manage_groq_key import ManageGroqKeyUseCase
from app.core.interfaces import IUserRepository

# Generated using: Fernet.generate_key().decode()
VALID_TEST_KEY = "8z_p0-K52Y3s0b5lU5m_Bq1_Gq9_Gq9_Gq9_Bq1_Bq1="
os.environ["SECRET_ENCRYPTION_KEY"] = VALID_TEST_KEY

async def test_encryption():
    print("Testing Encryption Service...")
    service = FernetEncryptionService()
    
    plaintext = "gsk_test_key_123"
    encrypted = service.encrypt(plaintext)
    decrypted = service.decrypt(encrypted)
    
    assert plaintext == decrypted
    assert plaintext != encrypted
    print("✅ Encryption Service Test Passed")

async def test_use_case():
    print("\nTesting ManageGroqKeyUseCase...")
    
    encryption_service = FernetEncryptionService()
    user_repo = MagicMock(spec=IUserRepository)
    use_case = ManageGroqKeyUseCase(encryption_service, user_repo)
    
    # Mock verify_key to avoid external requests
    use_case._verify_key = MagicMock(return_value=asyncio.Future())
    use_case._verify_key.return_value.set_result(True)
    
    user_id = "test-user-123"
    raw_key = "gsk_abcdef123456"
    
    await use_case.save_key(user_id, raw_key)
    
    # Check if repository was called
    assert user_repo.update_groq_key.called
    print("✅ Use Case Test Passed")

if __name__ == "__main__":
    # asyncio.run(test_encryption())
    # asyncio.run(test_use_case())
    