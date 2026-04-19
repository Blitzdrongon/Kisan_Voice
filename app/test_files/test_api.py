#!/usr/bin/env python3
"""
Test script to check API keys and services
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from dotenv import load_dotenv
load_dotenv()

def test_env_vars():
    """Test environment variables"""
    print("🔍 Testing Environment Variables:")
    print(f"GROQ_API_KEY: {'✅ Set' if os.getenv('GROQ_API_KEY') and os.getenv('GROQ_API_KEY') != 'your_groq_api_key_here' else '❌ Not set or placeholder'}")
    print(f"ELEVENLABS_API_KEY: {'✅ Set' if os.getenv('ELEVENLABS_API_KEY') and os.getenv('ELEVENLABS_API_KEY') != 'your_elevenlabs_api_key_here' else '❌ Not set or placeholder'}")
    print(f"OPENWEATHER_API_KEY: {'✅ Set' if os.getenv('OPENWEATHER_API_KEY') and os.getenv('OPENWEATHER_API_KEY') != 'your_openweather_api_key_here' else '❌ Not set or placeholder'}")
    print(f"GOOGLE_API_KEY: {'✅ Set' if os.getenv('GOOGLE_API_KEY') and os.getenv('GOOGLE_API_KEY') != 'your_google_api_key_here' else '❌ Not set or placeholder'}")
    print()

def test_services():
    """Test service initialization"""
    print("🔍 Testing Services:")
    
    try:
        from core.config import get_settings
        settings = get_settings()
        print("✅ Settings loaded")
        
        # Test Groq service
        try:
            from services.groq_service import get_groq_service
            groq_service = get_groq_service()
            print("✅ Groq service initialized")
            
            # Test a simple API call
            try:
                import asyncio
                response = asyncio.run(groq_service.generate_text("Hello", language="en"))
                print(f"✅ Groq API test: {response[:50]}...")
            except Exception as e:
                print(f"❌ Groq API test failed: {e}")
                
        except Exception as e:
            print(f"❌ Groq service failed: {e}")

        
        # Test ElevenLabs service
        try:
            from services.elevenlabs_service import get_elevenlabs_service
            elevenlabs_service = get_elevenlabs_service()
            print("✅ ElevenLabs service initialized")
        except Exception as e:
            print(f"❌ ElevenLabs service failed: {e}")
        
        # Test workflow
        try:
            from core.workflow import get_workflow
            workflow = get_workflow()
            print("✅ Workflow initialized")
        except Exception as e:
            print(f"❌ Workflow failed: {e}")
            
    except Exception as e:
        print(f"❌ Service test failed: {e}")
    
    print()

if __name__ == "__main__":
    test_env_vars()
    test_services()
