import json
import os
import urllib.error
import urllib.request
from typing import Dict, Optional, Tuple

import ollama


class AIEngine:
    """
    Handles LLM interactions with either Ollama (local) or Gemini (API).
    """

    def __init__(self, model: Optional[str] = None, provider: Optional[str] = None):
        self.provider = (provider or os.getenv("AI_PROVIDER", "ollama")).strip().lower()
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.model = model or (self.gemini_model if self.provider == "gemini" else self.ollama_model)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()

    def _mask_key(self, key: str) -> str:
        if not key:
            return "(not set)"
        if len(key) <= 8:
            return "*" * len(key)
        return f"{key[:4]}...{key[-4:]}"

    def _gemini_generate(self, prompt: str) -> str:
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is missing. Please set it in your environment/.env.")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.gemini_api_key}"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError(f"Gemini response missing candidates: {data}")

        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
        if not text:
            raise ValueError(f"Gemini response did not contain text: {data}")
        return text

    def _ollama_generate(self, prompt: str) -> str:
        response = ollama.chat(model=self.model, messages=[
            {"role": "user", "content": prompt},
        ])
        return response["message"]["content"]

    def _generate(self, prompt: str) -> str:
        if self.provider == "gemini":
            return self._gemini_generate(prompt)
        if self.provider == "ollama":
            return self._ollama_generate(prompt)
        raise ValueError(f"Unsupported AI_PROVIDER '{self.provider}'. Use 'ollama' or 'gemini'.")

    def check_api_connection(self) -> Tuple[bool, str]:
        """
        Verifies provider configuration and connectivity.
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
                model_hint = f" Available models: {', '.join(models[:5])}." if models else ""
                return True, f"Connected to Ollama successfully.{model_hint}"
            except Exception as e:
                return False, f"Ollama connection failed: {str(e)}"

        if self.provider == "gemini":
            if not self.gemini_api_key:
                return False, "GEMINI_API_KEY is missing. Please set it in your environment/.env."
            try:
                _ = self._gemini_generate("Reply with exactly: OK")
                return True, (
                    f"Connected to Gemini successfully using model '{self.model}'. "
                    f"API key detected: {self._mask_key(self.gemini_api_key)}"
                )
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", errors="ignore")
                return False, f"Gemini connection failed (HTTP {e.code}): {detail}"
            except Exception as e:
                return False, f"Gemini connection failed: {str(e)}"

        return False, f"Unsupported AI_PROVIDER '{self.provider}'. Use 'ollama' or 'gemini'."

    def generate_explanation(self, risk_data: Dict) -> str:
        """
        Generates an educational explanation for detected risks.
        """
        severity = risk_data.get("severity", "UNKNOWN")
        reasons = ", ".join(risk_data.get("reasons", []))
        prompt = (
            "As a medical safety assistant, explain the following health risk in simple, educational terms. "
            f"Severity: {severity}. Reasons: {reasons}. "
            "Provide clear warnings and suggest when to consult a professional. "
            "Do not provide a diagnosis."
        )

        try:
            return self._generate(prompt)
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
            "Extract medicine names and dosages from the following prescription text. "
            "Return it as a structured list. Text: \n"
            f"{ocr_text}"
        )

        try:
            return self._generate(prompt)
        except Exception as e:
            return f"AI Parsing unavailable (provider={self.provider}, model={self.model}): {str(e)}"
