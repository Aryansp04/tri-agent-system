"""
Lightweight client for Google Gemini API using standard library urllib.
Requires zero external dependencies.
"""
import json
import os
from typing import Optional, Dict, Any
import urllib.request
import urllib.error


class GeminiClient:
    DEFAULT_MODEL = "gemini-3.6-flash"
    FALLBACK_MODELS = ["gemini-3.6-flash", "gemini-3.8-flash", "gemini-flash-latest"]
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    # Default key is loaded at runtime from GEMINI_API_KEY environment variable
    # (set via .env locally or via Vercel Environment Variables in production)
    DEFAULT_API_KEY = ""

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "").strip() or self.DEFAULT_API_KEY
        self.model = model

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.4,
        max_output_tokens: int = 2048,
        api_key_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call the Gemini generateContent REST API.
        Returns {"success": True, "text": "...", "model": "..."} or {"success": False, "error": "..."}
        """
        key = api_key_override or self.api_key
        if not key:
            return {
                "success": False,
                "error": "No Gemini API key provided. Set GEMINI_API_KEY env var or enter it in the Web UI."
            }

        models_to_try = [self.model] + [m for m in self.FALLBACK_MODELS if m != self.model]
        last_error = ""

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        data = json.dumps(payload).encode("utf-8")

        for model_candidate in models_to_try:
            url = f"{self.BASE_URL}/{model_candidate}:generateContent?key={key}"
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    candidates = resp_data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        text_parts = [p.get("text", "") for p in parts if "text" in p]
                        text = "".join(text_parts).strip()
                        if text:
                            self.model = model_candidate
                            return {
                                "success": True,
                                "text": text,
                                "model": model_candidate
                            }
                    return {"success": False, "error": "Empty or unexpected response format from Gemini API."}
            except urllib.error.HTTPError as e:
                err_msg = e.read().decode("utf-8")
                try:
                    err_json = json.loads(err_msg)
                    detail = err_json.get("error", {}).get("message", err_msg)
                except Exception:
                    detail = err_msg
                last_error = f"Gemini API HTTP {e.code}: {detail}"
                if e.code == 404:
                    # Model not found or deprecated for this key; try next candidate
                    continue
                return {"success": False, "error": last_error}
            except Exception as e:
                return {"success": False, "error": f"Connection error calling Gemini API: {str(e)}"}

        return {"success": False, "error": last_error}
