import pytesseract
from PIL import Image
from typing import Union, Optional
import os

# Placeholder for Tesseract executable path
# In many Linux environments, it's just 'tesseract' in the PATH.
# For Windows, you might need: pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_image(image_source: Union[str, Image.Image]) -> str:
    """
    Extracts text from an image file or a PIL Image object.
    
    Args:
        image_source: Path to the image file or a PIL Image object.
        
    Returns:
        The extracted text as a string.
    """
    try:
        if isinstance(image_source, str):
            if not os.path.exists(image_source):
                return ""
            img = Image.open(image_source)
        else:
            img = image_source
            
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""

def clean_ocr_text(text: str) -> str:
    """
    Cleans raw OCR text for better parsing.
    """
    # Remove multiple newlines
    text = re.sub(r'\n+', '\n', text)
    return text.strip()
