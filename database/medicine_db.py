import json
import os
from typing import List, Dict, Optional

def load_medicine_db(file_path: str = "database/medicines.json") -> List[Dict]:
    """
    Loads the medicine database from a JSON file.
    
    Args:
        file_path: Path to the JSON database file.
        
    Returns:
        A list of medicine dictionaries.
    """
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def get_medicine_by_name(db: List[Dict], name: str) -> Optional[Dict]:
    """
    Finds a medicine by its exact name (case-insensitive).
    """
    name_lower = name.lower()
    for med in db:
        if med['name'].lower() == name_lower:
            return med
    return None
