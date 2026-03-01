from typing import List, Dict

class RiskEngine:
    """
    Computes health risk severity based on symptoms and interactions.
    """

    def __init__(self):
        # Rule-based severity mapping for common symptoms
        self.symptom_severity = {
            "chest pain": "HIGH",
            "difficulty breathing": "HIGH",
            "severe allergic reaction": "HIGH",
            "dizziness": "MEDIUM",
            "nausea": "LOW",
            "headache": "LOW",
            "fever": "MEDIUM",
            "rash": "MEDIUM"
        }

    def evaluate_risk(self, symptoms: List[str], interactions: List[Dict]) -> Dict:
        """
        Evaluates the overall risk level.
        """
        severity_score = 0
        reasons = []

        # Evaluate symptoms
        for symptom in symptoms:
            symptom_lower = symptom.lower()
            found = False
            for key, level in self.symptom_severity.items():
                if key in symptom_lower:
                    if level == "HIGH":
                        severity_score = max(severity_score, 3)
                    elif level == "MEDIUM":
                        severity_score = max(severity_score, 2)
                    else:
                        severity_score = max(severity_score, 1)
                    reasons.append(f"Symptom detected: {key} ({level})")
                    found = True
                    break
            if not found:
                severity_score = max(severity_score, 1)
                reasons.append(f"Unclassified symptom: {symptom}")

        # Evaluate interactions
        for interaction in interactions:
            risk = interaction['risk']
            if risk == "HIGH":
                severity_score = max(severity_score, 3)
            elif risk == "MEDIUM":
                severity_score = max(severity_score, 2)
            else:
                severity_score = max(severity_score, 1)
            reasons.append(f"Interaction risk: {interaction['pair'][0]} + {interaction['pair'][1]} ({risk})")

        # Map score back to label
        severity_label = "LOW"
        if severity_score == 3:
            severity_label = "HIGH"
        elif severity_score == 2:
            severity_label = "MEDIUM"

        return {
            "severity": severity_label,
            "reasons": reasons,
            "score": severity_score
        }
