import pytesseract
from PIL import Image
from typing import Union
import os
import io

# If you are on Windows, set this to your Tesseract path:
# Example (default Windows install):
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_image(image_source: Union[str, Image.Image, bytes]) -> str:
    """
    Extract text from:
      1. Path to image file
      2. PIL Image
      3. Bytes (e.g., from Streamlit upload)

    Returns an empty string on failure.
    """
    try:
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

        # --- OCR ---
        text = pytesseract.image_to_string(img)
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