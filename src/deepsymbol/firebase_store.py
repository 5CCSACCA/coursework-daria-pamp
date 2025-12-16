import os
from typing import Any, Dict, Optional

import firebase_admin
from firebase_admin import credentials, firestore

_db: Optional[firestore.Client] = None


def get_db() -> firestore.Client:
    global _db
    if _db is not None:
        return _db

    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path or not os.path.exists(cred_path):
        raise RuntimeError(
            "Firebase credentials not found. Check GOOGLE_APPLICATION_CREDENTIALS and docker-compose volume mount."
        )

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    _db = firestore.client()
    return _db


def save_output(item_id: str, payload: Dict[str, Any]) -> None:
    db = get_db()
    db.collection("outputs").document(str(item_id)).set(payload)


def get_output(item_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    doc = db.collection("outputs").document(str(item_id)).get()
    return doc.to_dict() if doc.exists else None


def list_outputs(limit: int = 50) -> list[Dict[str, Any]]:
    db = get_db()
    docs = db.collection("outputs").limit(limit).stream()
    out = []
    for d in docs:
        row = d.to_dict() or {}
        row["id"] = d.id
        out.append(row)
    return out


def update_output(item_id: str, patch: Dict[str, Any]) -> None:
    db = get_db()
    db.collection("outputs").document(str(item_id)).update(patch)


def delete_output(item_id: str) -> None:
    db = get_db()
    db.collection("outputs").document(str(item_id)).delete()

