"""
Encryption service for securing sensitive data.
Uses Fernet (symmetric encryption) from the cryptography library.
"""

import logging
from cryptography.fernet import Fernet
from app.config.config import config

logger = logging.getLogger(__name__)

class FernetEncryptionService:
    """
    Service for encrypting and decrypting data using Fernet.
    """

    def __init__(self) -> None:
        """
        Initialize the encryption service with the key from config.
        Raises ValueError if ENCRYPTION_KEY is not set.
        """
        if not config.ENCRYPTION_KEY:
            logger.error("ENCRYPTION_KEY not found in configuration.")
            raise ValueError("ENCRYPTION_KEY is required for FernetEncryptionService.")
            
        try:
            self.fernet = Fernet(config.ENCRYPTION_KEY)
        except Exception as e:
            logger.error(f"Invalid ENCRYPTION_KEY: {e}")
            raise ValueError(f"Failed to initialize Fernet: {e}")

    def encrypt(self, data: str) -> str:
        """
        Encrypt a string.
        
        Args:
            data: The plain text string to encrypt.
            
        Returns:
            The encrypted string (URL-safe base64 encoded).
        """
        if not data:
            return ""
        return self.fernet.encrypt(data.encode("utf-8")).decode("utf-8")

    def decrypt(self, token: str) -> str:
        """
        Decrypt a token.
        
        Args:
            token: The encrypted string to decrypt.
            
        Returns:
            The decrypted plain text string.
        """
        if not token:
            return ""
        return self.fernet.decrypt(token.encode("utf-8")).decode("utf-8")
