from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.responses import JSONResponse
import base64
import uuid
import psycopg2
import pika
import firebase_admin
from firebase_admin import credentials, auth, firestore

import os

app = FastAPI(title="Gateway API", description="Entry point for DeepSymbol pipeline")

# -----------------------------
# 1. Firebase Init
# -----------------------------
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")

cred = credentials.Certificate(FIREBASE_CREDENTIALS)
firebase_admin.initialize_app(cred)
db_firestore = firestore.client()

# -----------------------------
# 2. PostgreSQL Init
# -----------------------------
conn = psycopg2.connect(
    dbname="deep_symbol",
    user="admin",
    password="admin123",
    host="database",
    port=5432
)
conn.autocommit = True

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS requests (
    id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(200),
    filename VARCHAR(200),
    status VARCHAR(20)
);
""")

# -----------------------------
# 3. RabbitMQ Init
# -----------------------------
rabbit_connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="rabbitmq", credentials=pika.PlainCredentials("user", "pass"))
)
channel = rabbit_connection.channel()
channel.queue_declare(queue="task_queue", durable=True)


# -----------------------------
# Health Check
# -----------------------------
@app.get("/")
def home():
    return {"status": "Gateway API alive"}


# -----------------------------
# Upload endpoint (image upload)
# -----------------------------
@app.post("/upload-image/")
async def upload_image(file: UploadFile = File(...), authorization: str = Header(None)):
    # Validate Firebase token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Firebase token")

    id_token = authorization.replace("Bearer ", "")

    try:
        decoded = auth.verify_id_token(id_token)
        user_id = decoded["uid"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")

    # Read and encode image
    image_bytes = await file.read()
    image_b64 = base64.b64encode(image_bytes).decode()

    request_id = str(uuid.uuid4())

    # Save request to PostgreSQL
    cursor.execute(
        "INSERT INTO requests (id, user_id, filename, status) VALUES (%s, %s, %s, %s)",
        (request_id, user_id, file.filename, "pending")
    )

    # Save Firestore document
    db_firestore.collection("art_requests").document(request_id).set({
        "user_id": user_id,
        "filename": file.filename,
        "status": "pending",
    })

    # Send to RabbitMQ
    message = {
        "id": request_id,
        "image_b64": image_b64,
    }

    channel.basic_publish(
        exchange="",
        routing_key="task_queue",
        body=str(message).encode(),
        properties=pika.BasicProperties(delivery_mode=2)
    )

    return {"request_id": request_id, "status": "queued"}


# -----------------------------
# Status endpoint
# -----------------------------
@app.get("/status/{request_id}")
def get_status(request_id: str):
    doc = db_firestore.collection("art_requests").document(request_id).get()
    if not doc.exists:
        return JSONResponse(status_code=404, content={"error": "Request not found"})
    return doc.to_dict()
