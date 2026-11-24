from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    is_verified: bool
    tokens: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class VerifyEmailRequest(BaseModel):
    token: str

class ResetPasswordRequestRequest(BaseModel):
    email: EmailStr

class ResetPasswordConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class FirebaseLoginRequest(BaseModel):
    token: str

class SendOTPRequest(BaseModel):
    email: EmailStr
    purpose: str = "login"

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    code: str
    purpose: str = "login"
