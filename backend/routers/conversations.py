from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from pydantic import BaseModel
from database import get_db
from models import User, Conversation, Message
from services.auth import get_current_user
from datetime import datetime, timezone

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None

@router.get("")
def list_conversations(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Conversation).filter(
        Conversation.user_id == current_user.id,
        Conversation.deleted_at == None
    )
    
    if search:
        query = query.filter(Conversation.title.ilike(f"%{search}%"))
        
    total = query.count()
    
    # Order by pinned first, then updated_at descending
    conversations = query.order_by(
        desc(Conversation.is_pinned),
        desc(Conversation.updated_at)
    ).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "items": [
            {
                "id": c.id,
                "title": c.title,
                "is_pinned": c.is_pinned,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None
            } for c in conversations
        ],
        "total": total,
        "page": page,
        "limit": limit
    }

@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
        Conversation.deleted_at == None
    ).first()
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    messages = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at).all()
    
    return {
        "id": conv.id,
        "title": conv.title,
        "is_pinned": conv.is_pinned,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "provider": m.provider,
                "model": m.model,
                "created_at": m.created_at.isoformat() if m.created_at else None
            } for m in messages
        ]
    }

@router.patch("/{conversation_id}")
def update_conversation(
    conversation_id: str,
    update_data: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
        Conversation.deleted_at == None
    ).first()
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    if update_data.title is not None:
        conv.title = update_data.title
    if update_data.is_pinned is not None:
        conv.is_pinned = update_data.is_pinned
        
    db.commit()
    db.refresh(conv)
    
    return {"id": conv.id, "title": conv.title, "is_pinned": conv.is_pinned}

@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
        Conversation.deleted_at == None
    ).first()
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    conv.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "success"}
