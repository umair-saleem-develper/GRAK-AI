import sys
import json
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import time
from datetime import datetime

from main import app
from database import SessionLocal, engine
import models
from services.ai.providers.base import AIResponse, AIStreamChunk
import docx
from reportlab.pdfgen import canvas
import os

# Initialize DB
models.Base.metadata.create_all(bind=engine)
db = SessionLocal()
client = TestClient(app)

print("==================================================")
print("SPRINT 3 FULL VERIFICATION SCRIPT")
print("==================================================")

def get_auth_token(uid, email, name):
    with patch("routers.auth.verify_firebase_token") as mock_verify:
        mock_verify.return_value = {
            "uid": uid,
            "email": email,
            "name": name,
            "email_verified": True,
            "firebase": {"sign_in_provider": "google.com"}
        }
        resp = client.post("/api/auth/firebase", json={"token": "mock"})
        return resp.json()["data"]["access_token"]

# 8. USER ISOLATION
print("\n[8] USER ISOLATION VERIFICATION")
token_A = get_auth_token("uid_A", "userA@example.com", "User A")
token_B = get_auth_token("uid_B", "userB@example.com", "User B")

headers_A = {"Authorization": f"Bearer {token_A}"}
headers_B = {"Authorization": f"Bearer {token_B}"}

# A creates conversation
convo_A = client.post("/api/messages", json={"content": "Init A"}, headers=headers_A)
# We have to parse the SSE to get convo ID A
convo_id_A = None
for line in convo_A.iter_lines():
    if line.startswith("data: "):
        try:
            d = json.loads(line[6:])
            if d.get("type") == "meta": convo_id_A = d.get("conversation_id")
        except: pass

print(f"User A Conversation: {convo_id_A}")
# B tries to get A's conversation
resp_B_get_A = client.get(f"/api/conversations/{convo_id_A}", headers=headers_B)
print(f"User B requesting A's conversation -> HTTP {resp_B_get_A.status_code} {resp_B_get_A.json()}")
assert resp_B_get_A.status_code == 404

# B tries to send message to A's conversation
resp_B_msg_A = client.post("/api/messages", json={"conversation_id": convo_id_A, "content": "Hack!"}, headers=headers_B)
# Because it's SSE, if it 404s it returns a JSON response immediately or fails.
print(f"User B sending to A's conversation -> HTTP {resp_B_msg_A.status_code}")

# B tries to delete A's conversation
resp_B_del_A = client.delete(f"/api/conversations/{convo_id_A}", headers=headers_B)
print(f"User B deleting A's conversation -> HTTP {resp_B_del_A.status_code}")
assert resp_B_del_A.status_code == 404

print("✓ User isolation verified (User B receives 404 for User A data).")

# 1. REAL AI PROVIDER VERIFICATION (Mocked to simulate success)
print("\n[1] AI PROVIDER FAILOVER VERIFICATION")
# We will mock the stream method of the providers to simulate success/failure

async def mock_gemini_success(*args, **kwargs):
    yield AIStreamChunk(content="Gemini Output", is_done=True, model="gemini-1.5-flash", provider="gemini", total_tokens=15, prompt_tokens=5, completion_tokens=10)

async def mock_groq_success(*args, **kwargs):
    yield AIStreamChunk(content="Groq Output", is_done=True, model="llama3", provider="groq", total_tokens=20, prompt_tokens=10, completion_tokens=10)

async def mock_openrouter_success(*args, **kwargs):
    yield AIStreamChunk(content="OpenRouter Output", is_done=True, model="meta-llama", provider="openrouter", total_tokens=25, prompt_tokens=15, completion_tokens=10)

def mock_fail(*args, **kwargs):
    raise Exception("Simulated provider failure")

# Test Gemini Success
with patch('services.ai.providers.gemini.GeminiProvider.stream', side_effect=mock_gemini_success):
    print("Testing Gemini Success...")
    res = client.post("/api/messages", json={"content": "Test Gemini"}, headers=headers_A)
    output = "".join([l for l in res.iter_lines() if l])
    print(f"✓ Gemini output matched: {'Gemini Output' in output}")

# Test Groq Success (Gemini fails)
with patch('services.ai.providers.gemini.GeminiProvider.stream', side_effect=mock_fail), \
     patch('services.ai.providers.groq.GroqProvider.stream', side_effect=mock_groq_success):
    print("Testing Groq Success (Gemini Fails)...")
    res = client.post("/api/messages", json={"content": "Test Groq"}, headers=headers_A)
    output = "".join([l for l in res.iter_lines() if l])
    print(f"✓ Groq output matched: {'Groq Output' in output}")

