"""
Conversation nodes for KisanVoice LangGraph
"""

import uuid
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger
import time
from pathlib import Path
from core.state import Message, MessageType, Language, ConversationState
from core.memory import get_memory_manager
from services.groq_service import get_groq_service
from services.whisper_services import get_whisper_service
from services.weather_service import get_weather_service
from services.elevenlabs_service import get_elevenlabs_service
from services.image_anylsis import get_image_analysis
from services.gemini_tts_service import get_gemini_tts_service
from services.gemini_stt_service import get_gemini_stt_service
#from services.gemma_with_RAG_services import get_gemma_with_RAG_service

class ConversationNodes:
    """Nodes for conversation flow"""
    
    def __init__(self):
        self.groq_service = get_groq_service()
        self.weather_service = get_weather_service()
        self.elevenlabs_service = get_elevenlabs_service()
        self.memory_manager = get_memory_manager()
        self.image_analysis = get_image_analysis()
        self.whisper_service = get_whisper_service()
        self.gemini_tts_service = get_gemini_tts_service()
        self.gemini_stt_service = get_gemini_stt_service()
        #self.gemma_with_rag_service = get_gemma_with_RAG_service()
    
    async def process_user_input(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process user input and determine intent"""
        
        try:
            # Normalize state to mutable dict
            if not isinstance(state, dict):
                if hasattr(state, "model_dump"):
                    state = state.model_dump()
                else:
                    state = dict(state)
            user_input = state.get("user_input", "")
            session_id = state.get("session_id", "")
            user_id = state.get("user_id", "anonymous")
            language = state.get("language", "kn")
            
            # Create message
            message = Message(
                id=str(uuid.uuid4()),
                type=MessageType.TEXT,
                content=user_input,
                sender="user",
                language=Language(language)
            )
            
            # Add to state
            if "messages" not in state:
                state["messages"] = []
            state["messages"].append(message.dict())
            
            # Get conversation history for context
            conversation_history = self.memory_manager.get_conversation_history(session_id, limit=5)
            state["conversation_history"] = conversation_history
            
            # Get user preferences
            user_preferences = self.memory_manager.get_user_preferences(user_id)
            if user_preferences:
                state["user_preferences"] = user_preferences
                # Update language if user has preference
                if user_preferences.get("language") and language != user_preferences["language"]:
                    language = user_preferences["language"]
                    state["language"] = language
            
            # Determine intent
            intent = await self._classify_intent(user_input, language, state.get("image_url"), state.get("audio_url"))
            state["current_intent"] = intent
            
            logger.info(f"Processed user input: {intent}")
            return state
            
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            state["error"] = str(e)
            return state
    
    async def generate_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI response based on intent and memory context"""
        
        try:
            # Normalize state to mutable dict
            if not isinstance(state, dict):
                if hasattr(state, "model_dump"):
                    state = state.model_dump()
                else:
                    state = dict(state)
            intent = state.get("current_intent", "general")
            user_input = state.get("user_input", "")
            language = state.get("language", "kn")
            conversation_history = state.get("conversation_history", [])
            user_preferences = state.get("user_preferences", {})
            
            # Build context from memory
            context = self._build_context(user_input, conversation_history, user_preferences, language)
            
            if intent == "weather":
                response = await self._handle_weather_query(user_input, language, context)
            elif intent == "image_analysis":
                # Pass state to access image path inside handler
                response = await self._handle_image_analysis(state, language, context)
            elif intent == "voice_request":
                # Pass audio_url for STT handling
                response = await self._handle_voice_request(user_input, language, context, state.get("audio_url"))
            elif intent == "memory_query":
                response = await self._handle_memory_query(user_input, language, context)
            else:
                response = await self._handle_general_conversation(user_input, language, context)
            
            # Normalize empty/whitespace responses
            response = (response or "").strip()
            if not response:
                response = "ಕ್ಷಮಿಸಿ, ಒಂದು ದೋಷ ಸಂಭವಿಸಿದೆ." if language == "kn" else "Sorry, I couldn't generate a response."

            # Create assistant message
            assistant_message = Message(
                id=str(uuid.uuid4()),
                type=MessageType.TEXT,
                content=response,
                sender="assistant",
                language=Language(language)
            )
            
            # Add to state
            state["assistant_response"] = response
            state["messages"].append(assistant_message.dict())
            
            return state
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            error_response = "ಕ್ಷಮಿಸಿ, ಒಂದು ದೋಷ ಸಂಭವಿಸಿದೆ." if language == "kn" else "Sorry, an error occurred."
            state["assistant_response"] = error_response
            return state
    
    async def save_to_memory(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Save conversation to memory systems"""
        
        try:
            # Normalize state to mutable dict
            if not isinstance(state, dict):
                if hasattr(state, "model_dump"):
                    state = state.model_dump()
                else:
                    state = dict(state)
            user_input = state.get("user_input", "")
            assistant_response = state.get("assistant_response", "")
            session_id = state.get("session_id", "")
            user_id = state.get("user_id", "anonymous")
            language = state.get("language", "kn")
            
            if user_input and assistant_response:
                # Save to memory
                memory_id = self.memory_manager.add_conversation(
                    session_id=session_id,
                    user_id=user_id,
                    user_message=user_input,
                    assistant_response=assistant_response,
                    language=language,
                    metadata={
                        "intent": state.get("current_intent", "general"),
                        "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                if memory_id:
                    state["memory_saved"] = True
                    state["memory_id"] = memory_id
                    logger.info(f"Conversation saved to memory: {memory_id}")
                else:
                    state["memory_saved"] = False
                    logger.warning("Failed to save conversation to memory")
            
            return state
            
        except Exception as e:
            logger.error(f"Error saving to memory: {e}")
            state["memory_saved"] = False
            return state
    
    async def generate_audio_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate audio response using TTS"""
        time.sleep(2)
        try:
            # Normalize state to mutable dict
            if not isinstance(state, dict):
                if hasattr(state, "model_dump"):
                    state = state.model_dump()
                else:
                    state = dict(state)
            response_text = state.get("assistant_response", "")
            language = state.get("language", "kn")
            
            if not response_text:
                return state
            
            # Generate audio
            audio_data = await self.elevenlabs_service.text_to_speech(
                text=response_text,
                language=language
            )

            
            if audio_data:
                # Save audio to file (Gemini TTS returns WAV bytes). Use .wav extension.
                audio_filename = f"response_{uuid.uuid4()}.mp3"
                # Robust path construction: app/nodes/conversation_nodes.py -> app/uploads
                upload_dir = Path(__file__).parent.parent / "uploads"
                upload_dir.mkdir(parents=True, exist_ok=True)
                audio_path = str(upload_dir / audio_filename)

                if self.elevenlabs_service.save_audio_to_file(audio_data, audio_path):
                    state["audio_response_path"] = audio_path
                    state["audio_generated"] = True
                else:
                    state["audio_generated"] = False
            
            return state
            
        except Exception as e:
            logger.error(f"Error generating audio response: {e}")
            state["audio_generated"] = False
            return state
    
    def _build_context(self, user_input: str, conversation_history: List[Dict], 
                      user_preferences: Dict, language: str) -> str:
        """Build context from memory and preferences"""
        
        context_parts = []
        
        # Add user preferences context
        if user_preferences:
            if user_preferences.get("location"):
                context_parts.append(f"User location: {user_preferences['location']}")
            if user_preferences.get("language"):
                context_parts.append(f"Preferred language: {user_preferences['language']}")
        
        # Add recent conversation context
        if conversation_history:
            recent_context = []
            for conv in conversation_history[:3]:  # Last 3 conversations
                recent_context.append(f"Previous: {conv['user_message']} -> {conv['assistant_response']}")
            
            if recent_context:
                context_parts.append("Recent conversation context:\n" + "\n".join(recent_context))
        
        # Add current query context
        context_parts.append(f"Current query: {user_input}")
        
        return "\n\n".join(context_parts)
    
    async def _classify_intent(self, text: str, language: str, image_url: str, audio_url: str) -> str:
        """Classify user intent"""
        
        try:
            # Simple keyword-based intent classification
            text_lower = text.lower()
            
            # Weather-related keywords
            weather_keywords = ["ಮಳೆ", "ಹವಾಮಾನ", "ತಾಪಮಾನ", "ಉಷ್ಣತೆ", "rain", "weather", "temperature", "hot", "cold"]
            if any(keyword in text_lower for keyword in weather_keywords):
                return "weather"
            
            # Image analysis keywords
            image_keywords = ["ಚಿತ್ರ", "ಫೋಟೋ", "image", "photo", "picture", "analyze", "describe"]
            if image_url or any(keyword in text_lower for keyword in image_keywords):
                return "image_analysis"
            
            # Voice request keywords
            voice_keywords = ["ಧ್ವನಿ", "ಮಾತು", "voice", "speak", "audio", "sound"]
            if audio_url or any(keyword in text_lower for keyword in voice_keywords):
                return "voice_request"
            
            # Memory query keywords
            memory_keywords = ["ನೆನಪು", "ಮೊದಲು", "ಹಿಂದೆ", "memory", "remember", "before", "previous"]
            if any(keyword in text_lower for keyword in memory_keywords):
                return "memory_query"
            
            return "general"
            
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return "general"
    
    async def _handle_weather_query(self, query: str, language: str, context: str) -> str:
        """Handle weather-related queries"""
        
        try:
            # Extract city from query (simple approach)
            # In production, use NER or more sophisticated parsing
            
            # Default to Bangalore for now
            city = "hubli"
            country_code = "IN"
            
            weather_data = await self.weather_service.get_current_weather(
                city=city,
                country_code=country_code,
                language=language
            )
            
            if weather_data:
                if language == "kn":
                    response = f"{city} ನಲ್ಲಿ ಇಂದಿನ ಹವಾಮಾನ: {weather_data['description']}, ತಾಪಮಾನ: {weather_data['temperature']['current']}°C"
                else:
                    response = f"Current weather in {city}: {weather_data['description']}, Temperature: {weather_data['temperature']['current']}°C"
            else:
                response = "ಹವಾಮಾನ ಮಾಹಿತಿಯನ್ನು ಪಡೆಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ" if language == "kn" else "Could not fetch weather information"
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling weather query: {e}")
            return "ಹವಾಮಾನ ಮಾಹಿತಿಯನ್ನು ಪಡೆಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ" if language == "kn" else "Could not fetch weather information"
    
    async def _handle_image_analysis(self, state: Dict[str, Any], language: str, context: str) -> str:
        """Handle image analysis requests"""
        
        try:
            # Normalize state to mutable dict
            if not isinstance(state, dict):
                if hasattr(state, "model_dump"):
                    state = state.model_dump()
                else:
                    state = dict(state)
            # Check if image is available in state
            image_path = state.get("image_url")  # This is actually the file path
            if not image_path:
                return "ಚಿತ್ರವನ್ನು ಕಾಣಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ" if language == "kn" else "No image found for analysis"
            
            # Analyze image
            analysis = await self.image_analysis.analyze_image(
                image_path=image_path,
                language=language
            )
            
            if analysis:
                return analysis
            else:
                return "ಚಿತ್ರವನ್ನು ವಿಶ್ಲೇಷಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ" if language == "kn" else "Could not analyze the image"
                
        except Exception as e:
            logger.error(f"Error handling image analysis: {e}")
            return "ಚಿತ್ರ ವಿಶ್ಲೇಷಣೆಯಲ್ಲಿ ದೋಷ ಸಂಭವಿಸಿದೆ" if language == "kn" else "Error occurred during image analysis"
    
    async def _handle_voice_request(self, query: str, language: str, context: str, audio_url: str) -> str:
        """Handle voice-related requests with STT transcription if audio is provided"""
        
        try:
            # If audio is present, transcribe it using Groq Whisper
            if audio_url:
                try:
                    transcription = await self.gemini_stt_service.transcribe(audio_url, language=language)
                    logger.info(f"STT transcription: {transcription}")
                except Exception as stt_err:
                    logger.warning(f"STT failed: {stt_err}")
                    transcription = ""

                if transcription:
                    #language = await self.detect_language(transcription)

                    # Return transcription routed through general conversation
                    return await self._handle_general_conversation(transcription, language, context)

            # Fallback info message when no audio provided or STT failed
            if language == "kn":
                return "ಧ್ವನಿ ಸೇವೆಯು ಲಭ್ಯವಿದೆ. ದಯವಿಟ್ಟು ಆಡಿಯೋ ಕಳುಹಿಸಿ ಅಥವಾ ಪಠ್ಯವನ್ನು ನಮೂದಿಸಿ."
            return "Voice service is unavailable. Please try later."
            
        except Exception as e:
            logger.error(f"Error handling voice request: {e}")
            return "ಧ್ವನಿ ಸೇವೆಯಲ್ಲಿ ದೋಷ ಸಂಭವಿಸಿದೆ" if language == "kn" else "Error in voice service"
    
    async def _handle_memory_query(self, query: str, language: str, context: str) -> str:
        """Handle memory-related queries"""
        
        try:
            if language == "kn":
                response = "ನಿಮ್ಮ ಹಿಂದಿನ ಸಂವಾದಗಳನ್ನು ನೆನಪಿಸಿಕೊಳ್ಳಲು ನಾನು ಇಲ್ಲಿ ಇದ್ದೇನೆ. ಯಾವುದೇ ನಿರ್ದಿಷ್ಟ ವಿಷಯದ ಬಗ್ಗೆ ಕೇಳಲು ಬಯಸುವಿರಾ?"
            else:
                response = "I'm here to help you remember our previous conversations. Is there something specific you'd like to know about?"
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling memory query: {e}")
            return "ನೆನಪು ಸೇವೆಯಲ್ಲಿ ದೋಷ ಸಂಭವಿಸಿದೆ" if language == "kn" else "Error in memory service"
    
    async def _handle_general_conversation(self, query: str, language: str, context: str) -> str:
        """Handle general conversation with memory context"""
        
        try:
            # json_path = Path(
            #     "/home/rospc/tanishq/KisanVoice_v2/KisanVoice/rag/final_clean_merged_dataset.json"
            # )

            #self.gemma_with_rag_service.add_json(str(json_path))

            #language = await self.detect_language(query)
            logger.info(f"Language detected: {language}")
            # Enhance prompt with context
            
            
            response = await self.groq_service.generate_text(
                prompt=query,
                language=language,
                context=context
            )
            
            if response:
                return response
            else:
                return "ಕ್ಷಮಿಸಿ, ನಾನು ನಿಮ್ಮ ಪ್ರಶ್ನೆಗೆ ಉತ್ತರಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ" if language == "kn" else "Sorry, I couldn't respond to your question"
                
        except Exception as e:
            logger.error(f"Error in general conversation: {e}")
            return "ಸಂವಾದದಲ್ಲಿ ದೋಷ ಸಂಭವಿಸಿದೆ" if language == "kn" else "Error occurred during conversation"

    async def detect_language(text: str) -> str:
    # Full Kannada characters
        kannada = set(
            'ಀಁಂಃ಄ಅಆಇಈಉಊಋೠಌೡಎಏಐಒಓಔ'
            'ಕಖಗಘಙಚಛಜಝಞಟಠಡಢಣತಥದಧನ'
            'ಪಫಬಭಮಯರಱಲಳವಶಷಸಹ'
            '಼ಽಾಿೀುೂೃೄೆೇೈೊೋೌ್'
            'ೕೖೞ೟ೠೡ'
            '೦೧೨೩೪೫೬೭೮೯'
            '।॥'
        )

        # Full Hindi / Devanagari characters
        hindi = set(
            'ऀँंःऄअआइईउऊऋॠऌॡएऐओऔ'
            'कखगघङचछजझञटठडढणतथदधन'
            'पफबभमयरऱलळऴवशषसह'
            '़ऽािीुूृॄॅॆेैॉॊोौ्॒॑ॕॖॗ'
            '०१२३४५६७८९'
            '।॥'
        )

        # 1️⃣ Kannada detection
        if any(c in kannada for c in text):
            return "kn"

        # 2️⃣ Hindi detection
        if any(c in hindi for c in text):
            return "hi"

        # 3️⃣ English is the fallback
        return "en"

# Global instance
conversation_nodes = ConversationNodes()


def get_conversation_nodes() -> ConversationNodes:
    """Get conversation nodes instance"""
    return conversation_nodes
