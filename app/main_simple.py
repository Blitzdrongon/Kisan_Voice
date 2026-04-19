"""
Simplified Chainlit application for RaithaMithra (for testing without API keys)
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
🌾 **ರೈತಮಿತ್ರ (RaithaMithra)** - Your Agricultural AI Assistant

ನಮಸ್ಕಾರ! ನಾನು ರೈತಮಿತ್ರ, ನಿಮ್ಮ ಕೃಷಿ ಸಹಾಯಕ.
Hello! I am RaithaMithra, your agricultural assistant.

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

**Note:** This is a demo version. For full functionality, please add your API keys to .env file.
        """
        
        await cl.Message(
            content=welcome_msg,
            author="RaithaMithra"
        ).send()
        
        logger.info(f"Chat session started for user: {user_id}")
        
    except Exception as e:
        logger.error(f"Error starting chat session: {e}")
        await cl.Message(
            content="ಕ್ಷಮಿಸಿ, ಚಾಟ್ ಪ್ರಾರಂಭಿಸಲು ದೋಷ ಸಂಭವಿಸಿದೆ. / Sorry, an error occurred starting the chat.",
            author="RaithaMithra"
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

                    # Simple transcription (demo mode)
                    transcribed_text = "[Voice input received - transcription would happen here with API keys]"
                    
                    # Show transcribed text
                    await cl.Message(
                        content=f"🎤 **Voice Input:** {transcribed_text}",
                        author="You"
                    ).send()
                    
                    # Generate response for voice input
                    response = await generate_simple_response(transcribed_text, language, None)
                    
                    # Send text response
                    assistant_response = response.get("assistant_response", "")
                    if assistant_response:
                        await cl.Message(
                            content=assistant_response,
                            author="RaithaMithra"
                        ).send()
                    
                    # Update session
                    user_sessions[user_id]["conversation_history"].append({
                        "user_input": transcribed_text,
                        "assistant_response": assistant_response,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    return  # Exit early since we handled the audio
        
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
                    
                    # Simple image analysis (demo)
                    image_description = "I can see an image has been uploaded. In the full version, I would analyze this image for agricultural purposes."
                    user_input += f"\n[Image Analysis: {image_description}]"
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
        
        # Generate simple response (demo mode)
        response = await generate_simple_response(user_input, language, image_url)
        
        # Send text response
        assistant_response = response.get("assistant_response", "")
        if assistant_response:
            await cl.Message(
                content=assistant_response,
                author="RaithaMithra"
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
                    author="RaithaMithra"
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
            author="RaithaMithra"
        ).send()

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

async def generate_simple_response(user_input: str, language: str, image_url: str = None) -> Dict[str, Any]:
    """Generate a simple response for demo mode"""
    
    try:
        # Simple response generation based on keywords
        input_lower = user_input.lower()
        
        if language == "kn":
            # Kannada responses
            if any(word in input_lower for word in ["ನಮಸ್ಕಾರ", "ಹಲೋ", "ಹೇ"]):
                response = "ನಮಸ್ಕಾರ! ನಾನು ರೈತಮಿತ್ರ. ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?"
            elif any(word in input_lower for word in ["ಹವಾಮಾನ", "ಮಳೆ", "ತಾಪಮಾನ"]):
                response = "ಹವಾಮಾನ ಮಾಹಿತಿಗಾಗಿ, ದಯವಿಟ್ಟು ನಿಮ್ಮ API ಕೀಗಳನ್ನು ಸೆಟಪ್ ಮಾಡಿ."
            elif any(word in input_lower for word in ["ಬೆಳೆ", "ಕೃಷಿ", "ಕೀಟ"]):
                response = "ಕೃಷಿ ಸಲಹೆಗಳಿಗಾಗಿ, ದಯವಿಟ್ಟು ನಿಮ್ಮ API ಕೀಗಳನ್ನು ಸೆಟಪ್ ಮಾಡಿ."
            elif image_url:
                response = "ಚಿತ್ರವನ್ನು ನೋಡಿದ್ದೇನೆ. ಚಿತ್ರ ವಿಶ್ಲೇಷಣೆಗಾಗಿ, ದಯವಿಟ್ಟು ನಿಮ್ಮ API ಕೀಗಳನ್ನು ಸೆಟಪ್ ಮಾಡಿ."
            else:
                response = "ನಿಮ್ಮ ಪ್ರಶ್ನೆಗೆ ಉತ್ತರಿಸಲು ನನಗೆ ಸಂತೋಷವಾಗುತ್ತದೆ. ಪೂರ್ಣ ಕಾರ್ಯಕ್ಷಮತೆಗಾಗಿ, ದಯವಿಟ್ಟು ನಿಮ್ಮ API ಕೀಗಳನ್ನು ಸೆಟಪ್ ಮಾಡಿ."
        else:
            # English responses
            if any(word in input_lower for word in ["hello", "hi", "hey"]):
                response = "Hello! I am RaithaMithra. How can I help you?"
            elif any(word in input_lower for word in ["weather", "rain", "temperature"]):
                response = "For weather information, please set up your API keys."
            elif any(word in input_lower for word in ["crop", "agriculture", "pest"]):
                response = "For agricultural advice, please set up your API keys."
            elif image_url:
                response = "I can see an image. For image analysis, please set up your API keys."
            else:
                response = "I'd be happy to answer your question. For full functionality, please set up your API keys."
        
        return {
            "assistant_response": response,
            "audio_path": None,  # No audio in demo mode
            "language": language
        }
        
    except Exception as e:
        logger.error(f"Error generating simple response: {e}")
        error_msg = "ಕ್ಷಮಿಸಿ, ಒಂದು ದೋಷ ಸಂಭವಿಸಿದೆ." if language == "kn" else "Sorry, an error occurred."
        return {
            "assistant_response": error_msg,
            "audio_path": None,
            "language": language
        }

if __name__ == "__main__":
    # This will be handled by Chainlit
    pass
