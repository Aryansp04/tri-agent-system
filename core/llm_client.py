"""
Lightweight client for Google Gemini API using standard library urllib.
Requires zero external dependencies.
"""
import json
import os
from typing import Optional, Dict, Any, List
import urllib.request
import urllib.error


class GeminiClient:
    DEFAULT_MODEL = "gemini-2.5-flash"
    FALLBACK_MODELS = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-flash-latest",
        "gemini-1.5-pro",
        "gemini-2.0-flash-exp"
    ]
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    # Default key is loaded at runtime from GEMINI_API_KEY environment variable
    DEFAULT_API_KEY = ""

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        self.api_key = (api_key or os.environ.get("GEMINI_API_KEY", "")).strip().strip('"').strip("'") or self.DEFAULT_API_KEY
        self.model = model

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def discover_models(self, key: str) -> List[str]:
        """
        Dynamically query Google Gemini ListModels API to discover valid model names
        supported by this API key.
        """
        url = f"{self.BASE_URL}?key={key}"
        try:
            req = urllib.request.Request(url, headers={"Content-Type": "application/json"}, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = data.get("models", [])
                valid_models = []
                for m in models:
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        name = m.get("name", "").replace("models/", "")
                        if name:
                            valid_models.append(name)
                # Prioritize flash models
                flash_models = [m for m in valid_models if "flash" in m]
                other_models = [m for m in valid_models if "flash" not in m]
                return flash_models + other_models
        except Exception:
            return []

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.4,
        max_output_tokens: int = 2048,
        api_key_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call the Gemini generateContent REST API with dynamic model discovery & automatic fallbacks.
        Returns {"success": True, "text": "...", "model": "..."} or {"success": False, "error": "..."}
        """
        key = (api_key_override or self.api_key or "").strip().strip('"').strip("'")
        if not key:
            return {
                "success": False,
                "error": "No Gemini API key provided. Set GEMINI_API_KEY environment variable in Vercel or locally."
            }

        # 1. Discover models live for this key if possible
        discovered = self.discover_models(key)
        
        # 2. Build candidate list prioritizing discovered models, then defaults
        candidate_list = []
        if self.model and self.model in discovered:
            candidate_list.append(self.model)
        for m in discovered:
            if m not in candidate_list:
                candidate_list.append(m)
        for m in [self.model] + self.FALLBACK_MODELS:
            if m and m not in candidate_list:
                candidate_list.append(m)

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

        for model_candidate in candidate_list:
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
                    continue
            except urllib.error.HTTPError as e:
                err_msg = e.read().decode("utf-8")
                try:
                    err_json = json.loads(err_msg)
                    detail = err_json.get("error", {}).get("message", err_msg)
                except Exception:
                    detail = err_msg
                last_error = f"Gemini API HTTP {e.code}: {detail}"
                # If API key is invalid/unauthorized (400 / 401 / 403), stop immediately and report exact error
                if e.code in (400, 401, 403) and "API key" in detail:
                    return {"success": False, "error": last_error}
                continue
            except Exception as e:
                last_error = f"Connection error calling Gemini API: {str(e)}"
                continue

        return {"success": False, "error": last_error}
