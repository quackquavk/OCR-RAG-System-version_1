
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
import logging
logger = logging.getLogger(__name__)

class Config:
    
    TESSDATA_PREFIX: Optional[str] = os.getenv('TESSDATA_PREFIX')
    
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv(
        'GOOGLE_APPLICATION_CREDENTIALS',
        './app/config/google_service_account.json'
    )
    FIREBASE_CREDENTIALS: str = os.getenv(
        'FIREBASE_CREDENTIALS',
        './app/config/firebase-key.json'
    )
    
    
    GOOGLE_OAUTH_CLIENT_ID: Optional[str] = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    GOOGLE_OAUTH_CLIENT_SECRET: Optional[str] = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
    GOOGLE_OAUTH_REDIRECT_URI: str = os.getenv(
        'GOOGLE_OAUTH_REDIRECT_URI',
        'http://localhost:8000/api/sheets/oauth/callback'
    )
    
    ENCRYPTION_KEY: Optional[str] = os.getenv('ENCRYPTION_KEY')
    
    HOST: str = os.getenv('HOST', '0.0.0.0')
    PORT: int = int(os.getenv('PORT', '8000'))
    
    ALLOWED_ORIGINS: list = os.getenv('ALLOWED_ORIGINS', '*').split(',')
    
    @classmethod
    def validate(cls) -> None:
        """Validate that required configuration is present."""
        required_files = [
            ('GOOGLE_APPLICATION_CREDENTIALS', cls.GOOGLE_APPLICATION_CREDENTIALS),
            # ('FIREBASE_CREDENTIALS', cls.FIREBASE_CREDENTIALS),
        ]
        
        missing = []
        for name, path in required_files:
            if not Path(path).exists():
                missing.append(f"{name}: {path}")
        
        if missing:
            try:
               
                logger.warning("Warning: The following credential files are missing:")
                for item in missing:
                    logger.warning(f"   - {item}")
                logger.warning("\nThe application may not function correctly without these files.")
                logger.warning("Please ensure all credentials are in place before deployment.\n")
            except ImportError:
                print("Warning: The following credential files are missing:")
                for item in missing:
                    print(f"   - {item}")
    
    @classmethod
    def print_config(cls) -> None:
        """Print current configuration (for debugging)."""
        pass

config = Config()

if __name__ != "__main__":
    config.validate()
