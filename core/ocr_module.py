import pytesseract
from PIL import Image
from typing import Union
import os
import io
from PIL import ImageOps

def _configure_tesseract_binary() -> None:
    """
    Configure Tesseract executable path if provided via env var.
    """
    tesseract_path = os.getenv("TESSERACT_CMD", "").strip()
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path


def is_tesseract_available() -> bool:
    """
    Returns True when Tesseract OCR engine is reachable.
    """
    _configure_tesseract_binary()
    try:
        _ = pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False

def extract_text_from_image(image_source: Union[str, Image.Image, bytes]) -> str:
    """
    Extract text from:
      1. Path to image file
      2. PIL Image
      3. Bytes (e.g., from Streamlit upload)

    Returns an empty string on failure.
    """
    try:
        _configure_tesseract_binary()

        # --- IMAGE SOURCE AS PATH ---
        if isinstance(image_source, str):
            if not os.path.exists(image_source):
                return ""
            img = Image.open(image_source)

        # --- BYTES (e.g., UPLOADED FILE) ---
        elif isinstance(image_source, (bytes, bytearray)):
            img = Image.open(io.BytesIO(image_source))

        # --- PIL IMAGE ---
        elif isinstance(image_source, Image.Image):
            img = image_source

        else:
            raise TypeError(f"Unsupported image type: {type(image_source)}")

        # --- LIGHT PREPROCESSING TO IMPROVE OCR QUALITY ---
        # Convert to grayscale and increase contrast for cleaner text extraction.
        processed = ImageOps.grayscale(img)
        processed = ImageOps.autocontrast(processed)

        # --- OCR ---
        text = pytesseract.image_to_string(processed, config="--psm 6")
        return text.strip()

    except Exception as e:
        print(f"OCR Error: {e}")
        return ""

def clean_ocr_text(text: str) -> str:
    """
    Cleanup raw OCR text to remove excess newlines/spaces for parsing.
    """
    import re
    # collapse multiple newlines
    text = re.sub(r"\n+", "\n", text)
    # collapse multiple spaces
    text = re.sub(r"[ ]+", " ", text)
    return text.strip()


def extract_prescription_raw_text(image_source: Union[str, Image.Image, bytes]) -> str:
    """
    Convenience wrapper for prescription OCR extraction.
    """
    return clean_ocr_text(extract_text_from_image(image_source))
