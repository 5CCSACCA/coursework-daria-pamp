from fastapi import FastAPI, UploadFile, File, HTTPException
import firebase_admin
from firebase_admin import credentials, firestore
import requests
import os
import shutil

#Firebase Setup
if not os.path.exists("../serviceAccountKey.json") and not os.path.exists("serviceAccountKey.json"):
    print("WARNING: serviceAccountKey.json not found! Firebase will fail.")

# Initialize Firebase App
# We check if it's already initialized to avoid errors during "hot reload"
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

#API Setup
app = FastAPI(title="ArtiFy Gateway API (Firebase)")

# URLs of internal services
YOLO_SERVICE_URL = "http://yolo-service:8000/detect"
BITNET_SERVICE_URL = "http://bitnet-service:8001/generate"

@app.get("/")
def root():
    return {"status": "Gateway is online", "db": "Firebase Firestore"}

@app.post("/process-art")
async def process_art(file: UploadFile = File(...)):
    """
    1. Sends image to YOLO.
    2. Sends objects to BitNet.
    3. Saves result to Firestore (Cloud).
    """
    # Read file content once
    file_content = await file.read()
    
    # YOLO
    try:
        files = {'file': (file.filename, file_content, file.content_type)}
        yolo_res = requests.post(YOLO_SERVICE_URL, files=files)
        yolo_data = yolo_res.json()
        detections = [d['object'] for d in yolo_data.get('detections', [])]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"YOLO failed: {e}")

    # BitNet
    try:
        payload = {"detected_objects": detections, "style": "poetic"}
        bitnet_res = requests.post(BITNET_SERVICE_URL, json=payload)
        bitnet_data = bitnet_res.json()
        description = bitnet_data.get('generated_description', "No text")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BitNet failed: {e}")

    # Firebase Save
    # Create a new document in collection 'art_requests'
    doc_ref = db.collection('art_requests').document()
    doc_data = {
        "filename": file.filename,
        "objects": detections,
        "interpretation": description,
        "timestamp": firestore.SERVER_TIMESTAMP
    }
    doc_ref.set(doc_data)

    return {
        "id": doc_ref.id,
        "status": "Saved to Cloud",
        "filename": file.filename,
        "objects": detections,
        "interpretation": description
    }

@app.get("/history")
def get_history():
    """
    Fetch all past requests from Firebase Cloud.
    """
    docs = db.collection('art_requests').stream()
    history = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        # Convert timestamp to string if present
        if 'timestamp' in data:
            data['timestamp'] = str(data['timestamp'])
        history.append(data)
    return history

