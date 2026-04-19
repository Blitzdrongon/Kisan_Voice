"""
Memory management for RaithaMithra
"""

import os
import uuid
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass

from loguru import logger
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from core.config import get_settings


@dataclass
class MemoryItem:
    """Individual memory item"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    timestamp: datetime = None
    memory_type: str = "conversation"  # conversation, knowledge, experience
    language: str = "kn"
    tags: List[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.tags is None:
            self.tags = []
        if self.embedding is None:
            self.embedding = []


class ShortTermMemory:
    """SQLite-based short-term memory for conversation history"""
    
    def __init__(self, db_path: str = "data/raithamithra.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    assistant_response TEXT NOT NULL,
                    language TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    language TEXT NOT NULL,
                    created_at DATETIME NOT NULL,
                    last_active DATETIME NOT NULL,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    language TEXT NOT NULL,
                    voice_enabled BOOLEAN DEFAULT 1,
                    preferred_voice TEXT,
                    location TEXT,
                    timezone TEXT,
                    updated_at DATETIME NOT NULL
                )
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def add_conversation(self, session_id: str, user_id: str, user_message: str, 
                        assistant_response: str, language: str = "kn", 
                        metadata: Dict[str, Any] = None) -> str:
        """Add a conversation to memory"""
        conversation_id = str(uuid.uuid4())
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO conversations 
                (id, session_id, user_id, user_message, assistant_response, language, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conversation_id, session_id, user_id, user_message, 
                assistant_response, language, datetime.utcnow().isoformat(),
                json.dumps(metadata or {})
            ))
            conn.commit()
        
        return conversation_id
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM conversations 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (session_id, limit))
            
            conversations = []
            for row in cursor.fetchall():
                conversations.append({
                    'id': row['id'],
                    'session_id': row['session_id'],
                    'user_id': row['user_id'],
                    'user_message': row['user_message'],
                    'assistant_response': row['assistant_response'],
                    'language': row['language'],
                    'timestamp': row['timestamp'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                })
            
            return conversations[::-1]  # Reverse to get chronological order
    
    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM user_preferences WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'user_id': row['user_id'],
                    'language': row['language'],
                    'voice_enabled': bool(row['voice_enabled']),
                    'preferred_voice': row['preferred_voice'],
                    'location': row['location'],
                    'timezone': row['timezone'],
                    'updated_at': row['updated_at']
                }
            return None
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO user_preferences 
                    (user_id, language, voice_enabled, preferred_voice, location, timezone, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    preferences.get('language', 'kn'),
                    preferences.get('voice_enabled', True),
                    preferences.get('preferred_voice'),
                    preferences.get('location'),
                    preferences.get('timezone'),
                    datetime.utcnow().isoformat()
                ))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False


class LongTermMemory:
    """Qdrant-based long-term memory for semantic search"""
    
    def __init__(self, qdrant_url: str, collection_name: str = "raithamithra_memory"):
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.client = None
        self._init_client()
        self._init_collection()
    
    def _init_client(self):
        """Initialize Qdrant client"""
        try:
            self.client = QdrantClient(url=self.qdrant_url)
            logger.info(f"Connected to Qdrant at {self.qdrant_url}")
        except Exception as e:
            logger.warning(f"Qdrant not available at {self.qdrant_url}: {e}")
            logger.info("Continuing without Qdrant - using SQLite only")
            self.client = None
    
    def _init_collection(self):
        """Initialize Qdrant collection"""
        if not self.client:
            return
        
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Using existing Qdrant collection: {self.collection_name}")
                
        except Exception as e:
            logger.warning(f"Error initializing Qdrant collection: {e}")
            logger.info("Continuing without Qdrant - using SQLite only")
    
    def add_memory(self, content: str, metadata: Dict[str, Any], 
                   embedding: List[float] = None) -> Optional[str]:
        """Add a memory item to long-term storage"""
        if not self.client:
            return None
        
        try:
            memory_id = str(uuid.uuid4())
            
            # For now, use a simple embedding (you can integrate with an embedding service)
            if embedding is None:
                embedding = [0.0] * 1536  # Placeholder embedding
            
            point = PointStruct(
                id=memory_id,
                vector=embedding,
                payload={
                    "content": content,
                    "metadata": metadata,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"Added memory to Qdrant: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Error adding memory to Qdrant: {e}")
            return None
    
    def search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search memories by content"""
        if not self.client:
            return []
        
        try:
            # For now, return empty results (you can implement semantic search)
            # This would typically involve embedding the query and searching similar vectors
            return []
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []


class MemoryManager:
    """Main memory manager combining short-term and long-term memory"""
    
    def __init__(self):
        settings = get_settings()
        
        # Initialize short-term memory
        self.short_term = ShortTermMemory()
        
        # Initialize long-term memory
        self.long_term = LongTermMemory(
            qdrant_url=settings.qdrant_url
        )
        
        logger.info("Memory manager initialized successfully")
    
    def add_conversation(self, session_id: str, user_id: str, user_message: str, 
                        assistant_response: str, language: str = "kn", 
                        metadata: Dict[str, Any] = None) -> str:
        """Add a conversation to memory"""
        # Add to short-term memory
        conversation_id = self.short_term.add_conversation(
            session_id, user_id, user_message, assistant_response, language, metadata
        )
        
        # Add to long-term memory for semantic search
        content = f"User: {user_message}\nAssistant: {assistant_response}"
        self.long_term.add_memory(content, metadata or {})
        
        return conversation_id
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.short_term.get_conversation_history(session_id, limit)
    
    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences"""
        return self.short_term.get_user_preferences(user_id)
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        return self.short_term.update_user_preferences(user_id, preferences)
    
    def search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search long-term memories"""
        return self.long_term.search_memories(query, limit)


# Global memory manager instance
memory_manager = MemoryManager()


def get_memory_manager() -> MemoryManager:
    """Get memory manager instance"""
    return memory_manager

