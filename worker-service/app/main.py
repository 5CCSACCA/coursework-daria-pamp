import pika
import json
import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os
import sys
import base64

# --- 1. Setup Firebase ---
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Service URLs
YOLO_URL = "http://yolo-service:8000/detect"
BITNET_URL = "http://bitnet-service:8001/generate"

# --- 2. Processing Logic ---
def process_task(ch, method, properties, body):
    print(f" [x] Received task")
    data = json.loads(body)
    
    request_id = data['id']
    filename = data['filename']
    # Decode image from Base64 back to bytes
    file_bytes = base64.b64decode(data['image_b64'])

    print(f"Processing {filename} (ID: {request_id})...")

    try:
        # 1. Call YOLO
        files = {'file': (filename, file_bytes, 'image/jpeg')}
        yolo_resp = requests.post(YOLO_URL, files=files)
        detections = [d['object'] for d in yolo_resp.json().get('detections', [])]
        print(f" -> YOLO found: {detections}")

        # 2. Call BitNet
        # Improve logic: handle empty detections
        if detections:
            prompt_objs = detections
        else:
            # Special case for abstract art/portraits
            prompt_objs = [] 
            
        bitnet_resp = requests.post(BITNET_URL, json={"detected_objects": prompt_objs})
        description = bitnet_resp.json().get('generated_description', 'No text')
        print(" -> BitNet generated text")

        # 3. Update Firebase
        # We find the existing document (created by Gateway) and update it
        doc_ref = db.collection('art_requests').document(request_id)
        doc_ref.update({
            "status": "completed",
            "objects": detections,
            "interpretation": description,
            "processed_at": firestore.SERVER_TIMESTAMP
        })
        print(f" -> Firebase updated. Task Done!")

    except Exception as e:
        print(f"ERROR: {e}")
        # Mark as failed in DB
        db.collection('art_requests').document(request_id).update({
            "status": "failed",
            "error": str(e)
        })

    # Acknowledge message (tell RabbitMQ we are done)
    ch.basic_ack(delivery_tag=method.delivery_tag)


# --- 3. RabbitMQ Connection ---
def main():
    print("Worker starting... waiting for RabbitMQ")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    # Declare the queue
    channel.queue_declare(queue='task_queue', durable=True)

    # Listen
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='task_queue', on_message_callback=process_task)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
