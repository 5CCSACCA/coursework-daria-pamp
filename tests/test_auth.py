import pytest
import firebase_admin

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

def test_require_firebase_user_missing_token(monkeypatch):
    # Make sure auth.py does not try to init Firebase in this test
    firebase_admin._apps = ["already-initialized"]

    from deepsymbol import auth as auth_module

    with pytest.raises(HTTPException) as e:
        auth_module.require_firebase_user(creds=None)

    assert e.value.status_code == 401


def test_require_firebase_user_valid_token(monkeypatch):
    firebase_admin._apps = ["already-initialized"]

    from deepsymbol import auth as auth_module

    # Mock verify_id_token
    def fake_verify(token):
        assert token == "goodtoken"
        return {"uid": "u123", "email": "test@example.com"}

    monkeypatch.setattr(auth_module.fb_auth, "verify_id_token", fake_verify)

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="goodtoken")
    decoded = auth_module.require_firebase_user(creds=creds)
    assert decoded["uid"] == "u123"


def test_require_firebase_user_invalid_token(monkeypatch):
    firebase_admin._apps = ["already-initialized"]

    from deepsymbol import auth as auth_module

    def fake_verify(token):
        raise Exception("bad token")

    monkeypatch.setattr(auth_module.fb_auth, "verify_id_token", fake_verify)

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="badtoken")
    with pytest.raises(HTTPException) as e:
        auth_module.require_firebase_user(creds=creds)

    assert e.value.status_code == 401
