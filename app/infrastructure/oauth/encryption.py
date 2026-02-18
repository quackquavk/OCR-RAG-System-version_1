
"""
Encryption service for handling token security.
"""

import os
import logging
from typing import Optional
from cryptography.fernet import Fernet
from app.core.exceptions import ConfigurationError, ExternalServiceError

logger = logging.getLogger(__name__)

class EncryptionService:
    """
    Handles encryption and decryption of sensitive strings using Fernet.
    """

    def __init__(self) -> None:
        self._cipher: Optional[Fernet] = self._initialize_cipher()

    def _initialize_cipher(self) -> Optional[Fernet]:
        """Initialize the Fernet cipher for token encryption."""
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            logger.warning("ENCRYPTION_KEY not set. Token encryption disabled.")
            return None
        
        try:
            key_bytes = key.encode() if isinstance(key, str) else key
            return Fernet(key_bytes)
        except Exception as e:
            logger.error(f"Failed to initialize encryption cipher: {e}")
            return None

    def encrypt_token(self, token: Optional[str]) -> Optional[str]:
        """Encrypts a sensitive token string."""
        if not token:
            return None
        if not self._cipher:
            logger.error("Attempted encryption without active cipher.")
            raise ConfigurationError("Encryption key not configured.", config_key="ENCRYPTION_KEY")
        
        try:
            return self._cipher.encrypt(token.encode()).decode()
        except Exception as e:
            logger.error(f"Token encryption failed: {e}")
            raise ExternalServiceError("Encryption failed", "Cryptography")

    def decrypt_token(self, encrypted_token: Optional[str]) -> Optional[str]:
        """Decrypts a stored token string."""
        if not encrypted_token:
            return None
        if not self._cipher:
            logger.error("Attempted decryption without active cipher.")
            raise ConfigurationError("Encryption key not configured.", config_key="ENCRYPTION_KEY")
            
        try:
            return self._cipher.decrypt(encrypted_token.encode()).decode()
        except Exception as e:
            logger.error(f"Token decryption failed: {e}")
            raise ExternalServiceError("Decryption failed", "Cryptography")
