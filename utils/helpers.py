import re
from datetime import datetime
from typing import Any

def normalize_text(text: str) -> str:
    """
    Normalizes text by removing special characters and extra whitespace.
    """
    if not text:
        return ""
    # Remove non-alphanumeric characters except spaces
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    # Remove extra whitespace
    text = " ".join(text.split())
    return text.lower()

def log_event(message: str, level: str = "INFO") -> None:
    """
    Simple logging utility.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def validate_input(data: Any, expected_type: type) -> bool:
    """
    Validates if the input data matches the expected type.
    """
    return isinstance(data, expected_type)
