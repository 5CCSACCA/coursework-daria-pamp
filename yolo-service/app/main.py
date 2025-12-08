from fastapi import FastAPI, UploadFile, File, HTTPException
from ultralytics import YOLO
from PIL import Image
import io

app = FastAPI(
    title="YOLO Vision Service",
    description="Detects objects using YOLOv8n (Cloud-friendly)"
)

# Load Model at Startup
@app.on_event("startup")
def load_model():
    global model
    print("Loading YOLOv8n model...")
    model = YOLO("yolov8n.pt")
    print("YOLO model loaded successfully!")


# Health Endpoint (Stage 9)
@app.get("/health")
def health():
    return {"status": "ok"}


# Default Status Route
@app.get("/")
def home():
    return {"status": "YOLO service online", "model": "YOLOv8n"}


# Detect Route
@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    """
    Receives an image and returns a clean list of objects detected by YOLO.
    Matches the format expected by worker-service.
    """
    print(f"Received file: {file.filename}")

    try:
        # Read, convert
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # YOLO Prediction
        results = model(image)

        detections = []

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = result.names[class_id]

                detections.append({
                    "object": class_name
                })

        print(f"YOLO found {len(detections)} objects.")

        return {"detections": detections}

    except Exception as e:
        print(f"YOLO Error: {e}")
        raise HTTPException(status_code=500, detail=f"YOLO processing error: {e}")
