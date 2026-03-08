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
        self.emergency_symptom_severity = {
            "chest pain": "HIGH",
            "shortness of breath": "HIGH",
            "difficulty breathing": "HIGH",
            "fainting": "HIGH",
            "seizure": "HIGH",
            "confusion": "MEDIUM",
            "slurred speech": "HIGH",
            "weakness": "MEDIUM",
            "high fever": "MEDIUM",
            "persistent vomiting": "MEDIUM",
            "severe headache": "MEDIUM",
        }
        self.history_risk_markers = {
            "heart disease": "HIGH",
            "stroke": "HIGH",
            "hypertension": "MEDIUM",
            "diabetes": "MEDIUM",
            "asthma": "MEDIUM",
            "pregnancy": "MEDIUM",
            "kidney disease": "MEDIUM",
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

    def evaluate_emergency_risk(self, symptoms_text: str, history_text: str) -> Dict:
        """
        Rule-based emergency triage using symptom and history keywords.
        """
        severity_score = 1
        reasons: List[str] = []
        symptoms_lower = (symptoms_text or "").lower()
        history_lower = (history_text or "").lower()

        for keyword, level in self.emergency_symptom_severity.items():
            if keyword in symptoms_lower:
                if level == "HIGH":
                    severity_score = max(severity_score, 3)
                elif level == "MEDIUM":
                    severity_score = max(severity_score, 2)
                reasons.append(f"Emergency symptom match: {keyword} ({level})")

        for keyword, level in self.history_risk_markers.items():
            if keyword in history_lower:
                if level == "HIGH":
                    severity_score = max(severity_score, 3)
                elif level == "MEDIUM":
                    severity_score = max(severity_score, 2)
                reasons.append(f"Medical history risk factor: {keyword} ({level})")

        if not reasons:
            reasons.append("No high-confidence emergency marker matched; monitor symptoms closely.")

        severity_label = "LOW"
        if severity_score == 3:
            severity_label = "HIGH"
        elif severity_score == 2:
            severity_label = "MEDIUM"

        return {"severity": severity_label, "reasons": reasons, "score": severity_score}
