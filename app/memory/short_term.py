"""Short-term conversational memory"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Short-term conversation memory"""
    
    def __init__(self, 
                 session_id: str,
                 max_messages: int = 50,
                 ttl_minutes: int = 60):
        self.session_id = session_id
        self.max_messages = max_messages
        self.ttl_minutes = ttl_minutes
        self.messages: deque = deque(maxlen=max_messages)
        self.created_at = datetime.utcnow()
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a message to the conversation"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        }
        self.messages.append(message)
        logger.debug(f"Added {role} message to session {self.session_id}")
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages in the conversation"""
        return list(self.messages)
    
    def get_recent_messages(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages"""
        return list(self.messages)[-count:]
    
    def is_expired(self) -> bool:
        """Check if session has expired"""
        expiry_time = self.created_at + timedelta(minutes=self.ttl_minutes)
        is_expired = datetime.utcnow() > expiry_time
        
        if is_expired:
            logger.info(f"Session {self.session_id} has expired")
        
        return is_expired
    
    def clear(self) -> None:
        """Clear all messages"""
        self.messages.clear()
        logger.info(f"Cleared session {self.session_id}")


class ConversationMemoryManager:
    """Manager for multiple conversation sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, ConversationMemory] = {}
    
    def create_session(self, session_id: str, max_messages: int = 50) -> ConversationMemory:
        """Create a new conversation session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationMemory(
                session_id=session_id,
                max_messages=max_messages
            )
            logger.info(f"Created conversation session: {session_id}")
        
        return self.sessions[session_id]
    
    def get_session(self, session_id: str) -> Optional[ConversationMemory]:
        """Get a conversation session"""
        session = self.sessions.get(session_id)
        
        if session and session.is_expired():
            del self.sessions[session_id]
            return None
        
        return session
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add message to session"""
        session = self.create_session(session_id)
        session.add_message(role, content)
    
    def close_session(self, session_id: str) -> None:
        """Close a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Closed session: {session_id}")
