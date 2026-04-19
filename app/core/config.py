"""
Configuration management for KisanVoice
"""

import os
from typing import Optional, List
from pydantic import Field, field_validator, AliasChoices
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    groq_api_key: str = Field(..., description="Groq API key for LLM and STT")
    google_image_keys: str = Field(
        ..., 
        description="Google API key for vision LLM",
        validation_alias=AliasChoices("GOOGLE_IMAGE_KEYS", "GOOGLE_IMAGE", "google_image_keys", "google_image")
    )
    google_stt_keys: str = Field(
        ..., 
        description="Google API key for STT",
        validation_alias=AliasChoices("GOOGLE_STT_KEYS", "GOOGLE_STT", "google_stt_keys", "google_stt")
    )
    elevenlabs_api_key: str = Field(..., description="ElevenLabs API key for TTS")
    openweather_api_key: str = Field(..., description="OpenWeather API key")
    
    # Application Configuration
    app_name: str = Field(default="KisanVoice", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Log level")
    
    # Language Configuration
    default_language: str = Field(default="kn", description="Default language")
    supported_languages: str = Field(default="kn,en", description="Supported languages")
    
    # Model Configuration
    text_model: str = Field(default="llama-3.3-70b-versatile", description="Text generation model")
    vision_model: str = Field(default="llama-3.2-90b-vision-preview", description="Vision model")
    tts_voice_id: str = Field(default="21m00Tcm4TlvDq8ikWAM", description="ElevenLabs voice ID")
    
    # Memory Configuration
    qdrant_url: str = Field(default="http://localhost:6333", description="Qdrant URL")
    qdrant_api_key: Optional[str] = Field(None, description="Qdrant API key (optional for local)")
    sqlite_database_url: str = Field(default="sqlite:///./kisanvoice.db", description="SQLite database URL")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL")
    
    # API Configuration
    openweather_base_url: str = Field(default="https://api.openweathermap.org/data/2.5", description="OpenWeather base URL")
    groq_base_url: str = Field(default="https://api.groq.com/openai/v1", description="Groq API base URL")
    elevenlabs_base_url: str = Field(default="https://api.elevenlabs.io/v1", description="ElevenLabs API base URL")
    
    # Twilio (WhatsApp) Configuration
    twilio_account_sid: str = Field(default="", description="Twilio Account SID for WhatsApp")
    twilio_auth_token: str = Field(default="", description="Twilio Auth Token for WhatsApp")
    twilio_whatsapp_from: str = Field(default="", description="Twilio WhatsApp sender, e.g., whatsapp:+14155238886")
    
    # Validation - Updated for Pydantic V2
    @field_validator('groq_api_key', 'elevenlabs_api_key', 'openweather_api_key')
    @classmethod
    def validate_required_api_keys(cls, v: str, info) -> str:
        # Allow placeholder values for development
        if v in [f"your_{info.field_name}_here", "test_key_for_validation"]:
            return v
        if not v:
            raise ValueError(f"{info.field_name} is required")
        return v
    
    # Updated for Pydantic V2
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings
