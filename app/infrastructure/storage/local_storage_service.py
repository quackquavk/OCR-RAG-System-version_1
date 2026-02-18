import os
from datetime import datetime
from pathlib import Path
from fastapi import UploadFile
import logging

logger = logging.getLogger(__name__)

class LocalStorageService:
    """
    Handles file storage on the local filesystem.
    """

    def __init__(self, upload_dir: str = "media/uploads", base_url: str = "http://127.0.0.1:8000"):
        self.upload_dir = Path(upload_dir)
        self.base_url = base_url
        self._ensure_dir()

    def _ensure_dir(self):
        """Ensures the upload directory exists."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file: UploadFile) -> dict:
        """
        Saves an uploaded file and returns metadata.
        
        Args:
            file: The UploadFile object from FastAPI.
            
        Returns:
            Dict containing filename, local path, and accessible URL.
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        ext = os.path.splitext(file.filename)[-1] or ".png"

        # Determine file type and set appropriate filename
        if ext.lower() == ".pdf":
            filename = f"Document_{timestamp}{ext}"
        else:
            filename = f"Receipt_{timestamp}{ext}"

        file_path = self.upload_dir / filename

        try:
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Construct accessible URL
            url = f"{self.base_url}/media/uploads/{filename}"
            
            logger.info(f"File saved: {filename} at {file_path}")
            
            return {
                "filename": filename,
                "path": str(file_path),
                "url": url
            }
        except Exception as e:
            logger.error(f"Failed to save file {file.filename}: {e}")
            raise IOError(f"Could not save uploaded file: {e}")
        
        finally:
            pass
