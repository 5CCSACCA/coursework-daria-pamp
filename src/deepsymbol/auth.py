from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import os
import firebase_admin
from firebase_admin import credentials, auth as fb_auth

bearer_scheme = HTTPBearer(auto_error=False)

# Init Firebase Admin once
if not firebase_admin._apps:
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/app/secrets/firebase_key.json")
    firebase_admin.initialize_app(credentials.Certificate(cred_path))


def require_firebase_user(
    creds: HTTPAuthorizationCredentials = Security(bearer_scheme),
):
    """
    Swagger-friendly Firebase auth.
    Expects Authorization: Bearer <ID_TOKEN>
    """
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = creds.credentials.strip()
    try:
        decoded = fb_auth.verify_id_token(token)
        return decoded
    except Exception as e:
        print("AUTH ERROR:", repr(e))
        raise HTTPException(status_code=401, detail="Invalid or expired token")

