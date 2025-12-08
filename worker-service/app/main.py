import pika
import json
import requests
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import time
import sys
import os


# ---------------------------
# Firebase Initialization
# ---------------------------
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Internal service endpoints
YOLO_URL = "http://yolo-service:8000/detect"
BITNET_URL = "http://bitnet-service:8001/generate"


# ---------------------------
# Utility: safe POST with retries
# ---------------------------
def safe_post(url, **kwargs):
    """
    Makes a POST request with retries.
    Prevents worker from failing if YOLO or BitNet temporarily down.
    """
    for attempt in range(5):
        try:
            resp = requests.post(url, timeout=10, **kwargs)
            return resp
        except Exception as e:
            print(f"[WARN] Failed request to {url}, retrying... ({attempt+1}/5)")
            if attempt == 4:
                raise e
            time.sleep(2)


# ---------------------------
# Task Processing Logic
# ---------------------------
def process_task(ch, method, properties, body):
    print("\n==============================")
    print(" [x] Received new task")
    print("==============================")

    try:
        data = json.loads(body)
        request_id = data["id"]
        filename = data["filename"]
        image_bytes = base64.b64decode(data["image_b64"])

        print(f"Processing file: {filename}  | Request ID: {request_id}")

        # ---------------------------
        # 1. YOLO DETECTION
        # ---------------------------
        files = {"file": (filename, image_bytes)}

        try:
            yolo_resp = safe_post(YOLO_URL, files=files)
            yolo_json = yolo_resp.json() if yolo_resp.status_code == 200 else {}
        except Exception as e:
            print(f"[ERROR] YOLO error: {e}")
            yolo_json = {}

        detections = list({d.get("object") for d in yolo_json.get("detections", [])})
        detections = [d for d in detections if d]  # Remove None

        print(f" -> YOLO found objects: {detections}")

        # ---------------------------
        # 2. BITNET GENERATION
        # ---------------------------
        try:
            prompt_text = (
                "You are The Dream Interpreter — a gentle oracle who explains symbolic visions. "
                f"The following symbols appeared in a dream: {detections}. "
                "Give a short (2–4 sentence) mystical interpretation. "
                "Use soft, poetic, calming language. "
                "Focus on themes of guidance, hope, and inner reflection. "
                "Avoid negativity, violence, fear, or dark themes. "
                "Your answer should feel comforting and meaningful."
            )


            bitnet_resp = safe_post(
                BITNET_URL,
                json={
                    "detected_objects": [prompt_text]
                }
            )

            if bitnet_resp.status_code == 200:
                description = bitnet_resp.json().get("generated_description", "")

            else:
                description = "BitNet returned an error."

        except Exception as e:
            description = f"BitNet error: {e}"


        print(f" -> BitNet generated: {description[:80]}...")

        # ---------------------------
        # 3. UPDATE FIRESTORE
        # ---------------------------
        try:
            db.collection("art_requests").document(request_id).update({
                "status": "completed",
                "objects": detections,
                "interpretation": description,
                "processed_at": firestore.SERVER_TIMESTAMP
            })
            print(f" -> Firebase updated successfully")
        except Exception as e:
            print(f"[ERROR] Firebase update failed: {e}")

    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        try:
            db.collection("art_requests").document(request_id).update({
                "status": "failed",
                "error": str(e)
            })
        except:
            pass

    # Always ACK even if failed (avoids infinite queue block)
    ch.basic_ack(delivery_tag=method.delivery_tag)


# ---------------------------
# Worker → RabbitMQ Connection
# ---------------------------
def main():
    print("Worker starting...")

    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host="rabbitmq")
            )
            channel = connection.channel()
            channel.queue_declare(queue="task_queue", durable=True)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue="task_queue",
                on_message_callback=process_task
            )

            print(" [*] Worker ready. Waiting for tasks...")
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError:
            print("[WARN] RabbitMQ not ready, retrying in 5 seconds...")
            time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Worker stopped manually")
        sys.exit(0)

