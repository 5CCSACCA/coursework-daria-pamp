import uvicorn
from fastapi import FastAPI, File, UploadFile, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import firestore, auth
import pika
import base64
import uuid
import os
import json

app = FastAPI()

# CORS allowed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

firebase_admin.initialize_app()
db = firestore.client()

# RabbitMQ connection
def send_to_queue(data):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
    channel = connection.channel()
    channel.queue_declare(queue="task_queue", durable=True)
    channel.basic_publish(
        exchange="",
        routing_key="task_queue",
        body=json.dumps(data),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    connection.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/process-art")
async def process_art(file: UploadFile = File(...), authorization: str = Header(None)):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    user_token = authorization.split("Bearer ")[1].strip()

    try:
        decoded_user = firebase_admin.auth.verify_id_token(user_token)
        user_id = decoded_user["uid"]
    except:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")

    # Read image
    image_bytes = await file.read()
    image_b64 = base64.b64encode(image_bytes).decode()

    request_id = str(uuid.uuid4())

    # Write task to Firestore
    db.collection("art_requests").document(request_id).set({
        "user_id": user_id,
        "filename": file.filename,
        "status": "queued",
    })

    # Send task to RabbitMQ
    send_to_queue({
        "id": request_id,
        "filename": file.filename,
        "image_b64": image_b64,
    })

    return {"id": request_id, "status": "queued"}


@app.get("/history")
def history(authorization: str = Header(None)):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    user_token = authorization.split("Bearer ")[1].strip()

    try:
        decoded_user = firebase_admin.auth.verify_id_token(user_token)
        user_id = decoded_user["uid"]
    except:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")

    docs = db.collection("art_requests").where("user_id", "==", user_id).stream()

    return [
        {**doc.to_dict(), "id": doc.id}
        for doc in docs
    ]

@app.get("/status/{request_id}")
def get_status(request_id: str):
    doc = db.collection("art_requests").document(request_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Request not found")
    return doc.to_dict()


