"""
ElevenLabs service for text-to-speech
"""

import os
import base64
import json
from typing import Optional, Dict, Any
from pathlib import Path

import httpx
from loguru import logger

from core.config import get_settings


class ElevenLabsService:
    """Service for ElevenLabs Text-to-Speech"""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.elevenlabs_api_key
        self.base_url = self.settings.elevenlabs_base_url
        self.default_voice_id = self.settings.tts_voice_id
        
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def get_available_voices(self) -> Optional[Dict[str, Any]]:
        """Get list of available voices"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/voices",
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"ElevenLabs voices API error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching ElevenLabs voices: {e}")
            return None
    
    async def text_to_speech(
        self, 
        text: str, 
        voice_id: Optional[str] = None,
        language: str = "kn",
        output_format: str = "mp3"
    ) -> Optional[bytes]:
        """Convert text to speech using eleven_v3 model"""
        
        try:
            if not voice_id:
                voice_id = self.default_voice_id
            
            # Language-specific voice selection for Kannada
            if language == "kn":
                # Try to find a Kannada-compatible voice
                voices = await self.get_available_voices()
                if voices:
                    # Look for voices that might work well with Kannada
                    for voice in voices.get("voices", []):
                        if "indian" in voice.get("name", "").lower() or "south asian" in voice.get("description", "").lower():
                            voice_id = voice["voice_id"]
                            break
            
            payload = {
                "text": text,
                "model_id": "eleven_v3",  # Using the new alpha model
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/text-to-speech/{voice_id}",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(f"ElevenLabs TTS API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error in ElevenLabs TTS: {e}")
            return None
    
    async def text_to_speech_stream(
        self, 
        text: str, 
        voice_id: Optional[str] = None,
        language: str = "kn"
    ) -> Optional[httpx.Response]:
        """Convert text to speech with streaming using eleven_v3 model"""
        
        try:
            if not voice_id:
                voice_id = self.default_voice_id
            
            payload = {
                "text": text,
                "model_id": "eleven_v3",  # Using the new alpha model
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/text-to-speech/{voice_id}/stream",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    return response
                else:
                    logger.error(f"ElevenLabs TTS stream API error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error in ElevenLabs TTS streaming: {e}")
            return None
    
    def save_audio_to_file(self, audio_data: bytes, file_path: str) -> bool:
        """Save audio data to file"""
        
        try:
            with open(file_path, "wb") as f:
                f.write(audio_data)
            return True
        except Exception as e:
            logger.error(f"Error saving audio file: {e}")
            return False


# Global service instance
elevenlabs_service = ElevenLabsService()


def get_elevenlabs_service() -> ElevenLabsService:
    """Get ElevenLabs service instance"""
    return elevenlabs_service

