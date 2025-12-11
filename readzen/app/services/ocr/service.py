from abc import ABC, abstractmethod
import pytesseract
from pdf2image import convert_from_path
import logging

logger = logging.getLogger(__name__)

class OCRProvider(ABC):
    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        pass

class TesseractOCR(OCRProvider):
    def extract_text(self, file_path: str) -> str:
        try:
            # Check if file is PDF
            if file_path.lower().endswith('.pdf'):
                return self._process_pdf(file_path)
            else:
                # Assume image
                return pytesseract.image_to_string(file_path)
        except Exception as e:
            logger.error(f"OCR failed for {file_path}: {e}")
            raise

    def _process_pdf(self, file_path: str) -> str:
        # Convert PDF to images with optimized settings for speed
        # DPI 100 significantly reduces processing time. Grayscale removed for stability.
        # Added timeout to prevent hanging.
        try:
            images = convert_from_path(file_path, dpi=100, timeout=60)
        except Exception as e:
            raise Exception(f"PDF Conversion failed: {e}")

        text = ""
        for i, image in enumerate(images):
            page_text = pytesseract.image_to_string(image)
            text += f"\n\n--- Page {i+1} ---\n\n{page_text}"
        return text

def get_ocr_service() -> OCRProvider:
    return TesseractOCR()
