"""OCR (Optical Character Recognition) for extracting text from images."""

import pytesseract
from PIL import Image
import io
import os
from pathlib import Path


# Configure Tesseract path for Windows (adjust if needed)
# For Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# Default installation path:
if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def extract_text_from_image(image_data: bytes, language: str = 'eng') -> str:
    """
    Extract text from an image using OCR.
    
    Args:
        image_data: Image file bytes
        language: Language code for OCR
                 'eng' = English
                 'urd' = Urdu
                 'eng+urd' = Both
    
    Returns:
        Extracted text string
    """
    try:
        # Open image from bytes
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Perform OCR
        text = pytesseract.image_to_string(image, lang=language)
        
        # Clean up extracted text
        text = text.strip()
        
        if not text:
            raise ValueError("No text detected in image")
        
        return text
    
    except Exception as e:
        raise RuntimeError(f"OCR failed: {str(e)}")


def get_supported_languages() -> dict:
    """
    Get list of supported OCR languages.
    
    Returns:
        Dictionary of language codes and names
    """
    return {
        'eng': 'English',
        'urd': 'Urdu',
        'ara': 'Arabic',
        'hin': 'Hindi',
        'eng+urd': 'English + Urdu (Mixed)',
    }


def validate_image(image_data: bytes) -> bool:
    """
    Validate if the data is a valid image.
    
    Args:
        image_data: Image file bytes
    
    Returns:
        True if valid image, False otherwise
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        image.verify()
        return True
    except Exception:
        return False


def preprocess_image(image_data: bytes) -> bytes:
    """
    Preprocess image for better OCR accuracy.
    Applies grayscale conversion and contrast enhancement.
    
    Args:
        image_data: Original image bytes
    
    Returns:
        Preprocessed image bytes
    """
    try:
        from PIL import ImageEnhance
        
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to grayscale
        image = image.convert('L')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Save to bytes
        output = io.BytesIO()
        image.save(output, format='PNG')
        return output.getvalue()
    
    except Exception as e:
        # Return original if preprocessing fails
        return image_data
