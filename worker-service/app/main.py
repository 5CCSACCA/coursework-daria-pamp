import pika
import json
import requests
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import time
import sys

# Firebase initialization
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

YOLO_URL = "http://yolo-service:8000/detect"
BITNET_URL = "http://bitnet-service:8001/generate"


def safe_post(url, **kwargs):
    for attempt in range(5):
        try:
            return requests.post(url, timeout=15, **kwargs)
        except Exception as e:
            print(f"[WARN] Failed POST to {url}, retry {attempt+1}/5")
            if attempt == 4:
                raise e
            time.sleep(2)


def process_task(ch, method, properties, body):
    print("\n==============================")
    print(" [x] Received new task")
    print("==============================")

    try:
        data = json.loads(body)
        request_id = data["id"]
        filename = data["filename"]
        image_bytes = base64.b64decode(data["image_b64"])

        print(f"Processing: {filename} | Request ID: {request_id}")

        files = {"file": (filename, image_bytes)}

        # YOLO detection
        try:
            yolo_resp = safe_post(YOLO_URL, files=files)
            yolo_json = yolo_resp.json() if yolo_resp.status_code == 200 else {}
        except Exception as e:
            print(f"[ERROR] YOLO failure: {e}")
            yolo_json = {}

        detections = list({d.get("object") for d in yolo_json.get("detections", []) if d.get("object")})

        print(f" -> YOLO objects: {detections}")

        # BitNet interpretation
        try:
            symbol = detections[0] if detections else "unknown"
            prompt = (
                f"You are The Dream Interpreter. The symbol is: {symbol}. "
                "Give a poetic mystical interpretation in 2–3 sentences."
            )

            bit_resp = safe_post(BITNET_URL, json={"prompt": prompt})
            interpretation = bit_resp.json().get("generated_description", "") \
                if bit_resp.status_code == 200 else "BitNet error."
        except Exception as e:
            interpretation = f"BitNet error: {e}"

        print(f" -> Interpretation: {interpretation[:80]}...")

        # Firestore update
        db.collection("art_requests").document(request_id).update({
            "status": "completed",
            "objects": detections,
            "interpretation": interpretation,
            "processed_at": firestore.SERVER_TIMESTAMP,
        })

        print(" -> Firestore updated!")

    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        db.collection("art_requests").document(request_id).update({
            "status": "failed",
            "error": str(e)
        })

    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    print("Worker starting...")

    while True:
        try:
            conn = pika.BlockingConnection(
                pika.ConnectionParameters(host="rabbitmq")
            )
            ch = conn.channel()
            ch.queue_declare(queue="task_queue", durable=True)

            ch.basic_qos(prefetch_count=1)
            ch.basic_consume(queue="task_queue", on_message_callback=process_task)

            print(" [*] Worker ready. Waiting for tasks...")
            ch.start_consuming()

        except pika.exceptions.AMQPConnectionError:
            print("[WARN] RabbitMQ not ready, retrying...")
            time.sleep(5)


if __name__ == "__main__":
    main()
