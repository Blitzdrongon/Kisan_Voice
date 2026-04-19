"""
Gemini Flash TTS service with Load Balancing
"""

import base64
import io
import wave
from typing import Optional
from loguru import logger
from google import genai
from google.genai import types
from core.config import get_settings


class GeminiTTSService:
    """TTS service using Gemini with automatic load balancing."""

    def __init__(self):
        self.settings = get_settings()

        # Load multiple API keys for TTS
        raw_keys = self.settings.google_stt_keys
        self.api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]

        if not self.api_keys:
            raise ValueError("GOOGLE_TTS_KEYS not provided in environment variables")

        self.current_index = 0
        self.model = "gemini-2.5-flash-preview-tts"
        self.default_voice = "Puck"

        # Initialize with the first key
        self.client = self._create_client(self.api_keys[self.current_index])
        logger.info(f"Gemini TTS initialized with key index: {self.current_index}")

    def _create_client(self, key: str):
        """Create Gemini client for a specific key."""
        return genai.Client(api_key=key)

    def _rotate_key(self):
        """Switch to the next API key (round-robin)."""
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        new_key = self.api_keys[self.current_index]
        self.client = self._create_client(new_key)
        logger.warning(f"Gemini TTS switched to key index: {self.current_index}")

    async def _safe_api_call(self, func, *args, **kwargs):
        """
        Try executing the Gemini API call safely.
        If the current key fails, rotate to next key and retry.
        """
        attempts = len(self.api_keys)

        for attempt in range(attempts):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                logger.error(
                    f"TTS API key index {self.current_index} failed ({e}). "
                    f"Attempt {attempt + 1}/{attempts}."
                )
                self._rotate_key()

        raise RuntimeError("All TTS API keys failed. Check quota or network issues.")

    async def text_to_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: str = "kn",
        output_format: str = "wav",
    ) -> Optional[bytes]:

        try:
            if not text.strip():
                logger.warning("Gemini TTS called with empty text")
                return None

            voice_name = (voice_id or self.default_voice).strip()

            config = types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name
                        )
                    )
                ),
            )

            # PROTECTED API CALL
            response = await self._safe_api_call(
                self.client.models.generate_content,
                model=self.model,
                contents=text,
                config=config,
            )

            audio_payload = None

            try:
                for candidate in getattr(response, "candidates", []) or []:
                    parts = getattr(candidate, "content", None)
                    parts = getattr(parts, "parts", []) if parts else []
                    for part in parts:
                        inline = getattr(part, "inline_data", None)
                        if inline and getattr(inline, "data", None):
                            audio_payload = inline.data
                            break
                    if audio_payload:
                        break
            except Exception as parse_err:
                logger.warning(f"TTS parse warning: {parse_err}")

            if not audio_payload:
                logger.error("Gemini TTS returned no audio data")
                return None

            pcm_bytes = (
                audio_payload
                if isinstance(audio_payload, (bytes, bytearray))
                else base64.b64decode(str(audio_payload))
            )

            # Wrap PCM -> WAV
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(pcm_bytes)

            logger.info("Gemini TTS synthesis (WAV) succeeded")
            return wav_buffer.getvalue()

        except Exception as e:
            logger.error(f"Gemini TTS error: {e}")
            return None

    def save_audio_to_file(self, audio_data: bytes, file_path: str) -> bool:
        """Save WAV audio to disk."""
        try:
            with open(file_path, "wb") as f:
                f.write(audio_data)
            return True
        except Exception as e:
            logger.error(f"Error saving audio: {e}")
            return False


# Global instance
_gemini_tts_service = GeminiTTSService()


def get_gemini_tts_service() -> GeminiTTSService:
    return _gemini_tts_service
