from abc import ABC, abstractmethod
import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageOps
import fitz  # PyMuPDF
import os
import logging
import re
import hashlib

logger = logging.getLogger(__name__)

import pymupdf4llm
import logging
import os
import shutil

logger = logging.getLogger(__name__)

class OCRProvider(ABC):
    @abstractmethod
    def extract_text(self, file_path: str, doc_id: str = "temp") -> str:
        # doc_id needed for image naming
        pass

class PyMuPDF4LLMService(OCRProvider):
    def extract_text(self, file_path: str, doc_id: str = "temp") -> str:
        """
        Uses pymupdf4llm to convert PDF directly to Markdown.
        Preserves Layout, Tables, and Headers.
        Extracts images to static folder.
        """
        try:
            logger.info(f"Starting PyMuPDF4LLM extraction for {file_path}")
            
            # Create a specific folder for this document's images to avoid collisions
            # e.g. app/static/uploads/images/doc_1/
            img_rel_path = f"images/{doc_id}"
            img_output_dir = os.path.join("app/static/uploads", img_rel_path)
            
            # Clean/Create directory
            if os.path.exists(img_output_dir):
                shutil.rmtree(img_output_dir)
            os.makedirs(img_output_dir, exist_ok=True)
            
            # Convert to Markdown
            # pymupdf4llm writes images to 'image_path' and returns markdown with links to them.
            md_text = pymupdf4llm.to_markdown(
                file_path,
                write_images=True,
                image_path=img_output_dir,
                image_format="png"
            )
            
            # Fix Image Paths for Web
            # The markdown will contain paths like "app/static/uploads/images/doc_1/image.png"
            # We want "/static/uploads/images/doc_1/image.png"
            
            # Identify what the library outputted as path. 
            # Usually it outputs the relative path we passed to image_path.
            # Let's simply replace the filesystem prefix with the web prefix.
            
            # We know the files are in `app/static/uploads/images/{doc_id}`
            # We want them to be served from `/static/uploads/images/{doc_id}`
            
            # Replace all instances of the output dir with the web alias
            web_prefix = f"/static/uploads/{img_rel_path}"
            
            # This handles if pymupdf4llm used the full string we passed
            md_text = md_text.replace(img_output_dir, web_prefix)
            
            # Also handle if it used relative paths (depending on CWD)
            # Safe bet: Replace the common folder part
            # "app/static/uploads" -> "/static/uploads"
            md_text = md_text.replace("app/static/uploads", "/static/uploads")
            
            logger.info(f"Extraction complete for {doc_id}")
            return md_text
            
        except Exception as e:
            logger.error(f"PyMuPDF4LLM failed: {e}")
            raise

def get_ocr_service() -> OCRProvider:
    return PyMuPDF4LLMService()
