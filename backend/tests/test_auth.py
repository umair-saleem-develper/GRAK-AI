import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
# Force testing environment
os.environ["ENV"] = "testing"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models
from database import Base, get_db
from main import app
from config import settings

# Setup Testing DB
engine = create_engine(settings.TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def run_around_tests():
    # Setup before each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown after each test
    Base.metadata.drop_all(bind=engine)

def test_register_user():
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    
def test_register_duplicate_email():
    client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "password123"
    })
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 400
    
def test_login_success():
    client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "password123"
    })
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    
def test_login_failure_and_lockout():
    client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "password123"
    })
    
    # 5 failed attempts
    for i in range(5):
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        
    # 6th attempt should be locked out
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123" # even correct password should fail if locked
    })
    assert response.status_code == 403
    assert "locked" in response.json()["detail"].lower()

def test_refresh_token():
    client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "password123"
    })
    login_res = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    refresh_token = login_res.json()["refresh_token"]
    
    refresh_res = client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token
    })
    
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()
    assert "refresh_token" in refresh_res.json()

def test_logout():
    client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "password123"
    })
    login_res = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    access_token = login_res.json()["access_token"]
    
    logout_res = client.post("/api/auth/logout", headers={
        "Authorization": f"Bearer {access_token}"
    })
    assert logout_res.status_code == 200

def test_protected_profile_route():
    client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "password123"
    })
    login_res = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    access_token = login_res.json()["access_token"]
    
    profile_res = client.get("/api/user/profile", headers={
        "Authorization": f"Bearer {access_token}"
    })
    assert profile_res.status_code == 200
    assert profile_res.json()["email"] == "test@example.com"
    
def test_unauthorized_profile_access():
    profile_res = client.get("/api/user/profile")
    assert profile_res.status_code in (401, 403)
