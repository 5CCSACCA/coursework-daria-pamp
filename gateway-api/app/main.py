from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

import firebase_admin
from firebase_admin import credentials, firestore, auth

import pika
import json
import base64
import os
import uuid
import traceback


# Firebase init
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


# FastAPI + CORS
app = FastAPI(title="Gateway API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


# RabbitMQ Connection
def get_rabbit_channel():
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="rabbitmq")
        )
        channel = connection.channel()
        channel.queue_declare(queue="task_queue", durable=True)
        return connection, channel
    except Exception as e:
        print("\n[RABBIT ERROR]", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="RabbitMQ unreachable")


# Firebase Token Validation
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        decoded = auth.verify_id_token(token)
        # return ONLY the user_id for simplicity
        return decoded["user_id"]
    except Exception as e:
        print("\n[FIREBASE ERROR]", e)
        traceback.print_exc()
        raise HTTPException(status_code=401, detail="Invalid Firebase token")


# -------------------------------------
# HEALTH CHECK
# -------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# -------------------------------------
# MAIN PIPELINE ENDPOINT
# -------------------------------------
@app.post("/process-art")
async def process_art(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    try:
        print(f"\nUser {user_id} requested processing.")

        # Read image bytes
        file_bytes = await file.read()
        image_b64 = base64.b64encode(file_bytes).decode()

        # Create unique request ID
        req_id = str(uuid.uuid4())

        # Store initial record in Firestore
        doc_ref = db.collection("requests").document(req_id)
        doc_ref.set({
            "user_id": user_id,
            "status": "queued",
            "filename": file.filename,
        })

        # Prepare message for worker
        message = {
            "request_id": req_id,
            "user_id": user_id,
            "image": image_b64
        }

        # Send to RabbitMQ
        connection, channel = get_rabbit_channel()
        channel.basic_publish(
            exchange="",
            routing_key="task_queue",
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        connection.close()

        return {
            "status": "queued",
            "id": req_id
        }

    except Exception as e:
        print("\n[PROCESS ERROR]", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal processing error")
