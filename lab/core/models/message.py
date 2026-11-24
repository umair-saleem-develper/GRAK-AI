from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, generate_uuid

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String, nullable=False) # 'user', 'assistant', 'system'
    content = Column(String, nullable=False)
    
    # Analytics & LLM tracking
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    
    image_base64 = Column(String, nullable=True) # Optional single image for backward compat
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    conversation = relationship("Conversation", back_populates="messages")
