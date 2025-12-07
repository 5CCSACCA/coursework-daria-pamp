from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import requests
import io

# --- 1. Database Setup (SQLite) ---
# We use SQLite for Stage 4 persistence requirement. It's a file-based DB.
DATABASE_URL = "sqlite:///./artify.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define our Database Table
class ArtRequest(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    detected_objects = Column(String) # Stored as comma-separated string
    art_description = Column(Text)

# Create the table
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 2. API Setup ---
app = FastAPI(title="ArtiFy Gateway API")

# URLs of our other internal services (container names from docker-compose)
YOLO_SERVICE_URL = "http://yolo-service:8000/detect"
BITNET_SERVICE_URL = "http://bitnet-service:8001/generate"

@app.get("/")
def root():
    return {"status": "Gateway is online", "db": "SQLite"}

@app.post("/process-art")
async def process_art(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Main Orchestrator:
    1. Sends image to YOLO -> gets objects
    2. Sends objects to BitNet -> gets text
    3. Saves everything to DB
    4. Returns final result
    """
    # Read file once
    file_content = await file.read()
    
    # Step 1: Call YOLO Service
    try:
        # We need to send the file as multipart/form-data
        files = {'file': (file.filename, file_content, file.content_type)}
        yolo_response = requests.post(YOLO_SERVICE_URL, files=files)
        yolo_data = yolo_response.json()
        
        # Extract objects (e.g., ["cat", "dog"])
        detections = [d['object'] for d in yolo_data.get('detections', [])]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"YOLO Service failed: {e}")

    # Step 2: Call BitNet Service
    try:
        # Prepare data for BitNet
        payload = {
            "detected_objects": detections,
            "style": "poetic"
        }
        bitnet_response = requests.post(BITNET_SERVICE_URL, json=payload)
        bitnet_data = bitnet_response.json()
        
        description = bitnet_data.get('generated_description', "No description generated.")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BitNet Service failed: {e}")

    # Step 3: Save to Database
    db_record = ArtRequest(
        filename=file.filename,
        detected_objects=",".join(detections),
        art_description=description
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    # Step 4: Return Result
    return {
        "id": db_record.id,
        "filename": db_record.filename,
        "objects": detections,
        "interpretation": description
    }

@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    """
    Stage 4 Requirement: Endpoint to retrieve past interactions.
    """
    return db.query(ArtRequest).all()
