from typing import List, Dict


class SideEffectEngine:
    """
    Analyzes user-reported post-medication experiences
    considering age, gender, medicines, and dosage.
    """

    def analyze(
        self,
        age: int,
        gender: str,
        medicines: List[Dict],
        doses: List[str],
        experience: str = ""
    ) -> Dict:

        reasons = []
        risk_level = "LOW"

        # Age-based considerations
        if age >= 60:
            reasons.append("Older age may increase sensitivity to certain medicines.")
            risk_level = "MEDIUM"

        if age < 12:
            reasons.append("Children may require adjusted dosing.")

        # Dose-based observation
        for dose in doses:
            if any(char.isdigit() for char in dose):
                try:
                    value = int(''.join(filter(str.isdigit, dose)))
                    if value > 1000:
                        reasons.append("Higher dosage may increase side-effect probability.")
                        risk_level = "MEDIUM"
                except:
                    pass

        # Medication profile considerations
        if len(medicines) >= 3:
            reasons.append("Multiple medicines increase side-effect and interaction complexity.")
            risk_level = "MEDIUM"

        # Experience keywords (optional input)
        exp_lower = (experience or "").lower().strip()
        if exp_lower:
            if any(word in exp_lower for word in ["rash", "swelling", "breathing", "wheeze", "hives"]):
                reasons.append("Symptoms resemble a possible allergic-type reaction.")
                risk_level = "HIGH"
            elif any(word in exp_lower for word in ["dizziness", "nausea", "headache", "fatigue"]):
                reasons.append("Reported symptoms are common mild-to-moderate side effects.")
            else:
                reasons.append("Symptoms require general monitoring.")
        else:
            reasons.append("No symptom description provided; risk is estimated from profile and dosage only.")

        precaution = "Monitor symptoms closely and consult a healthcare professional if they worsen."

        return {
            "risk_level": risk_level,
            "reasons": reasons,
            "precaution": precaution
        }
