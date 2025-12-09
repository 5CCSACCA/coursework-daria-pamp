# DeepSymbol – Cloud-AI Coursework Project

Repository URL: [https://github.com/5CCSACCA/coursework-daria-pamp.git]

This project is my implementation for the 5CCSACCA – Cloud Computing for Artificial Intelligence coursework.
The goal was to design and build a complete cloud-native AI pipeline using containerised microservices, message queues, and asynchronous processing.
My system is called DeepSymbol — an AI oracle that interprets everyday objects as psychological symbols.
The application allows a user to upload an image, automatically detect objects (YOLOv8), generate symbolic meaning using a lightweight language model (BitNet), and store the final interpretation in Firestore.

## Test Firebase User

To allow testing the system end-to-end, a test user is included:
```bash
email: test@gmail.com
password: 123456
```
You can obtain a Firebase ID token with:
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"test@gmail.com","password":"123456","returnSecureToken":true}' \
  "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=YOUR_API_KEY"
```
Insert the returned idToken into the UI and upload any test image.

## 1. System Architecture

The solution is built using six microservices, connected through a message-driven pipeline:
Frontend → Gateway API → RabbitMQ → Worker → YOLO Service
                                            → BitNet Service
                                  ↓
                              Firestore

Components:
Service
Frontend (NGINX) - Minimal web UI for uploading an image and providing a Firebase token.
Gateway API (FastAPI) - Entry point, validates Firebase ID token, performs security checks, stores a request in Firestore, and sends the task to RabbitMQ.
RabbitMQ - Message queue enabling asynchronous processing.
Worker - Listens for tasks, calls YOLO + BitNet, composes final interpretation, writes back to Firestore.
YOLO Service - Object detection using YOLOv8n.
BitNet Service - Lightweight LLM generating symbolic interpretations.

The system is Dockerised and orchestrated using docker-compose.

## 2. How to Run the System

Prerequisites
-Docker & docker-compose
-Firebase project with serviceAccountKey.json
-YOLO model downloads automatically on first run

Start the full system
```bash
docker-compose up -d --build
```
This launches all 6 services and RabbitMQ.

Access the UI
```bash
http://localhost:3000
```

## 3. Authentication (Firebase)
The project uses Firebase Authentication to secure the Gateway API.
The frontend requires the user to paste a Firebase ID token obtained via:
```bash
curl 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=API_KEY' \
  -H 'Content-Type: application/json' \
  --data '{"email":"<email>", "password":"<pw>", "returnSecureToken":true}'
```
The idToken from this response is used in the Authorization: Bearer <token> header.

## 4. Processing Pipeline

When a user uploads an image:
1. Gateway API
-verifies Firebase token
-checks file size & content type
-creates Firestore document (status: "pending")
-sends message {id, filename, base64_image} to RabbitMQ

2. Worker
-receives the message
-calls YOLO service → /detect
-calls BitNet service → /generate
-updates Firestore with: detected objects, symbolic interpretation, status "completed"

3. The user sees the request ID in the frontend and can inspect Firestore for results.

## 5. Performance & Monitoring

The system includes:
-Prometheus monitoring
```bash
Instrumentator().instrument(app).expose(app)
```
-Health checks for each service
```bash
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
```
-Tests
```bash
tests/tests.sh
```

It performs:
health checks
YOLO inference test
BitNet generation test
Gateway pipeline test (returns 401 without token – expected)
small load test

*Note*: Internal services are not exposed publicly, so some tests intentionally return 000. This is acceptable because the services are only accessible inside the Docker network.

## 6. Security Measures

The system implements several required security features:
Firebase token validation in Gateway
Image size limit (5MB)
MIME-type validation (image/*)
Sanitised base64 encoding before sending to RabbitMQ
Isolated Docker network
Asynchronous design prevents blocking / overloading Gateway

These satisfy the coursework requirements for secure design.

## 7.Firestore Data Model
```bash
art_requests/
   <request_id>/
      user_id: string
      filename: string
      status: "pending" | "completed"
      timestamp: server_timestamp
      yolo_objects: [...]
      interpretation: "..."
```

## 8.Known Limitations

YOLO and BitNet are only accessible inside Docker, so direct curl tests from the host will fail (expected behaviour).
First YOLO model download takes ~1–2 seconds.
The frontend is intentionally simple because the focus is backend architecture.

These limitations were discussed in the coursework video.


# Conclusion
The system demonstrates:
container orchestration
asynchronous message-driven architecture
secure authentication
integration of computer vision + language models
cloud-style design patterns
monitoring and testing

DeepSymbol successfully performs symbolic interpretation of real-world images using a distributed, scalable AI pipeline.
