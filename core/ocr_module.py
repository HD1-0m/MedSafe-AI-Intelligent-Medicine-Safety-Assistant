import pytesseract
from PIL import Image
from typing import Union
import os
import io
from PIL import ImageOps
from PIL import ImageFilter
from typing import List, Tuple

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


def _score_ocr_candidate(image: Image.Image, config: str) -> Tuple[float, str]:
    """
    Run OCR and return (confidence_score, extracted_text).
    """
    text = pytesseract.image_to_string(image, config=config).strip()
    if not text:
        return 0.0, ""

    try:
        data = pytesseract.image_to_data(
            image,
            config=config,
            output_type=pytesseract.Output.DICT,
        )
        confidences: List[float] = []
        for raw in data.get("conf", []):
            try:
                value = float(raw)
            except Exception:
                continue
            if value >= 0:
                confidences.append(value)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    except Exception:
        avg_conf = 0.0

    # Slightly prefer candidates with more readable content when confidence is close.
    signal = min(len(text), 300) / 300.0
    score = (avg_conf * 0.85) + (signal * 15.0)
    return score, text


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

        # Standardize orientation/mode and build multiple variants for difficult text.
        img = ImageOps.exif_transpose(img).convert("RGB")
        gray = ImageOps.grayscale(img)

        variants: List[Image.Image] = []
        variants.append(ImageOps.autocontrast(gray))
        variants.append(ImageOps.equalize(gray))
        variants.append(ImageOps.autocontrast(gray.filter(ImageFilter.SHARPEN)))
        variants.append(ImageOps.autocontrast(gray.filter(ImageFilter.MedianFilter(size=3))))

        # Binary threshold variant often helps on faint pen strokes.
        threshold = ImageOps.autocontrast(gray).point(lambda p: 255 if p > 165 else 0)
        variants.append(threshold)

        # Try multiple segmentation modes and pick the best scoring candidate.
        language = os.getenv("OCR_LANG", "eng").strip() or "eng"
        configs = [
            f"--oem 1 --psm 6 -l {language}",
            f"--oem 1 --psm 11 -l {language}",
            f"--oem 1 --psm 4 -l {language}",
        ]

        best_score = -1.0
        best_text = ""
        for variant in variants:
            for config in configs:
                score, candidate_text = _score_ocr_candidate(variant, config)
                if score > best_score and candidate_text:
                    best_score = score
                    best_text = candidate_text

        return best_text.strip()

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
