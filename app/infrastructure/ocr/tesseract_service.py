import os
import platform
import asyncio
from pathlib import Path
from io import BytesIO
import requests
import easyocr
import numpy as np
import pytesseract
import cv2
import pillow_heif
from PIL import Image, UnidentifiedImageError
from pdf2image import convert_from_path

# Register HEIF opener for Pillow
pillow_heif.register_heif_opener()

import logging
logger = logging.getLogger(__name__)

def configure_tesseract():
    """
    Configure Tesseract OCR based on the deployment environment.
    """
    tessdata_prefix = os.getenv('TESSDATA_PREFIX')
    
    if tessdata_prefix:
        os.environ['TESSDATA_PREFIX'] = tessdata_prefix
        logger.debug(f"Using Tesseract data from: {tessdata_prefix}")
        return
    
    if platform.system() == 'Windows':
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tessdata',
            r'C:\Program Files (x86)\Tesseract-OCR\tessdata',
            os.path.join(os.getenv('LOCALAPPDATA', ''), r'Tesseract-OCR\tessdata')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                os.environ['TESSDATA_PREFIX'] = path
                logger.debug(f"Found Tesseract data at: {path}")
                return
        
        logger.warning("Tesseract data directory not found. Ensure Tesseract is installed or TESSDATA_PREFIX is set.")
    else:
        logger.debug("Using system Tesseract configuration.")

configure_tesseract()


class OCRService:
    """
    Service for extracting text from images and PDFs using Tesseract OCR with EasyOCR fallback.
    """
    
    def __init__(self, languages: str = 'eng'):
        self.languages = languages
        # EasyOCR uses 2-letter codes (en), Tesseract uses 3-letter (eng)
        easyocr_langs = [l.replace('eng', 'en') for l in languages.split('+')]
        self.easyocr_reader = easyocr.Reader(easyocr_langs, verbose=False)

    def preprocess_image(self, img: Image.Image) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy using OpenCV.
        """
        img_np = np.array(img.convert('RGB'))
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        
        # Apply Otsu's thresholding for optimal binary conversion
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    def _run_tesseract(self, image: np.ndarray) -> str:
        """Helper to run Tesseract with consistent config"""
        custom_config = r'--oem 3 --psm 6'
        return pytesseract.image_to_string(
            image, 
            lang=self.languages, 
            config=custom_config
        ).strip()

    def _run_easyocr_fallback(self, image_content: bytes) -> str:
        """Helper to run EasyOCR fallback"""
        try:
            text_list = self.easyocr_reader.readtext(image_content, detail=0)
            return "\n".join(text_list).strip()
        except Exception as e:
            logger.error(f"EasyOCR fallback failed: {e}")
            return ""

    def extract_text_from_url(self, image_url: str) -> str:
        """
        Extract text from an image URL.
        Raises exceptions on failure.
        """
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()

            img = Image.open(BytesIO(response.content))
            return self._process_single_image(img, raw_bytes=response.content)

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download image from {image_url}: {e}")
            raise ValueError(f"Failed to download image: {e}")
        except UnidentifiedImageError:
            logger.error(f"Invalid image format at {image_url}")
            raise ValueError("Invalid image file format")
        except Exception as e:
            logger.error(f"Error processing image URL {image_url}: {e}")
            raise

    def extract_text_from_image(self, image_path: Path) -> str:
        """
        Extracts text from a local image file.
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        try:
            img = Image.open(image_path)
            # Read bytes for EasyOCR fallback if needed
            with open(image_path, "rb") as f:
                raw_bytes = f.read()
                
            return self._process_single_image(img, raw_bytes=raw_bytes)

        except UnidentifiedImageError:
            raise ValueError(f"Invalid image file: {image_path}")
        except Exception as e:
            logger.error(f"Error extracting text from image {image_path}: {e}")
            raise

    async def extract_text_from_bytes_async(self, content: bytes, filename: str) -> str:
        """
        Extracts text from raw bytes asynchronously.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.extract_text_from_bytes, content, filename)

    def extract_text_from_bytes(self, content: bytes, filename: str) -> str:
        """
        Extracts text from raw bytes.
        """
        try:
            from pdf2image import convert_from_bytes
            ext = os.path.splitext(filename)[-1].lower()
            if ext == '.pdf':
                logger.info(f"Processing PDF from bytes: {filename}")
                images = convert_from_bytes(content, dpi=300)
                
                all_text = []
                for i, img in enumerate(images):
                    page_text = self._process_single_image(img)
                    if page_text:
                        all_text.append(f"--- Page {i + 1} ---\n{page_text}")
                return "\n\n".join(all_text)
            else:
                img = Image.open(BytesIO(content))
                return self._process_single_image(img, raw_bytes=content)
        except Exception as e:
            logger.error(f"Error extracting text from bytes {filename}: {e}")
            raise

    def _process_single_image(self, img: Image.Image, raw_bytes: bytes = None) -> str:
        """Internal method to process a loaded PIL image."""
        preprocessed = self.preprocess_image(img)
        text = self._run_tesseract(preprocessed)

        if not text or len(text) < 20:
            logger.info("Tesseract yield low text, attempting EasyOCR fallback.")
            if raw_bytes:
                fallback_text = self._run_easyocr_fallback(raw_bytes)
                if fallback_text:
                    return fallback_text
            elif img:
                 # convert PIL to bytes if raw_bytes not provided
                 buf = BytesIO()
                 img.save(buf, format=img.format or 'PNG')
                 return self._run_easyocr_fallback(buf.getvalue())
                 
        return text

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        Extracts text from a PDF file.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            logger.info(f"Processing PDF: {pdf_path}")
            images = convert_from_path(str(pdf_path), dpi=300)
            
            all_text = []
            for i, img in enumerate(images):
                page_text = self._process_single_image(img)
                if page_text:
                    all_text.append(f"--- Page {i + 1} ---\n{page_text}")
            
            combined_text = "\n\n".join(all_text)
            
            if not combined_text:
                logger.warning(f"No text extracted from PDF: {pdf_path}")
                raise ValueError("No text extracted from PDF")
            
            return combined_text

        except Exception as e:
            msg = str(e)
            if "poppler" in msg.lower():
                logger.error("Poppler not found. Please install Poppler.")
                raise EnvironmentError("Poppler is required for PDF processing but not found.")
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            raise

    def extract_text_from_file(self, file_path: Path) -> str:
        """
        Dispatches to correct extractor based on file extension.
        """
        ext = file_path.suffix.lower()
        if ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp','.heic','.heif']:
            return self.extract_text_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    async def extract_text_from_pdf_async(self, pdf_path: Path) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.extract_text_from_pdf, pdf_path)

    async def extract_text_from_file_async(self, file_path: Path) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.extract_text_from_file, file_path)

    async def extract_text_from_url_async(self, image_url: str) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.extract_text_from_url, image_url)
    