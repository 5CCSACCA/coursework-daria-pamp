from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware  # <--- STAGE 11: SECURITY
from prometheus_fastapi_instrumentator import Instrumentator # <--- STAGE 9: MONITORING
import firebase_admin
from firebase_admin import credentials, firestore
import pika
import json
import base64
import os

# --- Setup Firebase ---
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

app = FastAPI(title="ArtiFy Async Gateway")

# --- STAGE 11: SECURITY (CORS) ---
# Protects against unauthorized browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In real life, specific domains. For coursework, '*' is accepted.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- STAGE 9: MONITORING ---
# Automatically creates a /metrics endpoint for Prometheus
Instrumentator().instrument(app).expose(app)

@app.post("/process-art")
async def process_art(file: UploadFile = File(...)):
    # 1. Create DB entry
    doc_ref = db.collection('art_requests').document()
    doc_ref.set({
        "filename": file.filename,
        "status": "pending",
        "timestamp": firestore.SERVER_TIMESTAMP
    })
    request_id = doc_ref.id

    # 2. Prepare RabbitMQ message
    file_content = await file.read()
    image_b64 = base64.b64encode(file_content).decode('utf-8')

    message = {
        "id": request_id,
        "filename": file.filename,
        "image_b64": image_b64
    }

    # 3. Send to RabbitMQ
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()
        channel.queue_declare(queue='task_queue', durable=True)
        
        channel.basic_publish(
            exchange='',
            routing_key='task_queue',
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2))
        connection.close()
    except Exception as e:
        return {"error": f"RabbitMQ Error: {str(e)}"}

    return {
        "id": request_id,
        "status": "queued",
        "message": "Your art is being processed in the background."
    }

@app.get("/history")
def get_history():
    docs = db.collection('art_requests').order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
    return [{"id": d.id, **d.to_dict(), "timestamp": str(d.to_dict().get("timestamp"))} for d in docs]
