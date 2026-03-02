from rapidfuzz import process, fuzz
from typing import List, Dict, Tuple, Optional

from database.medicine_db import load_medicine_db

class InteractionChecker:
    def __init__(self, db_path: str = "database/medicines.json"):
        self.db = load_medicine_db(db_path)
        self.medicine_names = [med['name'] for med in self.db]
    def identify_medicine(self, query: str, threshold: int = 80) -> Optional[Dict]:
        """
        Identifies a medicine from a query string using fuzzy matching.
        """
        if not query or not self.medicine_names:
            return None
            
        result = process.extractOne(query, self.medicine_names, scorer=fuzz.WRatio)
        if result and result[1] >= threshold:
            match_name = result[0]
            for med in self.db:
                if med['name'] == match_name:
                    return med
        return None

    def check_interactions(self, selected_medicines: List[Dict]) -> List[Dict]:
        """
        Checks for interactions between a list of selected medicines.
        """
        interactions_found = []
        med_names = [med['name'].lower() for med in selected_medicines]
        
        for i, med in enumerate(selected_medicines):
            for interaction in med.get('interactions', []):
                interact_with = interaction['with'].lower()
                # Check if the interacting medicine is in the list (excluding itself)
                if interact_with in med_names:
                    # Avoid duplicate reporting (A with B and B with A)
                    # We can sort names to create a unique key
                    pair = sorted([med['name'], interaction['with']])
                    interaction_entry = {
                        "pair": pair,
                        "risk": interaction['risk'],
                        "description": interaction['description']
                    }
                    if interaction_entry not in interactions_found:
                        interactions_found.append(interaction_entry)
                        
        return interactions_found
