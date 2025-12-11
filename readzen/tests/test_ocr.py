import pytest
from unittest.mock import MagicMock, patch
from app.services.ocr.service import TesseractOCR

def test_ocr_provider_selection():
    from app.services.ocr.service import get_ocr_service
    service = get_ocr_service()
    assert isinstance(service, TesseractOCR)

@patch('app.services.ocr.service.pytesseract.image_to_string')
@patch('app.services.ocr.service.convert_from_path')
def test_tesseract_ocr_pdf(mock_convert, mock_tesseract):
    # Setup mocks
    mock_convert.return_value = ["mock_image_1", "mock_image_2"]
    mock_tesseract.side_effect = ["Page 1 text", "Page 2 text"]
    
    service = TesseractOCR()
    text = service.extract_text("dummy.pdf")
    
    # Assertions
    mock_convert.assert_called_once_with("dummy.pdf", dpi=100, timeout=60)
    assert mock_tesseract.call_count == 2
    assert "Page 1 text" in text
    assert "Page 2 text" in text
    assert "--- Page 1 ---" in text
