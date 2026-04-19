"""
Main Chainlit application for KisanVoice
"""

import os
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from io import BytesIO

import chainlit as cl
from loguru import logger

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import our services using relative imports
from core.config import get_settings
from core.memory import get_memory_manager
from core.workflow import get_workflow
from services.groq_service import get_groq_service
from services.elevenlabs_service import get_elevenlabs_service
from services.weather_service import get_weather_service

# Initialize services and components
settings = get_settings()
memory_manager = get_memory_manager()
workflow = get_workflow()
groq_service = get_groq_service()
elevenlabs_service = get_elevenlabs_service()
weather_service = get_weather_service()

# Create uploads directory
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

# User session management
user_sessions: Dict[str, Dict[str, Any]] = {}

@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session"""
    try:
        # Get user session info
        user_id = cl.user_session.get("id", "anonymous")
        session_id = f"session_{user_id}_{datetime.now().isoformat()}"
        
        # Initialize user session
        user_sessions[user_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "language": "kn",  # Default to Kannada
            "created_at": datetime.now().isoformat(),
            "conversation_history": []
        }
        
        # Set thread_id for compatibility
        cl.user_session.set("thread_id", session_id)
        
        # Welcome message in both languages
        welcome_msg = """
🌾 **ರೈತಮಿತ್ರ (KisanVoice)** - Your Agricultural AI Assistant

ನಮಸ್ಕಾರ! ನಾನು ರೈತಮಿತ್ರ, ನಿಮ್ಮ ಕೃಷಿ ಸಹಾಯಕ.
Hello! I am KisanVoice, your agricultural assistant.

**ನನ್ನ ಸೌಲಭ್ಯಗಳು / My Features:**
🌾 ಕೃಷಿ ಸಲಹೆಗಳು ಮತ್ತು ಮಾಹಿತಿ / Agricultural advice and information
🌤️ ಹವಾಮಾನ ಮಾಹಿತಿ / Weather information  
📸 ಚಿತ್ರ ವಿಶ್ಲೇಷಣೆ / Image analysis
🎤 ಧ್ವನಿ ಸಂವಾದ / Voice conversation (Click the microphone!)
💾 ಸಂವಾದ ಇತಿಹಾಸ / Conversation history

**ಭಾಷೆಗಳು / Languages:** ಕನ್ನಡ (Kannada) ಮತ್ತು ಇಂಗ್ಲಿಷ್ (English)

ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಕನ್ನಡ ಅಥವಾ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಕೇಳಿ!
Ask your question in Kannada or English!

