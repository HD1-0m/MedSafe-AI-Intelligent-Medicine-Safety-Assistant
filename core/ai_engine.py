import os
import base64
import json
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

import ollama


class AIEngine:
    """
    Handles LLM interactions with either Ollama (local) or Gemini (API).
    """

    def __init__(self, model: Optional[str] = None, provider: Optional[str] = None):
        self.provider = (provider or os.getenv("AI_PROVIDER", "ollama")).strip().lower()
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
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

    def _gemini_generate_with_image(self, prompt: str, image_bytes: bytes, mime_type: str) -> str:
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is missing. Please set it in your environment/.env.")

        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.gemini_api_key}"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": image_b64,
                            }
                        },
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
        with urllib.request.urlopen(req, timeout=30) as resp:
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

    def explain_risk(self, severity: str, reasons: List[str]) -> str:
        """
        Conversational safety guidance for interaction/symptom risks.
        """
        risk_data = {"severity": severity, "reasons": reasons}
        prompt = (
            "You are MedSafe AI, an educational medicine safety assistant. "
            "Explain the risk in a calm, simple paragraph. "
            "Include: what it means, what to monitor, and when to seek medical help. "
            "Do not diagnose and do not prescribe treatment. "
            f"Risk details: {json.dumps(risk_data)}"
        )
        try:
            return self._generate(prompt)
        except Exception as e:
            return (
                f"AI risk explanation unavailable (provider={self.provider}, model={self.model}): {str(e)}"
            )

    def solve_symptoms(self, symptoms_text: str, risk_data: Dict) -> str:
        """
        Educational symptom and doubt solver output.
        """
        prompt = (
            "You are an educational health assistant. "
            "Given user symptoms and a rule-based risk signal, provide: "
            "1) likely non-diagnostic possibilities in plain language, "
            "2) safe self-care tips, "
            "3) warning signs for urgent care. "
            "Keep it concise and non-alarmist. "
            f"Symptoms: {symptoms_text}\n"
            f"Risk signal: {json.dumps(risk_data)}"
        )
        try:
            return self._generate(prompt)
        except Exception as e:
            return f"AI symptom guidance unavailable (provider={self.provider}, model={self.model}): {str(e)}"

    def monitor_side_effects(
        self,
        age: int,
        gender: str,
        medicines: List[str],
        doses: List[str],
        experience: str,
        rule_assessment: Dict,
    ) -> str:
        """
        AI enhancement for side-effect monitoring.
        """
        payload = {
            "age": age,
            "gender": gender,
            "medicines": medicines,
            "doses": doses,
            "experience": experience,
            "rule_assessment": rule_assessment,
        }
        prompt = (
            "You are MedSafe AI. Analyze this side-effect report for educational awareness only. "
            "Return concise guidance with sections: Summary, Risk cues, Precaution, Escalation signs. "
            "Do not provide diagnosis or medication changes. "
            f"Input: {json.dumps(payload)}"
        )
        try:
            return self._generate(prompt)
        except Exception as e:
            return (
                f"AI side-effect analysis unavailable (provider={self.provider}, model={self.model}): {str(e)}"
            )

    def predict_emergency_risk(
        self,
        emergency_symptoms: str,
        medical_history: str,
        rule_assessment: Dict,
    ) -> str:
        """
        AI explanation for emergency risk context.
        """
        prompt = (
            "You are an emergency awareness assistant. "
            "Based on the symptom description, medical history, and rule-based score, provide "
            "clear triage-oriented educational guidance. Include urgency level and immediate safe next steps. "
            "Do not diagnose. Mention to call local emergency services for severe red flags. "
            f"Symptoms: {emergency_symptoms}\n"
            f"History: {medical_history}\n"
            f"Rule assessment: {json.dumps(rule_assessment)}"
        )
        try:
            return self._generate(prompt)
        except Exception as e:
            return (
                f"AI emergency risk analysis unavailable (provider={self.provider}, model={self.model}): {str(e)}"
            )

    def parse_prescription(self, ocr_text: str) -> str:
        """
        Uses AI to parse OCR text into strict JSON format.
        """
        schema_hint = {
            "medicines": [
                {
                    "medicine_name": "string",
                    "active_ingredient_or_salt": "string",
                    "dosage": "string",
                    "frequency": "string",
                    "duration": "string",
                    "notes": "string",
                }
            ]
        }
        prompt = (
            "Extract medicines and active drug/salt components from this prescription OCR text.\n"
            "Return STRICT JSON ONLY. No markdown, no commentary, no code fences.\n"
            "Output schema must be exactly: "
            f"{json.dumps(schema_hint)}\n"
            "Rules:\n"
            "- If a field is missing, use empty string.\n"
            "- Use one object per medicine.\n"
            "- Keep values concise and faithful to OCR text.\n"
            "OCR text:\n"
            f"{ocr_text}"
        )

        try:
            raw = self._generate(prompt)
            parsed = self._parse_json_strict(raw)
            return json.dumps(parsed, indent=2)
        except Exception as e:
            return json.dumps(
                {
                    "error": (
                        f"AI Parsing unavailable (provider={self.provider}, model={self.model}): {str(e)}"
                    ),
                    "medicines": [],
                },
                indent=2,
            )

    def parse_prescription_from_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        ocr_text: str = "",
    ) -> str:
        """
        Multimodal parsing:
        1) Tesseract raw OCR is provided as noisy context.
        2) Gemini reconstructs clearer text and returns strict JSON.
        Falls back to OCR-text-only parser when needed.
        """
        schema_hint = {
            "reconstructed_text": "cleaned prescription text",
            "medicines": [
                {
                    "medicine_name": "string",
                    "active_ingredient_or_salt": "string",
                    "dosage": "string",
                    "frequency": "string",
                    "duration": "string",
                    "notes": "string",
                }
            ],
        }
        prompt = (
            "Extract medicine names and dosages from this prescription image. "
            "If handwriting is unclear, try your best to decipher it conservatively.\n"
            "You are given noisy Tesseract OCR as additional context.\n"
            "Return STRICT JSON ONLY (no markdown).\n"
            f"Required schema: {json.dumps(schema_hint)}\n"
            "Rules:\n"
            "- Do not invent medicines that are not visually or textually plausible.\n"
            "- If uncertain, keep notes explaining ambiguity.\n"
            "- Keep reconstructed_text concise and readable.\n"
            f"Noisy OCR context:\n{ocr_text}"
        )
        try:
            if self.provider == "gemini":
                raw = self._gemini_generate_with_image(prompt, image_bytes, mime_type)
                parsed = self._parse_json_with_reconstruction(raw)
                return json.dumps(parsed, indent=2)
            return self.parse_prescription(ocr_text)
        except Exception:
            return self.parse_prescription(ocr_text)

    def _parse_json_strict(self, raw_text: str) -> Dict[str, Any]:
        """
        Parse model output into strict JSON object with required schema.
        """
        text = (raw_text or "").strip()
        if not text:
            raise ValueError("Model returned empty output.")

        # Strip markdown fences if model accidentally returns them.
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]

        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("JSON root must be an object.")

        medicines = parsed.get("medicines", [])
        if not isinstance(medicines, list):
            medicines = []

        normalized = []
        required_fields = [
            "medicine_name",
            "active_ingredient_or_salt",
            "dosage",
            "frequency",
            "duration",
            "notes",
        ]
        for item in medicines:
            if not isinstance(item, dict):
                continue
            cleaned = {field: str(item.get(field, "") or "").strip() for field in required_fields}
            if cleaned["medicine_name"]:
                normalized.append(cleaned)

        return {"medicines": normalized}

    def analyze_unknown_interactions(self, medicine_names: List[str]) -> Dict[str, Any]:
        """
        AI fallback interaction analysis for medicines not present in local DB.
        """
        cleaned_names = [name.strip() for name in medicine_names if name and name.strip()]
        if len(cleaned_names) < 2:
            return {
                "interactions": [],
                "advice": "Please provide at least two medicines for interaction analysis.",
            }

        schema_hint = {
            "interactions": [
                {
                    "pair": ["medicine_a", "medicine_b"],
                    "risk": "LOW|MEDIUM|HIGH",
                    "description": "detailed clinical interaction description",
                }
            ],
            "advice": "clear non-diagnostic safety advice",
        }
        prompt = (
            f"Check for potential drug-drug interactions between these medicines: {', '.join(cleaned_names)}.\n"
            "Identify the risk level (LOW, MEDIUM, HIGH) and provide a detailed clinical description of the interaction.\n"
            "If no interactions are found, state that clearly.\n"
            "Return STRICT JSON ONLY and no markdown.\n"
            f'Format as JSON with keys: "interactions" (array of objects with keys '
            f'"pair" (array of 2 strings), "risk" (string), "description" (string)), '
            f'"advice" (string).\n'
            f"Example schema: {json.dumps(schema_hint)}"
        )
        try:
            raw = self._generate(prompt)
            parsed = self._parse_json_interaction(raw)
            return parsed
        except Exception as e:
            return {
                "interactions": [],
                "advice": (
                    "AI fallback could not complete confident interaction extraction. "
                    f"Please verify with a pharmacist or doctor. Technical detail: {str(e)}"
                ),
            }

    def _parse_json_interaction(self, raw_text: str) -> Dict[str, Any]:
        text = (raw_text or "").strip()
        if not text:
            raise ValueError("Model returned empty interaction output.")

        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]

        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("Interaction JSON root must be an object.")

        interactions = parsed.get("interactions", [])
        if not isinstance(interactions, list):
            interactions = []

        normalized = []
        for item in interactions:
            if not isinstance(item, dict):
                continue
            pair = item.get("pair", [])
            if not isinstance(pair, list) or len(pair) != 2:
                continue
            pair_values = [str(pair[0]).strip(), str(pair[1]).strip()]
            if not pair_values[0] or not pair_values[1]:
                continue

            risk = str(item.get("risk", "MEDIUM")).upper().strip()
            if risk not in {"LOW", "MEDIUM", "HIGH"}:
                risk = "MEDIUM"

            description = str(item.get("description", "") or "").strip()
            if not description:
                description = "Potential interaction risk detected by AI fallback."

            normalized.append(
                {"pair": pair_values, "risk": risk, "description": description}
            )

        advice = str(parsed.get("advice", "") or "").strip()
        if not advice:
            advice = "Use caution and seek professional review for confirmation."

        return {"interactions": normalized, "advice": advice}

    def _parse_json_with_reconstruction(self, raw_text: str) -> Dict[str, Any]:
        text = (raw_text or "").strip()
        if not text:
            raise ValueError("Model returned empty prescription output.")

        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]

        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("Prescription JSON root must be an object.")

        base = self._parse_json_strict(text)
        reconstructed_text = str(parsed.get("reconstructed_text", "") or "").strip()
        return {
            "reconstructed_text": reconstructed_text,
            "medicines": base.get("medicines", []),
        }
