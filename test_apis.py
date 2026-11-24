import threading
import time
import requests
import uvicorn
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from backend.main import app
from backend.database import Base, engine, SessionLocal
from backend import models

client = TestClient(app)

print("Starting API Verification Tests...")

# Reset DB
models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

print("\n--- 1. Register API ---")
resp = client.post("/api/auth/register", json={"email": "test@example.com", "password": "password123"})
print(resp.json())

print("\n--- 2. Login API ---")
resp = client.post("/api/auth/login", json={"email": "test@example.com", "password": "password123"})
print(resp.json())
token = resp.json().get("data", {}).get("access_token")

headers = {"Authorization": f"Bearer {token}"}

print("\n--- 3. Create Conversation ---")
resp = client.post("/api/conversations/", json={"title": "Test Chat", "messages": [{"role": "user", "content": "Hello"}]}, headers=headers)
print(resp.json())
conv_id = resp.json().get("data", {}).get("id")

print("\n--- 4. Get Conversations ---")
resp = client.get("/api/conversations/", headers=headers)
print(resp.json())

print("\n--- 5. Delete Conversation ---")
resp = client.delete(f"/api/conversations/{conv_id}", headers=headers)
print(resp.json())

print("\n--- 6. Security (Missing JWT) ---")
resp = client.get("/api/conversations/")
print(resp.json())

print("\n--- 7. Security (Invalid JWT) ---")
resp = client.get("/api/conversations/", headers={"Authorization": "Bearer fake.token.here"})
print(resp.json())