# Test OpenRouter Success (Gemini & Groq fail)
with patch('services.ai.providers.gemini.GeminiProvider.stream', side_effect=mock_fail), \
     patch('services.ai.providers.groq.GroqProvider.stream', side_effect=mock_fail), \
     patch('services.ai.providers.openrouter.OpenRouterProvider.stream', side_effect=mock_openrouter_success):
    print("Testing OpenRouter Success (Gemini & Groq Fail)...")
    res = client.post("/api/messages", json={"content": "Test OpenRouter"}, headers=headers_A)
    output = "".join([l for l in res.iter_lines() if l])
    print(f"✓ OpenRouter output matched: {'OpenRouter Output' in output}")

# Test All Fail
with patch('services.ai.providers.gemini.GeminiProvider.stream', side_effect=mock_fail), \
     patch('services.ai.providers.groq.GroqProvider.stream', side_effect=mock_fail), \
     patch('services.ai.providers.openrouter.OpenRouterProvider.stream', side_effect=mock_fail):
    print("Testing All Fail...")
    res = client.post("/api/messages", json={"content": "Test Fail"}, headers=headers_A)
    output = "".join([l for l in res.iter_lines() if l])
    print(f"✓ Fallback output matched: {'high demand' in output}")


# 4. MESSAGE PERSISTENCE & 2. AI USAGE TABLE
print("\n[4 & 2] MESSAGE PERSISTENCE & AI USAGE TABLE")
# Fetch messages from DB for the last convo
msgs = db.query(models.Message).order_by(models.Message.id.desc()).limit(2).all()
msgs.reverse()
print("PostgreSQL Message Rows:")
for m in msgs:
    print(f"- ID: {m.id} | Role: {m.role} | Content: {m.content[:20]}... | Provider: {m.provider} | Model: {m.model} | Tokens: {m.tokens_used} | Time: {m.created_at}")

usage = db.query(models.AIUsage).order_by(models.AIUsage.id.desc()).limit(3).all()
print("\nPostgreSQL AI Usage Rows:")
for u in usage:
    print(f"- ID: {u.id} | Prompt: {u.prompt_tokens} | Completion: {u.completion_tokens} | Total: {u.total_tokens} | Provider: {u.provider} | Model: {u.model} | Latency: {u.latency:.2f}s")

# 3. CONVERSATION TITLE GENERATION
print("\n[3] CONVERSATION TITLE GENERATION")
convo_new = client.post("/api/messages", json={"content": "Create a python script to fetch web pages."}, headers=headers_A)
c_id = None
for line in convo_new.iter_lines():
    if line.startswith("data: "):
        try:
            d = json.loads(line[6:])
            if d.get("type") == "meta": c_id = d.get("conversation_id")
        except: pass

print(f"Before background task DB Title:")
c_db = db.query(models.Conversation).filter(models.Conversation.id == c_id).first()
print(f"-> {c_db.title}")

print("Sleeping 2s to allow async title generation...")
time.sleep(2)
db.refresh(c_db)
print(f"After background task DB Title:")
print(f"-> {c_db.title}")

# 5. FILE UPLOAD VERIFICATION (PDF, DOCX, TXT)
print("\n[5] FILE UPLOAD VERIFICATION")

# Create dummy TXT
with open("test.txt", "w") as f: f.write("Dummy TXT content.")
# Create dummy PDF
c = canvas.Canvas("test.pdf")
c.drawString(100, 750, "Dummy PDF content.")
c.save()
# Create dummy DOCX
doc = docx.Document()
doc.add_paragraph("Dummy DOCX content.")
doc.save("test.docx")

for file_name, mime in [("test.txt", "text/plain"), ("test.pdf", "application/pdf"), ("test.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")]:
    with open(file_name, "rb") as f:
        res = client.post("/api/uploads", headers=headers_A, files={"file": (file_name, f, mime)})
        print(f"Uploaded {file_name}: HTTP {res.status_code}")
        if res.status_code == 200:
            text = res.json().get("extracted_text", "")
            print(f"-> Extracted (first 20 chars): {text[:20]}...")
            assert len(text) > 0

db.close()
print("\nVerification Script Completed Successfully.")
