import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class SupabaseService:
    def __init__(self):
        self.url: str = os.getenv("SUPABASE_URL", "").strip()
        self.key: str = os.getenv("SUPABASE_ANON_KEY", "").strip()
        
        if not self.url or not self.key:
            # raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
            print("Warning: SUPABASE_URL and SUPABASE_ANON_KEY not set. Storage service will be disabled.")
            self.supabase = None
            return

        try:
            self.supabase: Client = create_client(self.url, self.key)
        except Exception as e:
            print(f"Failed to initialize Supabase client: {e}")
            self.supabase = None

    def upload_image(self, bucket_name: str, file_path: str, destination_path: str):
        """
        Uploads an image to a Supabase storage bucket.
        
        :param bucket_name: Name of the storage bucket.
        :param file_path: Local path to the image file.
        :param destination_path: Path/name in the storage bucket.
        :return: Response from Supabase.
        """
        if not self.supabase:
            raise ValueError("Supabase client is not initialized.")

        try:
            with open(file_path, 'rb') as f:
                response = self.supabase.storage.from_(bucket_name).upload(
                    path=destination_path,
                    file=f,
                    file_options={"content-type": "image/jpeg"} # Defaulting to jpeg, can be dynamic
                )
            return response
        except Exception as e:
            print(f"Error uploading image to Supabase: {e}")
            raise e

    def get_public_url(self, bucket_name: str, file_path: str):
        """
        Gets the public URL for a file in a storage bucket.
        """
        # Manually construct the public URL to ensure it's a full URL
        # Format: https://[PROJECT_ID].supabase.co/storage/v1/object/public/[BUCKET]/[FILE_PATH]
        # self.url already contains https://[PROJECT_ID].supabase.co
        return f"{self.url}/storage/v1/object/public/{bucket_name}/{file_path}"

from fastapi import UploadFile
from datetime import datetime
import mimetypes

class SupabaseStorageService:
    """
    Handles file storage on Supabase Storage.
    Compatible with LocalStorageService interface.
    """

    def __init__(self, bucket_name: str = None):
        self.bucket_name = bucket_name or os.getenv("SUPABASE_BUCKET", "image").strip()
        self.service = SupabaseService()

    async def save_file(self, file: UploadFile) -> dict:
        """
        Saves an uploaded file to Supabase and returns metadata.
        
        Args:
            file: The UploadFile object from FastAPI.
            
        Returns:
            Dict containing filename, local path (temp), and accessible URL.
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        ext = os.path.splitext(file.filename)[-1] or ".png"

        # Determine file type and set appropriate filename
        if ext.lower() == ".pdf":
            filename = f"Document_{timestamp}{ext}"
        else:
            filename = f"Receipt_{timestamp}{ext}"

        try:
            # Read file content
            content = await file.read()
            
            # Use mimetypes to guess content type
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

            # Upload to Supabase
            if not self.service.supabase:
                 raise IOError("Supabase service is not configured.")

            # Note: supabase-py upload accepts bytes
            response = self.service.supabase.storage.from_(self.bucket_name).upload(
                path=filename,
                file=content,
                file_options={"content-type": content_type}
            )

            # Get public URL
            public_url = self.service.get_public_url(self.bucket_name, filename)

            return {
                "filename": filename,
                "path": filename, # In this context, path is the remote path
                "url": public_url
            }
        except Exception as e:
            print(f"Failed to save file to Supabase {file.filename}: {e}")
            raise IOError(f"Could not save uploaded file to Supabase: {e}")
        finally:
            await file.seek(0) # Reset file pointer for any subsequent reads

    async def delete_file(self, filename: str) -> bool:
        """
        Deletes a file from Supabase Storage.
        
        Args:
            filename: The name of the file to delete.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            if not self.service.supabase:
                print("Supabase service not configured, skipping delete.")
                return False

            # The remove method expects a list of paths
            response = self.service.supabase.storage.from_(self.bucket_name).remove([filename])
            
            # If successful, response is a list of deleted objects
            if response and len(response) > 0:
                return True
            return False
        except Exception as e:
            print(f"Failed to delete file from Supabase {filename}: {e}")
            return False
