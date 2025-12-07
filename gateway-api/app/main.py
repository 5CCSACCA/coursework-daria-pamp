from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

import firebase_admin
from firebase_admin import credentials, firestore, auth

import pika
import json
import base64
import os
import time


# ---------------------------
# Firebase Initialization
# ---------------------------
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()


# ---------------------------
# FastAPI App
# ---------------------------
app = FastAPI(title="ArtiFy Async Gateway (Secured)")


# ---------------------------
# CORS (Stage 11)
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # For coursework demo: open CORS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------
# Monitoring (Stage 9)
# ---------------------------
Instrumentator().instrument(app).expose(app)


# ---------------------------
# Authentication (Stage 7)
# ---------------------------
security = HTTPBearer()

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates the Firebase Token sent via Authorization header.
    """
    token = creds.credentials
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token["uid"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------
# Utility: Secure RabbitMQ Connection
# ---------------------------
def safe_rabbitmq_connection(max_retries: int = 5):
    """
    Attempts to connect to RabbitMQ with retry logic.
    Prevents gateway crash if RabbitMQ is slow to start.
    """
    for attempt in range(max_retries):
        try:
            return pika.BlockingConnection(
                pika.ConnectionParameters(host="rabbitmq")
            )
        except Exception as e:
            if attempt == max_retries - 1:
                raise HTTPException(
                    status_code=500,
                    detail=f"Cannot connect to RabbitMQ: {e}"
                )
            time.sleep(2)


# ---------------------------
# HEALTH ENDPOINT (Stage 9)
# ---------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------
# PROCESS ART ENDPOINT (Stage 6)
# ---------------------------
@app.post("/process-art")
async def process_art(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    """
    Receives an image, performs validation & security checks,
    stores metadata in Firestore,
    sends async processing task to RabbitMQ.
    """
    print(f"User {user_id} requested processing.")


    # ----------------------------------------
    # SECURITY CHECK 1: Limit file size (Stage 11)
    # ----------------------------------------
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(
            status_code=413,
            detail="Uploaded file is too large (max size = 5 MB)"
        )


    # ----------------------------------------
    # SECURITY CHECK 2: Ensure file is image
    # ----------------------------------------
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only image files are allowed"
        )


    # ----------------------------------------
    # STAGE 4/5: Create Firestore Request Entry
    # ----------------------------------------
    doc_ref = db.collection("art_requests").document()

    try:
        doc_ref.set({
            "user_id": user_id,
            "filename": file.filename,
            "status": "pending",
            "timestamp": firestore.SERVER_TIMESTAMP,
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Firestore Error: {e}"
        )

    request_id = doc_ref.id


    # ----------------------------------------
    # ENCODE IMAGE (base64)
    # ----------------------------------------
    file_bytes = await file.read()
    image_b64 = base64.b64encode(file_bytes).decode("utf-8")

    mq_message = {
        "id": request_id,
        "filename": file.filename,
        "image_b64": image_b64
    }


    # ----------------------------------------
    # SEND TO RABBITMQ (Stage 6)
    # ----------------------------------------
    try:
        connection = safe_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare(queue="task_queue", durable=True)

        channel.basic_publish(
            exchange="",
            routing_key="task_queue",
            body=json.dumps(mq_message),
            properties=pika.BasicProperties(delivery_mode=2)
        )

        connection.close()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"RabbitMQ Error: {e}"
        )


    # ----------------------------------------
    # ASYNC RESPONSE
    # ----------------------------------------
    return {
        "id": request_id,
        "status": "queued",
        "message": "Authenticated. Your artwork is being processed asynchronously."
    }


# ---------------------------
# GET HISTORY (Stage 4/5)
# ---------------------------
@app.get("/history")
def get_history(user_id: str = Depends(get_current_user)):
    """
    Returns processing history for the authenticated user.
    """
    try:
        docs = db.collection("art_requests").where(
            "user_id", "==", user_id
        ).stream()

        return [
            {
                "id": d.id,
                **d.to_dict(),
                "timestamp": str(d.to_dict().get("timestamp"))
            }
            for d in docs
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Firestore Error: {e}"
        )
