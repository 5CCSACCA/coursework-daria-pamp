from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BitNetService")

app = FastAPI(title="Text Generation Service (LLM)")

# Global model variable
generator = None

class TextRequest(BaseModel):
    detected_objects: list[str]
    style: str = "creative"

@app.on_event("startup")
def load_model():
    global generator
    logger.info("Loading LLM model...")
    try:
        # We use GPT-2 as a proxy for BitNet constraints
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

    # --- IMPROVED PROMPT LOGIC ---
    if request.detected_objects:
        # If objects found (e.g., cat, sun)
        objects_list = ", ".join(request.detected_objects)
        prompt = f"I saw a painting with {objects_list}. It made me feel"
    else:
        # If NO objects found (Abstract art or Portrait like Mona Lisa)
        prompt = "I saw a mysterious and beautiful masterpiece painting. It made me feel"
    
    try:
        result = generator(
            prompt, 
            max_length=100, # Let it write a bit more
            num_return_sequences=1,
            truncation=True,
            pad_token_id=50256,
            temperature=0.8 # More creativity
        )
        
        # Clean up the output to remove the prompt itself
        full_text = result[0]['generated_text']
        # We try to keep only the new part or return the whole thing
        return {
            "input_objects": request.detected_objects,
            "generated_description": full_text
        }
    except Exception as e:
        return {"error": str(e)}
