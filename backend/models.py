"""
Models re-exporter for backwards compatibility.
All domain models are modularly separated inside `core/models/`:
- core/models/base.py
- core/models/user.py
- core/models/session.py
- core/models/auth.py
- core/models/conversation.py
- core/models/message.py
- core/models/upload.py
- core/models/analytics.py
"""
from core.models import (
    Base,
    generate_uuid,
    User,
    Session,
    AuthAuditLog,
    PasswordResetToken,
    EmailVerificationToken,
    OTPVerification,
    Conversation,
    Message,
    Upload,
    AIUsage,
    ImageGenerationLog,
    ResearchLog,
)

__all__ = [
    "Base",
    "generate_uuid",
    "User",
    "Session",
    "AuthAuditLog",
    "PasswordResetToken",
    "EmailVerificationToken",
    "OTPVerification",
    "Conversation",
    "Message",
    "Upload",
    "AIUsage",
    "ImageGenerationLog",
    "ResearchLog",
]
