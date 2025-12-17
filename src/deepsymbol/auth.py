from fastapi import Header, HTTPException
import os
import firebase_admin
from firebase_admin import credentials, auth as fb_auth

# Initialize Firebase Admin exactly once
if not firebase_admin._apps:
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/app/secrets/firebase_key.json")
    firebase_admin.initialize_app(credentials.Certificate(cred_path))


def require_firebase_user(authorization: str = Header(default="")):
    """
    Require 'Authorization: Bearer <ID_TOKEN>' header and validate via Firebase Admin.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty token")

    try:
        decoded = fb_auth.verify_id_token(token)
        return decoded  # uid, email, etc.
    except Exception as e:
        # Helpful during development (shows real reason in docker logs)
        print("AUTH ERROR:", repr(e))
        raise HTTPException(status_code=401, detail="Invalid or expired token")

