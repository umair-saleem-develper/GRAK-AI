from sqlalchemy.orm import Session
from models import AuthAuditLog
from fastapi import Request
import json

def log_auth_event(
    db: Session,
    event_type: str,
    status: str,
    user_id: str = None,
    ip: str = None,
    user_agent: str = None,
    metadata: dict = None
):
    """
    Logs an authentication event to the audit table.
    """
    try:
        log_entry = AuthAuditLog(
            user_id=user_id,
            ip=ip,
            user_agent=user_agent,
            event_type=event_type,
            status=status,
            metadata_info=json.dumps(metadata) if metadata else None
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"Failed to write audit log: {e}")
        db.rollback()

def get_client_ip(request: Request) -> str:
    # Handle proxies if necessary, otherwise use client.host
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0]
    return request.client.host if request.client else "unknown"

def get_user_agent(request: Request) -> str:
    return request.headers.get("User-Agent", "unknown")
