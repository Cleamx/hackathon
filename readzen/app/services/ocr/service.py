from abc import ABC, abstractmethod
import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageOps
import re
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
                image = Image.open(file_path)
                image = self._preprocess_image(image)
                text = pytesseract.image_to_string(image)
                return self._post_process_text(text)
        except Exception as e:
            logger.error(f"OCR failed for {file_path}: {e}")
            raise

    def _process_pdf(self, file_path: str) -> str:
        # Convert PDF to images with high quality settings
        # DPI 300 is standard for OCR clarity.
        try:
            images = convert_from_path(file_path, dpi=300, timeout=120)
        except Exception as e:
            raise Exception(f"PDF Conversion failed: {e}")

        full_text = ""
        for i, image in enumerate(images):
            # Preprocess image (Contrast, Binarization)
            processed_image = self._preprocess_image(image)
            
            # Extract Text
            page_text = pytesseract.image_to_string(processed_image, lang='fra+eng') # Dual lang support if available, else defaults
            
            # Clean page text individually to prevent merging across pages
            clean_page_text = self._post_process_text(page_text)

            # Append with page marker (Explicitly required for pagination splitting in API)
            full_text += f"\n\n--- Page {i+1} ---\n\n{clean_page_text}"
            
        return full_text

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Enhance image for OCR: Grayscale -> AutoContrast.
        """
        # Convert to grayscale
        gray = image.convert('L')
        # maximize contrast
        enhanced = ImageOps.autocontrast(gray)
        return enhanced

    def _post_process_text(self, text: str) -> str:
        """
        Clean up raw OCR text and apply structure:
        1. Fix split words (hyphen at end of line).
        2. Detect Titles (Short lines, All Caps).
        3. Fix broken paragraphs.
        """
        if not text:
            return ""

        # 1. Normalize line endings
        text = text.replace('\r\n', '\n')

        # 2. De-hyphenation: "exam-\nple" -> "example"
        text = re.sub(r'(\w+)-\n+(\w+)', r'\1\2', text)

        lines = text.split('\n')
        processed_blocks = []
        current_buffer = []

        for line in lines:
            line = line.strip()
            if not line:
                # Flush buffer as paragraph if exists
                if current_buffer:
                    processed_blocks.append(" ".join(current_buffer))
                    current_buffer = []
                continue

            # Heuristic for Title/Header
            # 1. Short line (< 80 chars)
            # 2. No terminal punctuation (., ;, :)
            # 3. Either All Caps OR Title Case
            is_title = False
            if len(line) < 80 and not line[-1] in '.,;:':
                # Check for All Caps (allow some non-letters like numbers)
                if line.isupper() or (line.istitle() and len(line) < 50):
                   is_title = True
            
            if is_title:
                # Flush previous paragraph
                if current_buffer:
                    processed_blocks.append(" ".join(current_buffer))
                    current_buffer = []
                # Mark as title (using markdown-like syntax for frontend to pick up)
                processed_blocks.append(f"### {line}")
            else:
                # Regular text line, append to buffer
                current_buffer.append(line)
        
        # Flush remaining
        if current_buffer:
            processed_blocks.append(" ".join(current_buffer))

        return '\n\n'.join(processed_blocks)

def get_ocr_service() -> OCRProvider:
    return TesseractOCR()
