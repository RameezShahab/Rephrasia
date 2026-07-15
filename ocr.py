"""
ocr.py — Optical Character Recognition for extracting text from images.

Uses Tesseract OCR (must be installed separately on the host).

Windows:  Download from https://github.com/UB-Mannheim/tesseract/wiki
          Install to C:\\Program Files\\Tesseract-OCR\\
Docker:   Installed via apt-get in Dockerfile (tesseract-ocr package).
"""

import io
import logging
import os

import pytesseract
from PIL import Image, ImageEnhance

logger = logging.getLogger(__name__)

# ── Windows Tesseract path auto-detection ────────────────────────────────────
if os.name == "nt":
    _possible_paths = [
        r"D:\agy 120b gpt pro\tesseract.exe",
        r"D:\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\User\AppData\Local\Tesseract-OCR\tesseract.exe",
    ]
    for _path in _possible_paths:
        if os.path.exists(_path):
            pytesseract.pytesseract.tesseract_cmd = _path
            logger.info("Tesseract found at: %s", _path)
            break
    else:
        logger.warning(
            "Tesseract-OCR not found in default locations. "
            "Install it or update the path in ocr.py."
        )

# ── Supported language codes ──────────────────────────────────────────────────
SUPPORTED_LANGUAGES: dict[str, str] = {
    "eng":     "English",
    "urd":     "Urdu",
    "ara":     "Arabic",
    "hin":     "Hindi",
    "eng+urd": "English + Urdu (Mixed)",
}


def get_supported_languages() -> dict[str, str]:
    """Return a mapping of Tesseract language codes → human-readable names."""
    return dict(SUPPORTED_LANGUAGES)


def validate_image(image_data: bytes) -> bool:
    """
    Return True if *image_data* is a valid image that PIL can open.

    Note: image.verify() rewinds the file handle, so we open a fresh BytesIO.
    """
    try:
        Image.open(io.BytesIO(image_data)).verify()
        return True
    except Exception:
        return False


def preprocess_image(image_data: bytes) -> bytes:
    """
    Enhance image contrast to improve OCR accuracy.

    Converts to greyscale and boosts contrast by 2×.
    Returns original bytes unchanged if any error occurs.
    """
    try:
        image = Image.open(io.BytesIO(image_data)).convert("L")
        image = ImageEnhance.Contrast(image).enhance(2.0)
        output = io.BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()
    except Exception as exc:
        logger.warning("Image preprocessing failed (%s); using original.", exc)
        return image_data


def extract_text_from_image(image_data: bytes, language: str = "eng") -> str:
    """
    Extract text from *image_data* using Tesseract OCR.

    Args:
        image_data: Raw image bytes (PNG, JPG, WEBP, BMP, TIFF).
        language:   Tesseract language code (default 'eng').

    Returns:
        Stripped text string extracted from the image.

    Raises:
        ValueError:  If no text is detected in the image.
        RuntimeError: If Tesseract fails or is not installed.
    """
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported OCR language '{language}'. "
            f"Choose from: {', '.join(SUPPORTED_LANGUAGES)}"
        )
    try:
        image = Image.open(io.BytesIO(image_data))
        if image.mode != "RGB":
            image = image.convert("RGB")

        text = pytesseract.image_to_string(image, lang=language).strip()

        if not text:
            raise ValueError("No text detected in image.")

        logger.debug("OCR extracted %d characters (lang=%s).", len(text), language)
        return text

    except ValueError:
        raise
    except Exception as exc:
        logger.exception("OCR extraction failed.")
        raise RuntimeError(f"OCR failed: {exc}") from exc