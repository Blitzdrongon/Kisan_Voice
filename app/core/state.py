"""
State management for RaithaMithra conversations
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class MessageType(str, Enum):
    """Types of messages"""
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    WEATHER = "weather"
    SYSTEM = "system"


class Language(str, Enum):
    """Supported languages"""
    KANNADA = "kn"
    ENGLISH = "en"
    HINDI = "hi"


class Message(BaseModel):
    """Individual message in conversation"""
    id: str
    type: MessageType
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sender: str  # "user" or "assistant"
    metadata: Optional[Dict[str, Any]] = None
    language: Language = Language.KANNADA


class ConversationState(BaseModel):
    """State of a conversation"""
    session_id: str
    user_id: str
    messages: List[Message] = Field(default_factory=list)
    current_language: Language = Language.KANNADA
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Weather context
    last_weather_query: Optional[str] = None
    weather_location: Optional[str] = None
    
    # Voice context
    voice_enabled: bool = True
    preferred_voice: Optional[str] = None
    
    # WhatsApp context
    whatsapp_number: Optional[str] = None
    whatsapp_session_active: bool = False


class UserProfile(BaseModel):
    """User profile information"""
    user_id: str
    name: str
    preferred_language: Language = Language.KANNADA
    location: Optional[str] = None
    timezone: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    preferences: Dict[str, Any] = Field(default_factory=dict)


class GlobalState:
    """Global application state"""
    
    def __init__(self):
        self.conversations: Dict[str, ConversationState] = {}
        self.user_profiles: Dict[str, UserProfile] = {}
        self.active_sessions: Dict[str, str] = {}  # session_id -> user_id
    
    def get_conversation(self, session_id: str) -> Optional[ConversationState]:
        """Get conversation by session ID"""
        return self.conversations.get(session_id)
    
    def create_conversation(self, session_id: str, user_id: str) -> ConversationState:
        """Create a new conversation"""
        conversation = ConversationState(session_id=session_id, user_id=user_id)
        self.conversations[session_id] = conversation
        self.active_sessions[session_id] = user_id
        return conversation
    
    def add_message(self, session_id: str, message: Message) -> bool:
        """Add message to conversation"""
        conversation = self.get_conversation(session_id)
        if conversation:
            conversation.messages.append(message)
            conversation.updated_at = datetime.utcnow()
            return True
        return False
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by user ID"""
        return self.user_profiles.get(user_id)
    
    def update_user_profile(self, user_id: str, **kwargs) -> bool:
        """Update user profile"""
        profile = self.get_user_profile(user_id)
        if profile:
            for key, value in kwargs.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            profile.last_active = datetime.utcnow()
            return True
        return False


# Global state instance
global_state = GlobalState()


def get_global_state() -> GlobalState:
    """Get global state instance"""
    return global_state

