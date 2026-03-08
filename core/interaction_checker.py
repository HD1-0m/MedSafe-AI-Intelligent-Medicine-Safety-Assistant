from typing import Dict, List, Optional, Tuple

from rapidfuzz import fuzz, process

from database.medicine_db import load_medicine_db


class InteractionChecker:
    def __init__(self, db_path: str = "database/medicines.json"):
        self.db = load_medicine_db(db_path)
        self.medicine_names = [med["name"] for med in self.db]

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
                if med["name"] == match_name:
                    return med
        return None

    def identify_medicines_from_text(self, text: str, threshold: int = 80) -> Tuple[List[Dict], List[str]]:
        """
        Parses comma-separated medicine names and returns:
        (identified_medicines, unknown_inputs)
        """
        if not text.strip():
            return [], []

        identified: List[Dict] = []
        unknown: List[str] = []
        seen = set()
        for part in text.split(","):
            raw_name = part.strip()
            if not raw_name:
                continue
            med = self.identify_medicine(raw_name, threshold=threshold)
            if med:
                if med["name"] not in seen:
                    identified.append(med)
                    seen.add(med["name"])
            else:
                unknown.append(raw_name)
        return identified, unknown

    def check_interactions(self, selected_medicines: List[Dict]) -> List[Dict]:
        """
        Checks for interactions between a list of selected medicines.
        """
        interactions_found = []
        med_names = [med["name"].lower() for med in selected_medicines]

        for i, med in enumerate(selected_medicines):
            for interaction in med.get("interactions", []):
                interact_with = interaction["with"].lower()
                # Check if the interacting medicine is in the list (excluding itself)
                if interact_with in med_names:
                    # Avoid duplicate reporting (A with B and B with A)
                    # We can sort names to create a unique key
                    pair = sorted([med["name"], interaction["with"]])
                    interaction_entry = {
                        "pair": pair,
                        "risk": interaction["risk"],
                        "description": interaction["description"],
                    }
                    if interaction_entry not in interactions_found:
                        interactions_found.append(interaction_entry)

        return interactions_found
