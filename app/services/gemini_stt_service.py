"""
Gemini STT (speech-to-text) service using Gemini 2.5 Flash with load balancing
across multiple Google API keys.
"""

import os
from typing import Optional, List

from loguru import logger
from google import genai
from google.genai import types

from core.config import get_settings


class GeminiKeyBalancer:
    """Round-robin load balancer for multiple Gemini STT API keys."""

    def __init__(self, keys: List[str]):
        if not keys:
            raise ValueError("No Google STT keys provided")

        # Clean and store keys
        self.keys = [k.strip() for k in keys if k.strip()]
        self.index = 0
        self.total = len(self.keys)

    def next_key(self) -> str:
        """Return the next API key in round-robin fashion."""
        key = self.keys[self.index]
        self.index = (self.index + 1) % self.total
        return key


class GeminiSTTService:
    """Service to transcribe audio files using Gemini API with multi-key load balancing."""

    def __init__(self):
        self.settings = get_settings()

        # Accept comma-separated or list of keys
        keys = self.settings.google_stt_keys
        if isinstance(keys, str):
            keys = [k.strip() for k in keys.split(",")]

        self.lb = GeminiKeyBalancer(keys)
        self.model = "gemini-2.5-flash"

    def _get_client(self):
        """Fetch a new Gemini client using the next API key."""
        return genai.Client(api_key=self.lb.next_key())

    def _guess_mime_type(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in (".mp3", ".mpeg"):
            return "audio/mp3"
        if ext == ".wav":
            return "audio/wav"
        if ext == ".ogg":
            return "audio/ogg"
        if ext == ".flac":
            return "audio/flac"
        if ext == ".aac":
            return "audio/aac"
        if ext in (".aiff", ".aif"):
            return "audio/aiff"
        return "audio/mp3"

    async def transcribe(self, file_path: str, language: str, prompt: Optional[str] = None) -> str:
        """Transcribe audio file and return plain text."""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Audio file not found: {file_path}")

            mime = self._guess_mime_type(file_path)

            # Use load-balanced API key
            client = self._get_client()

            # Upload audio via Files API
            uploaded = client.files.upload(file=file_path)

            user_prompt = (
                prompt
                or "Transcribe the audio EXACTLY as spoken. Do NOT translate. Do NOT interpret. "
                "Keep the original language exactly the same. Output only the transcript."
            )

            response = client.models.generate_content(
                model=self.model,
                contents=[user_prompt, uploaded],
                
            )
            logger.info(f"Gemini STT response: {response}")

            # Preferred text
            if hasattr(response, "text") and response.text:
                return response.text.strip()

            # Fallback aggregation
            aggregated = []
            for cand in getattr(response, "candidates", []) or []:
                parts = getattr(cand.content, "parts", []) if cand.content else []
                for part in parts:
                    if hasattr(part, "text") and part.text:
                        aggregated.append(part.text)

            if aggregated:
                return "\n".join(s.strip() for s in aggregated if s.strip())

            return ""

        except Exception as e:
            logger.error(f"Gemini STT error: {e}")
            return ""


# Global service instance
_gemini_stt_service = GeminiSTTService()

def get_gemini_stt_service() -> GeminiSTTService:
    return _gemini_stt_service
