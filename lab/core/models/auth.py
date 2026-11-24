from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, generate_uuid

class AuthAuditLog(Base):
    __tablename__ = "auth_audit_logs"
    
    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    ip = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    event_type = Column(String, nullable=False, index=True) # Login, Logout, Failed Login, etc.
    status = Column(String, nullable=False) # success, failure
    metadata_info = Column(String, nullable=True) # JSON string
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    
    user = relationship("User")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    
    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    user = relationship("User", back_populates="password_reset_tokens")

class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"
    
    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    user = relationship("User", back_populates="email_verification_tokens")

class OTPVerification(Base):
    __tablename__ = "otp_verifications"
    
    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    email = Column(String, index=True, nullable=False)
    otp_hash = Column(String, nullable=False)
    purpose = Column(String, default="login", nullable=False)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
