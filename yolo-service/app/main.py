from fastapi import FastAPI, UploadFile, File
from ultralytics import YOLO
from PIL import Image
import io

app = FastAPI(
    title="YOLO Vision Service",
    description="This service detects objects in images using YOLOv8n"
)

#load the model globally so I don't load it for every request; I use 'yolov8n.pt' because it is small and fast (good for our requirments)
print("Loading YOLO model...")
model = YOLO('yolov8n.pt')
print("Model loaded successfully!")

@app.get("/")
def home():
    """check to see if the service is running"""
    return {"status": "System is online", "model": "YOLOv8n"}

@app.post("/analyze-image/")
async def analyze_image(file: UploadFile = File(...)):
    """receives an image file; runs YOLO object detection; returns a list of detected objects"""
    print(f"Received file: {file.filename}")

    try:
        image_data = await file.read()
        
        #convert bytes to an image so YOLO can read it
        image = Image.open(io.BytesIO(image_data))

        #run the prediction
        results = model(image)

        #process the results to get a simple JSON list
        detected_objects = []
        
        #only take the first result because we sent one image
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = result.names[class_id]
                confidence = float(box.conf[0])

                detected_objects.append({
                    "object": class_name,
                    "confidence": round(confidence, 2)
                })

        print(f"Found {len(detected_objects)} objects.")
        
        return {
            "filename": file.filename,
            "detected_objects": detected_objects
        }

    except Exception as e:
        #if something wrong, return error
        return {"error": str(e)}
