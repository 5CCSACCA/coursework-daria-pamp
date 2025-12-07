from fastapi import FastAPI, UploadFile, File
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

@app.post("/process-art")
async def process_art(file: UploadFile = File(...)):
    """
    Async Endpoint:
    1. Saves 'pending' status to Firebase.
    2. Pushes image to RabbitMQ.
    3. Returns ID immediately.
    """
    # 1. Create DB entry first
    doc_ref = db.collection('art_requests').document()
    doc_ref.set({
        "filename": file.filename,
        "status": "pending", # Start as pending
        "timestamp": firestore.SERVER_TIMESTAMP
    })
    request_id = doc_ref.id

    # 2. Prepare message for RabbitMQ
    file_content = await file.read()
    # Convert bytes to base64 string to send via JSON
    image_b64 = base64.b64encode(file_content).decode('utf-8')

    message = {
        "id": request_id,
        "filename": file.filename,
        "image_b64": image_b64
    }

    # 3. Send to RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='task_queue', durable=True)
    
    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make message persistent
        ))
    connection.close()

    # 4. Return immediately!
    return {
        "id": request_id,
        "status": "queued",
        "message": "Your art is being processed in the background."
    }

@app.get("/history")
def get_history():
    docs = db.collection('art_requests').order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
    return [{"id": d.id, **d.to_dict(), "timestamp": str(d.to_dict().get("timestamp"))} for d in docs]
