from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import firebase_admin
from firebase_admin import credentials, firestore, auth
import pika
import json
import base64
import os

# --- Setup Firebase ---
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

app = FastAPI(title="ArtiFy Async Gateway (Secured)")

# --- SECURITY (CORS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MONITORING ---
Instrumentator().instrument(app).expose(app)

# --- AUTHENTICATION LOGIC (STAGE 7) ---
security = HTTPBearer()

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates the Firebase Token sent in the Authorization header.
    Format: 'Authorization: Bearer <token>'
    """
    token = creds.credentials
    try:
        # Verify the token with Firebase Admin
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        return uid
    except Exception as e:
        print(f"Auth Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# --- ENDPOINTS ---

@app.post("/process-art")
async def process_art(
    file: UploadFile = File(...), 
    user_id: str = Depends(get_current_user) # <--- THIS PROTECTS THE ENDPOINT
):
    """
    Secured Endpoint. Only works if a valid Firebase Token is provided.
    """
    print(f"User {user_id} requested processing.")

    # 1. Create DB entry (with User ID!)
    doc_ref = db.collection('art_requests').document()
    doc_ref.set({
        "user_id": user_id, # We now know WHO sent the request
        "filename": file.filename,
        "status": "pending",
        "timestamp": firestore.SERVER_TIMESTAMP
    })
    request_id = doc_ref.id

    # 2. RabbitMQ
    file_content = await file.read()
    image_b64 = base64.b64encode(file_content).decode('utf-8')
    message = {"id": request_id, "filename": file.filename, "image_b64": image_b64}

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

    return {"id": request_id, "status": "queued", "message": "Authenticated & Processing."}

@app.get("/history")
def get_history(user_id: str = Depends(get_current_user)): # <--- PROTECTED TOO
    """
    Returns history ONLY for the logged-in user.
    """
    # Filter query by user_id
    docs = db.collection('art_requests').where("user_id", "==", user_id).stream()
    return [{"id": d.id, **d.to_dict(), "timestamp": str(d.to_dict().get("timestamp"))} for d in docs]
