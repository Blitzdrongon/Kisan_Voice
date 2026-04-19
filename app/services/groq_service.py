"""
Groq service for LLM and vision capabilities
"""

import os
import base64
import json
from typing import Optional, Dict, Any, List
from pathlib import Path

import httpx
from loguru import logger
#from services.rag_e5_groq import get_e5_rag_service
from core.config import get_settings


class GroqService:
    """Service for interacting with Groq API"""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.groq_api_key
        # Fix: Use correct base URL without duplication
        self.base_url = "https://api.groq.com/openai/v1"
        #self.rag_service = get_e5_rag_service()
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
    
    async def generate_text(
        self, 
        prompt: str, 
        model: str = "llama-3.3-70b-versatile",
        max_tokens: int = 500,
        temperature: float = 0.7,
        language: str = "kn",
        context: str = ""
    ) -> str:
        """Generate text using Groq API"""
        
        try:
            import httpx
            
            #context = self.rag_service.retrieve(query=prompt, top_k=5)
            #context = "\n\n".join(context["documents"])
            logger.info(f"Retrieved context: {context}")
            
            # Prepare the prompt
            # system_prompt = (
            #         "You are KisanVoice, a friendly and helpful AI assistant. Respond in {language} language. "
            #         "Rules:\n"
            # "1. Answer ONLY using the provided CONTEXT if ONLY any agriculture question is asked .\n"
            # "2. Use outside knowledge just to frame the answer.\n"
            # "3. If the answer is not explicitly present, reply exactly:\n"
            # "   'Information not available in the document.'\n"
            # "4. Be concise."
            #     )

            system_prompt = f"""
You are KISAN VOICE, an AI agriculture assistant helping farmers mainly in North Karnataka and nearby regions of India.
Your goal is to provide practical, safe, and easy farming guidance that improves crop yield, reduces risk, and supports sustainable farming.
Your responses must be simple, actionable, and farmer-friendly.
LANGUAGE RULE
• Always reply in the {language} language only.
• If the farmer mixes languages, prefer {language} language.
• If language is unclear, respond in simple {language} language.
• Use short, voice-friendly sentences.
---------------------
REGIONAL FOCUS
Prioritize crops commonly grown in Karnataka:
• Jowar
• Bajra
• Cotton
• Tur (Pigeon pea)
• Groundnut
• Maize
• Paddy
• Onion
• Sugarcane
Adjust advice according to common farming practices in Karnataka.
---------------------------------
Use the provided context is the chat history use it when relevant.
If context is missing, ask for the context.
-------------------------
INTENT UNDERSTANDING
First identify the farmer’s intent.
Possible intents include:
• crop_advice
• pest_disease
• fertilizer_advice
• irrigation
• weather_based_advice
• market_price
• government_scheme
• livestock_care
• general_question
If the farmer's question contains symptoms, treat it as pest_disease.
-----------------------
IMPORTANT INFORMATION EXTRACTION
Try to identify:
• Crop name
• Crop stage (seedling / vegetative / flowering / harvest)
• Symptoms
• Location
• Weather conditions
If critical information is missing, ask ONE simple follow-up question.
Example:
"What crop are you growing?"
-----------------------
WHAT YOU HELP WITH
Provide practical guidance on:
• Crop cultivation
• Fertilizer usage
• Irrigation methods
• Pest and disease control
• Weather-based farming advice
• Market selling tips (if location known)
• Government agriculture schemes
• Livestock care (cattle, goats, poultry)
• Sustainable farming practices
• Soil health improvement
-----------------------
RESPONSE FORMAT (FARMER FRIENDLY)
⭐ Key Points
Explain the issue in simple terms.
➤ What To Do
Provide step-by-step actions.
Always include:
• Dosage
• Units (ml per litre / kg per acre)
• Timing
• Method of application
⚠ Important Warning
Mention safety precautions, especially for pesticides.
❌ Avoid
Mention harmful or incorrect farming practices.
🌱 Extra Tip
Provide one useful farming suggestion.
-----------------------
PESTICIDE SAFETY RULES
• Follow ICAR / KVK recommended practices.
• Avoid banned or unsafe chemicals.
• Prefer Integrated Pest Management (IPM).
Always combine:
• Cultural methods
• Biological control
• Chemical control only if necessary.
Never give pesticide dosage without units.
Example:
"Imidacloprid 0.3 ml per litre water."
-----------------------
WEATHER AWARENESS
If rain or extreme weather is mentioned:
• Avoid recommending spraying before rain.
• Suggest weather-safe practices.
Example:
Do not spray pesticides before rainfall.
-----------------------
MARKET ADVIC
If the farmer asks about selling crops:
Ask for location or nearest mandi.
Example:
"Which district or mandi do you want the price for?"
-----------------------
EMERGENCY RULE
If severe crop damage, pesticide poisoning, or livestock emergency is suspected:
Advise contacting:
• nearest KVK (Krishi Vigyan Kendra)
• agriculture officer
• veterinary doctor
-----------------------
RESPONSE STYLE
• Keep answers short and clear.
• Avoid technical jargon.
• Use bullet points.
• Limit responses to about 120 words if possible.
------------------
GOAL
Provide clear, safe, and practical farming advice that helps farmers make better decisions and increase farm productivity.
"""
            user_prompt = f"""
                        CONTEXT:
                        {context}

                        QUESTION:
                        {prompt}

                        ANSWER:
                        """
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Create a new client for each request to avoid closure issues
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.debug(f"Groq API response: {result}")

                # Robust extraction of assistant text across possible schemas
                generated_text = None
                try:
                    if result.get("choices"):
                        choice0 = result["choices"][0]
                        # Primary: chat completion format
                        generated_text = (
                            choice0.get("message", {}).get("content")
                            or choice0.get("text")
                        )
                        logger.debug(f"Extracted text: '{generated_text}'")
                except Exception as extract_err:
                    logger.warning(f"Groq response parse warning: {extract_err}")

                generated_text = (generated_text or "").strip()

                if not generated_text:
                    logger.warning(f"Groq returned empty content. Raw response: {result}")
                    return (
                        "ಕ್ಷಮಿಸಿ, ಒಂದು ದೋಷ ಸಂಭವಿಸಿದೆ." if language == "kn" else "Sorry, I couldn't generate a response."
                    )

                logger.info(f"Text generated successfully using {model}")
                return generated_text
            else:
                logger.error(f"Groq API error: {response.status_code} - {response.text}")
                return f"ಕ್ಷಮಿಸಿ, ಒಂದು ದೋಷ ಸಂಭವಿಸಿದೆ." if language == "kn" else "Sorry, an error occurred."
                
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return f"ಕ್ಷಮಿಸಿ, ಒಂದು ದೋಷ ಸಂಭವಿಸಿದೆ." if language == "kn" else "Sorry, an error occurred."
    
    async def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe audio using Groq's Whisper model"""
        
        try:
            import httpx
            
            # Check if file exists
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            # Prepare the request
            with open(audio_file_path, "rb") as audio_file:
                files = {"file": audio_file}
                data = {"model": "whisper-1"}
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                # Create a new client for each request
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/audio/transcriptions",
                        files=files,
                        data=data,
                        headers=headers,
                        timeout=30.0
                    )
            
            if response.status_code == 200:
                result = response.json()
                transcribed_text = result["text"]
                logger.info("Audio transcribed successfully")
                return transcribed_text
            else:
                logger.error(f"Transcription error: {response.status_code} - {response.text}")
                return ""
                
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return ""
    
    async def analyze_image(
        self, 
        image_path: str, 
        prompt: str = "Describe this image in detail",
        model: str = "llama-3.2-90b-vision-preview",
        language: str = "kn"
    ) -> str:
        """Analyze image using Groq's vision model"""
        
        try:
            import httpx
            
            # Check if file exists
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Read and encode image
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Determine MIME type based on file extension
            file_ext = Path(image_path).suffix.lower()
            if file_ext in ['.jpg', '.jpeg']:
                mime_type = "image/jpeg"
            elif file_ext == '.png':
                mime_type = "image/png"
            elif file_ext == '.gif':
                mime_type = "image/gif"
            elif file_ext == '.webp':
                mime_type = "image/webp"
            else:
                mime_type = "image/jpeg"  # Default
            
            # Prepare the prompt based on language
            if language == "kn":
                system_prompt = "ಈ ಚಿತ್ರವನ್ನು ವಿವರವಾಗಿ ವಿವರಿಸಿ. ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸಿ."
            else:
                system_prompt = "Describe this image in detail. Respond in English."
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Create a new client for each request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result["choices"][0]["message"]["content"]
                logger.info("Image analyzed successfully")
                return analysis
            else:
                logger.error(f"Image analysis error: {response.status_code} - {response.text}")
                return f"ಕ್ಷಮಿಸಿ, ಚಿತ್ರ ವಿಶ್ಲೇಷಣೆಯಲ್ಲಿ ದೋಷ ಸಂಭವಿಸಿದೆ." if language == "kn" else "Sorry, an error occurred in image analysis."
                
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return f"ಕ್ಷಮಿಸಿ, ಚಿತ್ರ ವಿಶ್ಲೇಷಣೆಯಲ್ಲಿ ದೋಷ ಸಂಭವಿಸಿದೆ." if language == "kn" else "Sorry, an error occurred in image analysis."
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return [
            "llama-3.3-70b-versatile",
            "llama-3.2-90b-vision-preview",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
    
    def is_healthy(self) -> bool:
        """Check if the service is healthy"""
        try:
            import httpx
            # Create a new client for health check
            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/models", 
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
            return response.status_code == 200
        except:
            return False


# Global service instance
groq_service = GroqService()


def get_groq_service() -> GroqService:
    """Get Groq service instance"""
    return groq_service

