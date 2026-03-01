import ollama
from typing import Dict, Optional

class AIEngine:
    """
    Handles local LLM interactions using Ollama.
    """

    def __init__(self, model: str = "llama3"):
        self.model = model

    def generate_explanation(self, risk_data: Dict) -> str:
        """
        Generates an educational explanation for detected risks.
        """
        severity = risk_data.get('severity', 'UNKNOWN')
        reasons = ", ".join(risk_data.get('reasons', []))
        
        prompt = (
            f"As a medical safety assistant, explain the following health risk in simple, educational terms. "
            f"Severity: {severity}. Reasons: {reasons}. "
            f"Provide clear warnings and suggest when to consult a professional. "
            f"Do not provide a diagnosis."
        )

        try:
            response = ollama.chat(model=self.model, messages=[
                {'role': 'user', 'content': prompt},
            ])
            return response['message']['content']
        except Exception as e:
            return f"AI Explanation unavailable (Ollama error: {str(e)}). Please ensure Ollama is running with the {self.model} model."

    def parse_prescription(self, ocr_text: str) -> str:
        """
        Uses AI to structure raw OCR text from a prescription.
        """
        prompt = (
            f"Extract medicine names and dosages from the following prescription text. "
            f"Return it as a structured list. Text: \n{ocr_text}"
        )
        
        try:
            response = ollama.chat(model=self.model, messages=[
                {'role': 'user', 'content': prompt},
            ])
            return response['message']['content']
        except Exception as e:
            return f"AI Parsing unavailable: {str(e)}"
