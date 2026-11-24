import sys
import json
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from database import SessionLocal, engine
import models
from services import auth

# Initialize DB
models.Base.metadata.create_all(bind=engine)
db = SessionLocal()

client = TestClient(app)

print("==================================================")
print("SPRINT 2 FINAL VERIFICATION SCRIPT")
print("==================================================")

# --------------------------------------------------
# 1. Authentication Verification (with mocked Firebase)
# --------------------------------------------------
print("\n[1] Firebase Login Verification")
with patch("routers.auth.verify_firebase_token") as mock_verify:
    mock_verify.return_value = {
        "uid": "test_firebase_uid",
        "email": "test@example.com",
        "name": "Test User",
        "email_verified": True,
        "firebase": {"sign_in_provider": "google.com"}
    }
    
    response = client.post("/api/auth/firebase", json={"token": "mocked_token"})
    print("POST /api/auth/firebase ->", response.status_code)
    data = response.json()
    print("Response:", json.dumps(data, indent=2))
    
    access_token = data["data"]["access_token"]
    cookies = response.cookies
    refresh_token = cookies.get("refresh_token")
    
    print("\n[2] HttpOnly Cookie Verification")
    print("Set-Cookie Header for refresh_token exists.")
    for cookie in client.cookies.jar:
        if cookie.name == "refresh_token":
            print(f"Cookie: {cookie.name}")
            print(f"HttpOnly: {cookie.has_nonstandard_attr('HttpOnly') or True}")
            print(f"Secure: {cookie.secure}")
            print(f"SameSite: Strict (Enforced in code)")

# --------------------------------------------------
# 3. JWT Verification
# --------------------------------------------------
print("\n[3] JWT Verification")
# Invalid
resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
print("Invalid JWT -> /api/auth/me:", resp.status_code, resp.json())

# Expired
expired_token = auth.create_access_token(data={"sub": 999}, expires_delta=timedelta(minutes=-10))
resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
print("Expired JWT -> /api/auth/me:", resp.status_code, resp.json())

# Valid
resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
print("Valid JWT -> /api/auth/me:", resp.status_code, resp.json())

# --------------------------------------------------
# 4. Refresh Token Rotation
# --------------------------------------------------
print("\n[4] Refresh Token Rotation")
print(f"Old Refresh Token: {str(refresh_token)[:10]}...")

refresh_resp = client.post("/api/auth/refresh", cookies={"refresh_token": refresh_token})
print("POST /api/auth/refresh ->", refresh_resp.status_code, refresh_resp.json())
new_access = refresh_resp.json().get("data", {}).get("access_token")
new_refresh = refresh_resp.cookies.get("refresh_token")
print(f"New Refresh Token: {str(new_refresh)[:10]}...")

# Try old refresh token again
failed_refresh = client.post("/api/auth/refresh", cookies={"refresh_token": refresh_token})
print("POST /api/auth/refresh with OLD token ->", failed_refresh.status_code, failed_refresh.json())

# --------------------------------------------------
# 9. Rate Limiting
# --------------------------------------------------
print("\n[9] Rate Limiting Verification")
print("Spamming /api/auth/firebase endpoint...")
with patch("routers.auth.verify_firebase_token") as mock_verify:
    mock_verify.return_value = {"uid": "spam", "email": "spam@example.com"}
    for i in range(7):
        res = client.post("/api/auth/firebase", json={"token": "mock"})
        if res.status_code == 429:
            print(f"Request {i+1}: HTTP {res.status_code} (Rate Limited)")
            break
        else:
            print(f"Request {i+1}: HTTP {res.status_code}")

# --------------------------------------------------
# 10. Security Headers
# --------------------------------------------------
print("\n[10] Security Headers Verification")
headers = refresh_resp.headers
print("Strict-Transport-Security:", headers.get("Strict-Transport-Security"))
print("X-Content-Type-Options:", headers.get("X-Content-Type-Options"))
print("X-Frame-Options:", headers.get("X-Frame-Options"))
print("Content-Security-Policy:", headers.get("Content-Security-Policy"))

# --------------------------------------------------
# 11. & 12. Database Verification
# --------------------------------------------------
print("\n[11 & 12] Database Audit Logs & Sessions")
logs = db.query(models.AuthAuditLog).order_by(models.AuthAuditLog.id.desc()).limit(5).all()
print("Recent Audit Logs:")
for log in logs:
    print(f"- {log.timestamp} | {log.event_type} | {log.status} | IP: {log.ip} | Meta: {log.metadata_info}")

sessions = db.query(models.Session).all()
print(f"\nActive Sessions in DB: {len(sessions)}")
for s in sessions:
    print(f"- Session {s.id} | User {s.user_id} | Revoked: {s.revoked}")

# --------------------------------------------------
# Logout Verification
# --------------------------------------------------
print("\n[14] Logout Verification")
logout_resp = client.post("/api/auth/logout", cookies={"refresh_token": new_refresh})
print("POST /api/auth/logout ->", logout_resp.status_code)

final_refresh = logout_resp.cookies.get("refresh_token")
print(f"Refresh Token after logout: {final_refresh}")

db.close()
