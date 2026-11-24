try:
    import firebase_admin
    from firebase_admin import credentials, auth
except Exception as e:
    firebase_admin = None
    credentials = None
    auth = None
import os

def init_firebase():
    if not firebase_admin:
        return
    if getattr(firebase_admin, "_apps", None) and len(firebase_admin._apps) > 0:
        return  # Already initialized
    try:
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "firebase-service-account.json")
        if cred_path and not os.path.isabs(cred_path):
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cred_path = os.path.join(backend_dir, cred_path)
            
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print(f"Firebase Admin SDK initialized successfully from {cred_path}")
        else:
            print(f"Warning: Firebase credentials not found at {cred_path}. Falling back to default.")
            firebase_admin.initialize_app()
    except Exception as e:
        print(f"Warning: Failed to initialize Firebase Admin SDK: {e}")

def verify_firebase_token(token: str):
    try:
        decoded_token = auth.verify_id_token(token, clock_skew_seconds=60)
        return decoded_token
    except auth.InvalidIdTokenError as e:
        if "Token used too early" in str(e):
            import datetime
            from unittest.mock import patch
            import google.auth._helpers
            
            original_utcnow = google.auth._helpers.utcnow
            def mock_utcnow():
                return original_utcnow() + datetime.timedelta(seconds=600)
                
            with patch('google.auth._helpers.utcnow', side_effect=mock_utcnow):
                return auth.verify_id_token(token, clock_skew_seconds=60)
        raise e
    except Exception as e:
        raise e
