from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
import hashlib
import secrets

import models
import schemas
from database import get_db
from services import auth
from services.audit import log_auth_event, get_client_ip, get_user_agent
from services.firebase_service import verify_firebase_token
from services.email_service import send_otp_email
from config import settings
from middleware import limiter

router = APIRouter(prefix="/api/auth", tags=["auth"])

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

@router.post("/firebase")
@limiter.limit("5/minute")
def firebase_login(request: Request, response: Response, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header.split(" ")[1]
    
    try:
        decoded_token = verify_firebase_token(token)
        email = decoded_token.get("email")
        firebase_uid = decoded_token.get("uid")
        
        if not email:
            raise ValueError("Email missing from Firebase token")
            
        user = db.query(models.User).filter(models.User.email == email).first()
        
        if not user:
            # Create user if it doesn't exist
            # password can be a random hash since they login via firebase
            random_pw = auth.get_password_hash(str(uuid.uuid4()))
            user = models.User(
                email=email,
                hashed_password=random_pw,
                is_verified=decoded_token.get("email_verified", False),
                display_name=decoded_token.get("name")
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
        # Check lockout
        if user.locked_until and user.locked_until.replace(tzinfo=None) > datetime.utcnow():
            log_auth_event(db, "Failed Login", "failure", user_id=user.id, ip=ip, user_agent=ua, metadata={"reason": "account_locked"})
            raise HTTPException(status_code=403, detail="Account locked. Try again later.")
            
        # Issue JWTs
        access_token = auth.create_access_token(data={"sub": user.id})
        raw_refresh_token = str(uuid.uuid4())
        hashed_refresh = hash_token(raw_refresh_token)
        
        session = models.Session(
            user_id=user.id,
            refresh_token_hash=hashed_refresh,
            ip_address=ip,
            user_agent=ua,
            device_name=None, # Extract from UA in a real app
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(session)
        db.commit()
        
        # Set HttpOnly Cookie
        response.set_cookie(
            key="refresh_token",
            value=raw_refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        )
        
        provider = decoded_token.get("firebase", {}).get("sign_in_provider", "firebase")
        log_auth_event(db, "Google Login" if provider == "google.com" else "Email Login", "success", user.id, ip, ua, {"provider": provider})
        
        return {"success": True, "data": {"access_token": access_token}, "error": None}
        
    except ValueError as e:
        log_auth_event(db, "Login", "failure", ip=ip, user_agent=ua, metadata={"error": str(e)})
        raise HTTPException(status_code=401, detail="Invalid Firebase token")
    except Exception as e:
        print(f"Exception in firebase_login: {e}")
        log_auth_event(db, "Login", "failure", ip=ip, user_agent=ua, metadata={"error": "Token verification failed", "details": str(e)})
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

@router.post("/refresh")
@limiter.limit("10/minute")
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    raw_rt = request.cookies.get("refresh_token")
    
    if not raw_rt:
        raise HTTPException(status_code=401, detail="No refresh token found")
        
    hashed_rt = hash_token(raw_rt)
    session = db.query(models.Session).filter(
        models.Session.refresh_token_hash == hashed_rt,
        models.Session.revoked == False
    ).first()
    
    if not session or session.expires_at.replace(tzinfo=None) < datetime.utcnow():
        if session:
            session.revoked = True
            db.commit()
        response.delete_cookie("refresh_token")
        raise HTTPException(status_code=401, detail="Invalid or expired session")
        
    # Rotate token
    new_raw_rt = str(uuid.uuid4())
    new_hashed_rt = hash_token(new_raw_rt)
    
    # Revoke old session and create new to prevent replay attacks (or just update hash)
    # Updating hash on the same session ID is cleaner for tracking devices
    session.refresh_token_hash = new_hashed_rt
    session.last_activity = datetime.utcnow()
    db.commit()
    
    access_token = auth.create_access_token(data={"sub": session.user_id})
    
    response.set_cookie(
        key="refresh_token",
        value=new_raw_rt,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    )
    
    log_auth_event(db, "Token Refresh", "success", session.user_id, ip, ua)
    return {"success": True, "data": {"access_token": access_token}, "error": None}

@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    raw_rt = request.cookies.get("refresh_token")
    
    if raw_rt:
        hashed_rt = hash_token(raw_rt)
        session = db.query(models.Session).filter(models.Session.refresh_token_hash == hashed_rt).first()
        if session:
            session.revoked = True
            log_auth_event(db, "Logout", "success", session.user_id, ip, ua)
            db.commit()
    
    response.delete_cookie("refresh_token")
    return {"success": True, "data": {}, "error": None}

@router.post("/logout-all")
def logout_all(current_user: models.User = Depends(auth.get_current_user), request: Request = None, response: Response = None, db: Session = Depends(get_db)):
    ip = get_client_ip(request) if request else "unknown"
    ua = get_user_agent(request) if request else "unknown"
    
    db.query(models.Session).filter(
        models.Session.user_id == current_user.id,
        models.Session.revoked == False
    ).update({"revoked": True})
    db.commit()
    
    if response:
        response.delete_cookie("refresh_token")
        
    log_auth_event(db, "Logout All", "success", current_user.id, ip, ua)
    return {"success": True, "data": {}, "error": None}

@router.get("/me")
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    data = {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "is_verified": current_user.is_verified,
        "tokens": current_user.tokens,
        "display_name": current_user.display_name,
        "avatar_url": current_user.avatar_url,
    }
    return {"success": True, "data": data, "error": None}

@router.post("/send-otp")
@limiter.limit("5/hour")
def send_otp(req: schemas.SendOTPRequest, request: Request, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    
    # Check for recent OTP requests (30-second cooldown)
    cooldown_time = datetime.utcnow() - timedelta(seconds=30)
    recent_otp = db.query(models.OTPVerification).filter(
        models.OTPVerification.email == req.email,
        models.OTPVerification.purpose == req.purpose,
        models.OTPVerification.created_at > cooldown_time
    ).first()
    
    if recent_otp:
        raise HTTPException(status_code=429, detail="Please wait 30 seconds before requesting another OTP.")
        
    # Delete previous OTPs for this email and purpose
    db.query(models.OTPVerification).filter(
        models.OTPVerification.email == req.email,
        models.OTPVerification.purpose == req.purpose
    ).delete()
    
    # Generate 6-digit secure OTP
    otp_code = str(secrets.randbelow(900000) + 100000)
    
    # Hash OTP
    otp_hash = hash_token(otp_code)
    
    new_otp = models.OTPVerification(
        email=req.email,
        otp_hash=otp_hash,
        purpose=req.purpose,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(new_otp)
    db.commit()
    
    # Send email
    try:
        send_otp_email(req.email, otp_code)
    except Exception as e:
        db.delete(new_otp)
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to send OTP email")
        
    return {"success": True, "message": "OTP sent successfully"}

@router.post("/verify-otp")
@limiter.limit("5/minute")
def verify_otp(req: schemas.VerifyOTPRequest, response: Response, request: Request, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    
    otp_record = db.query(models.OTPVerification).filter(
        models.OTPVerification.email == req.email,
        models.OTPVerification.purpose == req.purpose
    ).first()
    
    if not otp_record:
        raise HTTPException(status_code=400, detail="No OTP requested for this email or it has expired.")
        
    if otp_record.attempts >= 3:
        db.delete(otp_record)
        db.commit()
        raise HTTPException(status_code=400, detail="Too many failed attempts. Please request a new OTP.")
        
    if datetime.utcnow() > otp_record.expires_at.replace(tzinfo=None):
        db.delete(otp_record)
        db.commit()
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
        
    provided_hash = hash_token(req.code.strip())
    if provided_hash != otp_record.otp_hash:
        otp_record.attempts += 1
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid code. Please try again.")
        
    otp_record.verified_at = datetime.utcnow()
    db.delete(otp_record)
    
    user = db.query(models.User).filter(models.User.email == req.email).first()
    
    if not user:
        random_pw = auth.get_password_hash(str(uuid.uuid4()))
        user = models.User(
            email=req.email,
            hashed_password=random_pw,
            is_verified=True,
            display_name=req.email.split('@')[0]
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not user.is_verified:
        user.is_verified = True
        db.commit()

    if user.locked_until and user.locked_until.replace(tzinfo=None) > datetime.utcnow():
        log_auth_event(db, "Failed Login", "failure", user_id=user.id, ip=ip, user_agent=ua, metadata={"reason": "account_locked"})
        raise HTTPException(status_code=403, detail="Account locked. Try again later.")

    access_token = auth.create_access_token(data={"sub": user.id})
    raw_refresh_token = str(uuid.uuid4())
    hashed_refresh = hash_token(raw_refresh_token)
    
    session = models.Session(
        user_id=user.id,
        refresh_token_hash=hashed_refresh,
        ip_address=ip,
        user_agent=ua,
        device_name=None,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(session)
    db.commit()
    
    response.set_cookie(
        key="refresh_token",
        value=raw_refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    )
    
    log_auth_event(db, "Email Login", "success", user.id, ip, ua, {"method": "otp"})
    
    return {"success": True, "data": {"access_token": access_token}, "error": None}
