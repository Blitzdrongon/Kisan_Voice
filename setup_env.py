#!/usr/bin/env python3
"""
Environment setup script for KisanVoice
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file with required variables"""
    
    env_content = """# KisanVoice Environment Configuration

# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here

# ElevenLabs API Configuration (for Text-to-Speech)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# OpenWeather API Configuration
OPENWEATHER_API_KEY=your_openweather_api_key_here

# Application Configuration
APP_NAME=KisanVoice
APP_VERSION=1.0.0
DEBUG=true
LOG_LEVEL=INFO

# Language Configuration
DEFAULT_LANGUAGE=kn
SUPPORTED_LANGUAGES=kn,en

# Model Configuration
TEXT_MODEL=llama-3.3-70b-versatile
VISION_MODEL=llama-3.2-90b-vision-preview
TTS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# Memory Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
SQLITE_DATABASE_URL=sqlite:///./kisanvoice.db

# Redis Configuration
REDIS_URL=redis://localhost:6379

# API Base URLs
OPENWEATHER_BASE_URL=https://api.openweathermap.org/data/2.5
GROQ_BASE_URL=https://api.groq.com/openai/v1
ELEVENLABS_BASE_URL=https://api.elevenlabs.io/v1
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write(env_content)
        print("✅ Created .env file")
        print("📝 Please edit .env file and add your API keys:")
        print("   - GROQ_API_KEY: Get from https://console.groq.com/")
        print("   - ELEVENLABS_API_KEY: Get from https://elevenlabs.io/")
        print("   - OPENWEATHER_API_KEY: Get from https://openweathermap.org/")
    else:
        print("✅ .env file already exists")

def test_imports():
    """Test if all required modules can be imported"""
    
    print("\n🔍 Testing imports...")
    
    try:
        # Test basic imports
        import chainlit as cl
        print("✅ chainlit imported successfully")
        
        # Test app imports
        sys.path.insert(0, str(Path("app")))
        
        from core.config import get_settings
        print("✅ config imported successfully")
        
        from services.groq_service import get_groq_service
        print("✅ groq_service imported successfully")
        
        from services.elevenlabs_service import get_elevenlabs_service
        print("✅ elevenlabs_service imported successfully")
        
        from core.workflow import get_workflow
        print("✅ workflow imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_services():
    """Test service initialization"""
    
    print("\n🔍 Testing services...")
    
    try:
        from core.config import get_settings
        settings = get_settings()
        print("✅ Settings loaded")
        
        # Test Groq service
        from services.groq_service import get_groq_service
        groq_service = get_groq_service()
        print("✅ Groq service initialized")
        
        # Test ElevenLabs service
        from services.elevenlabs_service import get_elevenlabs_service
        elevenlabs_service = get_elevenlabs_service()
        print("✅ ElevenLabs service initialized")
        
        # Test workflow
        from core.workflow import get_workflow
        workflow = get_workflow()
        print("✅ Workflow initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Service error: {e}")
        return False

def main():
    """Main setup function"""
    
    print("🌾 KisanVoice Setup Script")
    print("=" * 40)
    
    # Create .env file
    create_env_file()
    
    # Test imports
    if not test_imports():
        print("\n❌ Setup failed: Import errors")
        return
    
    # Test services
    if not test_services():
        print("\n❌ Setup failed: Service errors")
        print("💡 Make sure to add your API keys to the .env file")
        return
    
    print("\n✅ Setup completed successfully!")
    print("\n🚀 To run the application:")
    print("   1. Add your API keys to .env file")
    print("   2. Run: chainlit run app/main.py")
    print("   3. Open: http://localhost:8000")

if __name__ == "__main__":
    main()
