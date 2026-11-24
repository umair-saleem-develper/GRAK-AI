import os
os.environ.setdefault("WRAPT_DISABLE_EXTENSIONS", "true")
import json
from dotenv import load_dotenv

# Load env variables first
load_dotenv(override=True)

import sentry_sdk
from config import settings
from services.firebase_service import init_firebase

# Init Firebase
init_firebase()

if getattr(settings, "SENTRY_DSN", None):
    sentry_sdk.init(dsn=settings.SENTRY_DSN)

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import uuid

from services.auth import get_current_user, deduct_tokens
from services.huggingface import generate_image as hf_generate_image
from services.ai_engine import generate_text, generate_text_stream, hybrid_web_research, PROVIDER_DIAGNOSTICS, check_provider_health, generate_text_stream, hybrid_web_research
from services.document_generator import create_word_document, create_powerpoint_presentation
from database import engine, Base
import models

# Auto-create tables on startup if not already created
try:
    Base.metadata.create_all(bind=engine)
except Exception as db_init_err:
    print(f"Database auto-migration warning: {db_init_err}")

app = FastAPI(title="OmniAI Backend")

# Dynamic CORS for local development and Vercel production deployments
raw_origins = os.environ.get("ALLOWED_ORIGINS", os.environ.get("CORS_ORIGINS", ""))
if raw_origins:
    allowed_origins = [orig.strip() for orig in raw_origins.split(",") if orig.strip()]
else:
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8001",
    ]

# Regex matches any Vercel deployment preview or production domain (*.vercel.app)
allow_origin_regex = os.environ.get("CORS_ORIGIN_REGEX", r"https://.*\.vercel\.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from middleware import setup_middlewares
setup_middlewares(app)


# Create a static directory for downloads
DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
app.mount("/downloads", StaticFiles(directory=DOWNLOADS_DIR), name="downloads")
app.mount("/api/images", StaticFiles(directory=DOWNLOADS_DIR), name="api_images")

from routers.auth import router as auth_router
from routers.conversations import router as conv_router
app.include_router(auth_router)
app.include_router(conv_router)

from routers.messages import router as messages_router
from routers.uploads import router as uploads_router
from routers.voice import router as voice_router

app.include_router(messages_router)
app.include_router(uploads_router)
app.include_router(voice_router)

class ChatMessage(BaseModel):
    role: str
    content: str
    image_base64: Optional[str] = None
    images: Optional[List[str]] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ImageRequest(BaseModel):
    prompt: str

class DocumentRequest(BaseModel):
    topic: str
    doc_type: str # 'word' or 'ppt'

class ResearchRequest(BaseModel):
    query: str

@app.get("/api/diagnostics")
def get_diagnostics():
    return PROVIDER_DIAGNOSTICS

@app.post("/api/diagnostics/refresh")
def refresh_diagnostics():
    check_provider_health()
    return PROVIDER_DIAGNOSTICS

@app.get("/health")
def health_check():
    """Production health check endpoint for Render/uptime monitoring."""
    return {"status": "ok", "service": "OmniAI Backend"}

@app.get("/")
def read_root():
    return {"success": True, "data": {"status": "OmniAI Backend is running"}, "error": None}

@app.post("/api/research")
def research_endpoint(req: ResearchRequest, current_user = Depends(get_current_user)):
    try:
        reply = hybrid_web_research(req.query)
        return {"success": True, "data": {"reply": reply}, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/image")
def generate_image(req: ImageRequest, current_user = Depends(get_current_user)):
    # 3 tokens for image
    # if not deduct_tokens(current_user.id, 3):
    #     raise HTTPException(status_code=402, detail="Insufficient tokens")
    
    filename = f"image_{uuid.uuid4().hex}.png"
    filepath = os.path.join(DOWNLOADS_DIR, filename)
    
    success = hf_generate_image(req.prompt, filepath)
    
    if success:
        return {"success": True, "data": {"image_url": f"/downloads/{filename}"}, "error": None}
    else:
        # Fallback if API fails or no key
        return {"success": True, "data": {"image_url": "https://via.placeholder.com/512x512.png?text=Mock+AI+Image"}, "error": None}

@app.post("/api/document")
def generate_document(req: DocumentRequest, current_user = Depends(get_current_user)):
    # 5 tokens for document
    # if not deduct_tokens(current_user.id, 5):
    #     raise HTTPException(status_code=402, detail="Insufficient tokens")
    
    # Generate content using AI
    prompt = f"Generate a comprehensive and structured outline or content about: {req.topic}"
    content = generate_text(prompt)
    
    file_id = uuid.uuid4().hex
    
    if req.doc_type == "ppt":
        filename = f"presentation_{file_id}.pptx"
        filepath = os.path.join(DOWNLOADS_DIR, filename)
        create_powerpoint_presentation(req.topic, content, filepath)
    else:
        filename = f"document_{file_id}.docx"
        filepath = os.path.join(DOWNLOADS_DIR, filename)
        create_word_document(req.topic, content, filepath)
        
    data = {"file_url": f"/downloads/{filename}", "message": f"{req.doc_type.upper()} generated successfully."}
    return {"success": True, "data": data, "error": None}

@app.post("/api/research_web")
def research_web(req: ResearchRequest, current_user = Depends(get_current_user)):
    # 2 tokens for web research (optional based on your token economics)
    # if not deduct_tokens(current_user.id, 2):
    #     raise HTTPException(status_code=402, detail="Insufficient tokens")
    
    response_text = hybrid_web_research(req.query)
    return {"success": True, "data": {"reply": response_text}, "error": None}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
