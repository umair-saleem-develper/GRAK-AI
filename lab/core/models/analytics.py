from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from .base import Base, generate_uuid

class AIUsage(Base):
    __tablename__ = "ai_usage"
    
    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    latency = Column(Float, nullable=True) # latency in seconds
    estimated_cost = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

class ImageGenerationLog(Base):
    __tablename__ = "image_generation_logs"
    
    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    prompt = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    latency = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

class ResearchLog(Base):
    __tablename__ = "research_logs"
    
    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    query = Column(String, nullable=False)
    latency = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
