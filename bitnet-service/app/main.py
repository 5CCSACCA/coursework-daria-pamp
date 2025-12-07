from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BitNetService")

app = FastAPI(title="Text Generation Service (LLM)")

generator = None

class TextRequest(BaseModel):
    detected_objects: list[str]
    style: str = "creative"

@app.on_event("startup")
def load_model():
    global generator
    logger.info("Loading LLM model...")
    try:
        # GPT-2 Small is a proxy for BitNet
        generator = pipeline("text-generation", model="gpt2")
        logger.info("Model loaded successfully!")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")

@app.get("/")
def status_check():
    return {"status": "LLM Service is running", "model": "gpt2"}

@app.post("/generate")
def generate_text(request: TextRequest):
    if not generator:
        raise HTTPException(status_code=503, detail="Model is loading")

    # --- 1. Smart Prompt Logic ---
    # Check if we actually have objects
    if request.detected_objects and len(request.detected_objects) > 0:
        # Clean up list (remove duplicates)
        unique_objects = list(set(request.detected_objects))
        objects_str = ", ".join(unique_objects)
        prompt = f"I saw a painting containing {objects_str}. It makes me feel"
    else:
        # Fallback for empty detections (Mona Lisa, Abstract, or failed detection)
        prompt = "I saw a mysterious and beautiful masterpiece painting. It makes me feel"
    
    logger.info(f"Generating for prompt: {prompt}")

    try:
        # --- 2. Generation with Anti-Repetition ---
        result = generator(
            prompt, 
            max_length=80, 
            num_return_sequences=1,
            truncation=True,
            pad_token_id=50256,
            temperature=0.8,         # Creativity
            no_repeat_ngram_size=2,  # FIX: Stops "in a different place" loops
            repetition_penalty=1.2   # FIX: Penalizes repeating words
        )
        
        full_text = result[0]['generated_text']
        
        # Simple cleanup to stop at the last dot
        if "." in full_text:
            cleaned_text = full_text.rsplit('.', 1)[0] + "."
        else:
            cleaned_text = full_text

        return {
            "input_objects": request.detected_objects,
            "generated_description": cleaned_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



