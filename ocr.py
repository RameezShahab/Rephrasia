"""OCR (Optical Character Recognition) for extracting text from images."""

import pytesseract
from PIL import Image
import io
import os
from pathlib import Path

# --- CONFIGURATION FOR WINDOWS ---
# Download Tesseract here: https://github.com/UB-Mannheim/tesseract/wiki
if os.name == 'nt':  # Windows
    # Common default paths
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Users\User\AppData\Local\Tesseract-OCR\tesseract.exe'
    ]
    
    tesseract_found = False
    for path in possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            tesseract_found = True
            print(f"✅ Tesseract found at: {path}")
            break
            
    if not tesseract_found:
        print("⚠️ WARNING: Tesseract-OCR not found in default locations.")
        print("   Please install it or update the path in ocr.py")

def extract_text_from_image(image_data: bytes, language: str = 'eng') -> str:
    """Extract text from an image using OCR."""
    try:
        image = Image.open(io.BytesIO(image_data))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        text = pytesseract.image_to_string(image, lang=language)
        text = text.strip()
        
        if not text:
            raise ValueError("No text detected in image")
        
        return text
    
    except Exception as e:
        raise RuntimeError(f"OCR failed: {str(e)}")

def get_supported_languages() -> dict:
    return {
        'eng': 'English',
        'urd': 'Urdu',
        'ara': 'Arabic',
        'hin': 'Hindi',
        'eng+urd': 'English + Urdu (Mixed)',
    }

def validate_image(image_data: bytes) -> bool:
    try:
        image = Image.open(io.BytesIO(image_data))
        image.verify()
        return True
    except Exception:
        return False

def preprocess_image(image_data: bytes) -> bytes:
    try:
        from PIL import ImageEnhance
        image = Image.open(io.BytesIO(image_data))
        image = image.convert('L')
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        output = io.BytesIO()
        image.save(output, format='PNG')
        return output.getvalue()
    except Exception as e:
        return image_data