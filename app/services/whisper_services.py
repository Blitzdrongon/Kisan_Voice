import os
import tempfile
from typing import Optional

from loguru import logger
from core.config import get_settings


class SpeechToText:
    """Handle speech-to-text using Groq Whisper via HTTP API, aligned with workflow."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.api_key = self.settings.groq_api_key
        self.base_url = "https://api.groq.com/openai/v1"
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")

    async def transcribe_file(self, audio_file_path: str, language: str = "auto") -> str:
        """Transcribe a local audio file path using Whisper."""
        try:
            import httpx

            if not audio_file_path or not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

            with open(audio_file_path, "rb") as audio_file:
                files = {"file": (os.path.basename(audio_file_path), audio_file, "application/octet-stream")}
                # Use Groq Whisper model name compatible with OpenAI endpoint
                data = {"model": "whisper-large-v3-turbo"}
                if language and language != "auto":
                    data["language"] = language
                headers = {"Authorization": f"Bearer {self.api_key}"}

                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/audio/transcriptions",
                        files=files,
                        data=data,
                        headers=headers,
                        timeout=60.0,
                    )

            if response.status_code == 200:
                result = response.json()
                text = result.get("text", "").strip()
                #language = result.get("language", "").strip()
                logger.info("Whisper transcription successful")
                #logger.info(f"Whisper language: {language}")    
                logger.info(f"Whisper transcription: {text}")
                return text
            else:
                logger.error(f"Whisper transcription failed: {response.status_code} - {response.text}")
                return "" , ""
        except Exception as e:
            logger.error(f"STT transcribe_file error: {e}")
            return "",""

    async def transcribe_bytes(self, audio_data: bytes, language: str = "auto") -> str:
        """Transcribe in-memory audio bytes by writing to a temp file first."""
        if not audio_data:
            return ""
        temp_path: Optional[str] = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_data)
                temp_path = tmp.name
            return await self.transcribe_file(temp_path, language=language)
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass


# Global instance and accessor
_whisper_service: Optional[SpeechToText] = None


def get_whisper_service() -> SpeechToText:
    global _whisper_service
    if _whisper_service is None:
        _whisper_service = SpeechToText()
    return _whisper_service