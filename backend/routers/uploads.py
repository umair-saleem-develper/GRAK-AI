from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from database import get_db
from models import User, Upload
from services.auth import get_current_user
from services.document_parser import DocumentParser

router = APIRouter(prefix="/api/uploads", tags=["Uploads"])

@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Read the file content
    content = await file.read()
    
    import asyncio
    import base64
    # Extract text from file in a background worker thread to never block FastAPI's event loop
    extracted_text = await asyncio.to_thread(DocumentParser.parse_file, content, file.content_type, file.filename)
    
    is_image = "image" in (file.content_type or "").lower() or any(
        file.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"]
    )
    
    # Requirement 3: If image extraction really fails, do not send placeholder to chat; return clear error
    if is_image and not extracted_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not read this image"
        )
    
    image_b64 = None
    if is_image:
        mime = file.content_type if file.content_type and "image/" in file.content_type else "image/png"
        image_b64 = f"data:{mime};base64,{base64.b64encode(content).decode('utf-8')}"
    
    if not extracted_text:
        extracted_text = f"[Attached file: {file.filename}]"
    elif extracted_text.startswith("[Unsupported"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract text from file or unsupported format."
        )
    
    # Save Upload metadata to database (simulating storage)
    upload_record = Upload(
        user_id=current_user.id,
        filename=file.filename,
        file_url=f"local://extracted/{file.filename}",
        file_type=file.content_type,
        storage_provider="local_memory"
    )
    db.add(upload_record)
    db.commit()
    db.refresh(upload_record)
    
    return {
        "id": upload_record.id,
        "filename": upload_record.filename,
        "extracted_text": extracted_text,
        "text": extracted_text,
        "image_base64": image_b64
    }
