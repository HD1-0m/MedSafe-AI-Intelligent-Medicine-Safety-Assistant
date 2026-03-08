import os
from typing import Dict, Optional, Tuple

import ollama


class AIEngine:
    """
    Handles local LLM interactions using Ollama.
    Also supports lightweight API diagnostics for Ollama/Gemini configuration.
    """

    def __init__(self, model: Optional[str] = None, provider: Optional[str] = None):
        self.provider = (provider or os.getenv("AI_PROVIDER", "ollama")).strip().lower()
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()

    def _mask_key(self, key: str) -> str:
        if not key:
            return "(not set)"
        if len(key) <= 8:
            return "*" * len(key)
        return f"{key[:4]}...{key[-4:]}"

    def check_api_connection(self) -> Tuple[bool, str]:
        """
        Verifies API/provider configuration and connectivity.
        Returns (is_connected, message).
        """
        if self.provider == "ollama":
            try:
                available = ollama.list()
                models = []
                if isinstance(available, dict):
                    for item in available.get("models", []):
                        if isinstance(item, dict):
                            models.append(item.get("name", "unknown"))
                model_hint = (
                    f" Available models: {', '.join(models[:5])}."
                    if models else
                    " No models detected in Ollama list response."
                )
                return True, f"Connected to Ollama successfully.{model_hint}"
            except Exception as e:
                return False, f"Ollama connection failed: {str(e)}"

        if self.provider == "gemini":
            if not self.gemini_api_key:
                return False, "GEMINI_API_KEY is missing. Please set it in your environment/.env."
            return True, f"Gemini provider selected. API key detected: {self._mask_key(self.gemini_api_key)}"

        return False, f"Unsupported AI_PROVIDER '{self.provider}'. Use 'ollama' or 'gemini'."

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
            return (
                f"AI Explanation unavailable (provider={self.provider}, model={self.model}, error={str(e)}). "
                "Please ensure the provider is configured and reachable."
            )

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
            return f"AI Parsing unavailable (provider={self.provider}, model={self.model}): {str(e)}"