🎤 **Voice Input:** Click the microphone icon to speak!
        """
        
        await cl.Message(
            content=welcome_msg,
            author="KisanVoice"
        ).send()
        
        logger.info(f"Chat session started for user: {user_id}")
        
    except Exception as e:
        logger.error(f"Error starting chat session: {e}")
        await cl.Message(
            content="ಕ್ಷಮಿಸಿ, ಚಾಟ್ ಪ್ರಾರಂಭಿಸಲು ದೋಷ ಸಂಭವಿಸಿದೆ. / Sorry, an error occurred starting the chat.",
            author="KisanVoice"
        ).send()

@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages"""
    try:
        user_id = cl.user_session.get("id", "anonymous")
        user_session = user_sessions.get(user_id, {})
        session_id = user_session.get("session_id", f"session_{user_id}")
        language = user_session.get("language", "kn")
        
        # Get user input
        user_input = message.content
        
        # Handle audio if present
        if message.elements:
            for element in message.elements:
                if element.type == "audio":
                    # Process audio input
                    audio_data = element.content
                    audio_mime_type = element.mime_type or "audio/mpeg"
                    
                    # Show user's audio message
                    input_audio_el = cl.Audio(mime=audio_mime_type, content=audio_data)
                    await cl.Message(author="You", content="", elements=[input_audio_el]).send()

                    # Save audio file temporarily for transcription
                    audio_filename = f"voice_input_{uuid.uuid4()}.wav"
                    audio_path = UPLOADS_DIR / audio_filename
                    
                    with open(audio_path, "wb") as f:
                        f.write(audio_data)

                    # Transcribe audio using Groq
                    try:
                        transcribed_text = await groq_service.transcribe_audio(str(audio_path))
                        
                        if transcribed_text:
                            # Show transcribed text
                            await cl.Message(
                                content=f"🎤 **Voice Input:** {transcribed_text}",
                                author="You"
                            ).send()
                            
                            # Use transcribed text as user input
                            user_input = transcribed_text
                        else:
                            await cl.Message(
                                content="🎤 Sorry, I couldn't understand your voice. Please try again or type your message.",
                                author="KisanVoice"
                            ).send()
                            return
                            
                    except Exception as e:
                        logger.error(f"Error transcribing audio: {e}")
                        await cl.Message(
                            content="🎤 Sorry, there was an error processing your voice input. Please try typing instead.",
                            author="KisanVoice"
                        ).send()
                        return
                    
                    finally:
                        # Clean up temporary audio file
                        if os.path.exists(audio_path):
                            os.remove(audio_path)
                    
                    break  # Exit after processing audio
        
        # Handle image if present
        image_url = None
        if message.elements:
            for element in message.elements:
                if element.type == "image":
                    # Save image to uploads
                    image_filename = f"image_{uuid.uuid4()}.jpg"
                    image_path = UPLOADS_DIR / image_filename
                    
                    # Save image data
                    with open(image_path, "wb") as f:
                        f.write(element.content)
                    
                    image_url = str(image_path)
                    
                    # Analyze image and add to message content
                    try:
                        # Use Groq for image analysis
                        image_description = await groq_service.analyze_image(
                            image_path,
                            "Please describe what you see in this image in the context of our agricultural conversation."
                        )
                        user_input += f"\n[Image Analysis: {image_description}]"
                    except Exception as e:
                        logger.warning(f"Failed to analyze image: {e}")
                    break
        
        # Detect language from input
        if user_input:
            # Simple language detection
            kannada_chars = set('ಅಆಇಈಉಊಋಎಏಐಒಔಕಖಗಘಙಚಛಜಝಞಟಠಡಢಣತಥದಧನಪಫಬಭಮಯರಲವಶಷಸಹಳಱೞ')
            if any(char in kannada_chars for char in user_input):
                language = "kn"
            else:
                language = "en"
            
            # Update session language
            user_sessions[user_id]["language"] = language
        
        # Process message using workflow
        response = await workflow.run_conversation(
            user_input=user_input,
            session_id=session_id,
            user_id=user_id,
            language=language,
            image_url=image_url
        )
        
        # Send text response
        assistant_response = response.get("assistant_response", "")
        if assistant_response:
            await cl.Message(
                content=assistant_response,
                author="KisanVoice"
            ).send()
        
        # Send audio response if generated
        audio_path = response.get("audio_path")
        if audio_path and os.path.exists(audio_path):
            try:
                with open(audio_path, "rb") as audio_file:
                    audio_data = audio_file.read()
                
                await cl.Message(
                    content="",
                    elements=[
                        cl.Audio(
                            name="Response Audio",
                            content=audio_data,
                            mime_type="audio/mpeg",
                            auto_play=True
                        )
                    ],
                    author="KisanVoice"
                ).send()
                
                # Clean up audio file
                os.remove(audio_path)
                
            except Exception as e:
                logger.error(f"Error sending audio: {e}")
        
        # Update session
        user_sessions[user_id]["conversation_history"].append({
            "user_input": user_input,
            "assistant_response": assistant_response,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Message processed for user: {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        error_msg = "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ಸಂದೇಶವನ್ನು ಸಂಸ್ಕರಿಸಲು ದೋಷ ಸಂಭವಿಸಿದೆ." if language == "kn" else "Sorry, an error occurred processing your message."
        await cl.Message(
            content=error_msg,
            author="KisanVoice"
        ).send()

# Audio handling is now integrated into the main on_message handler

@cl.on_chat_end
async def on_chat_end():
    """Handle chat session end"""
    try:
        user_id = cl.user_session.get("id", "anonymous")
        if user_id in user_sessions:
            del user_sessions[user_id]
        
        logger.info(f"Chat session ended for user: {user_id}")
        
    except Exception as e:
        logger.error(f"Error ending chat session: {e}")

if __name__ == "__main__":
    # This will be handled by Chainlit
    pass
