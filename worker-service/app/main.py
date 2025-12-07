import pika
import json
import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os
import sys
import base64
import time

# --- 1. Setup Firebase ---
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Service URLs (Internal Docker Network)
YOLO_URL = "http://yolo-service:8000/detect"
BITNET_URL = "http://bitnet-service:8001/generate"

# --- 2. Processing Logic ---
def process_task(ch, method, properties, body):
    print(f" [x] Received task")
    try:
        data = json.loads(body)
        request_id = data['id']
        filename = data['filename']
        # Decode image
        file_bytes = base64.b64decode(data['image_b64'])

        print(f"Processing {filename} (ID: {request_id})...")

        # 1. Call YOLO
        # We must verify YOLO gets the file correctly
        files = {'file': (filename, file_bytes, 'image/jpeg')}
        yolo_resp = requests.post(YOLO_URL, files=files)
        
        if yolo_resp.status_code == 200:
            detections = [d['object'] for d in yolo_resp.json().get('detections', [])]
            # Remove duplicates using set
            detections = list(set(detections))
        else:
            print(f"YOLO Error: {yolo_resp.text}")
            detections = []

        print(f" -> YOLO found: {detections}")

        # 2. Call BitNet (FIXED PROMPT LOGIC)
        # We verify if we have objects to create a logical prompt
        if detections:
            # Join objects: "cat, dog"
            objs_str = ", ".join(detections)
            prompt_payload = {"detected_objects": detections, "style": "poetic"}
        else:
            # Fallback if no objects found (prevents hallucination)
            prompt_payload = {"detected_objects": [], "style": "abstract"}
            
        bitnet_resp = requests.post(BITNET_URL, json=prompt_payload)
        
        if bitnet_resp.status_code == 200:
            full_text = bitnet_resp.json().get('generated_description', '')
            # FIX: Cut off text at the last complete sentence to avoid rambling
            if "." in full_text:
                description = full_text.rsplit('.', 1)[0] + "."
            else:
                description = full_text
        else:
            description = "Could not generate description."

        print(f" -> BitNet generated: {description[:50]}...")

        # 3. Update Firebase
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
        # Try to mark as failed if possible
        try:
            db.collection('art_requests').document(request_id).update({
                "status": "failed",
                "error": str(e)
            })
        except:
            pass

    # Acknowledge message so RabbitMQ removes it from queue
    ch.basic_ack(delivery_tag=method.delivery_tag)


# --- 3. RabbitMQ Connection ---
def main():
    print("Worker starting... connecting to RabbitMQ...")
    # Add a retry loop because RabbitMQ might take a few seconds to start
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
            channel = connection.channel()
            channel.queue_declare(queue='task_queue', durable=True)
            
            # Use prefetch to handle 1 message at a time
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='task_queue', on_message_callback=process_task)

            print(' [*] Waiting for messages. To exit press CTRL+C')
            channel.start_consuming()
            break
        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ not ready yet, retrying in 5 seconds...")
            time.sleep(5)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
