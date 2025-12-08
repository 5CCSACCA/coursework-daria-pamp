from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BitNetService")

app = FastAPI(title="Text Generation Service (BitNet Proxy)")

generator = None

class TextRequest(BaseModel):
    detected_objects: list[str]
    style: str = "creative"

@app.on_event("startup")
def load_model():
    global generator
    logger.info("Loading GPT-2 model (BitNet proxy)...")
    try:
        generator = pipeline(
            "text-generation",
            model="gpt2",
            pad_token_id=50256  # IMPORTANT FIX
        )
        logger.info("LLM loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        traceback.print_exc()

@app.post("/generate")
def generate_text(request: TextRequest):
    if generator is None:
        raise HTTPException(status_code=503, detail="Model is loading")

    # Build prompt
    if request.detected_objects:
        objects = ", ".join(set(request.detected_objects))
        prompt = f"Express the emotion creatively. I saw a painting containing {objects}. It makes me feel"
    else:
        prompt = "Express the emotion creatively. I saw an abstract mysteries painting. It makes me feel"

    logger.info(f"Prompt sent to model: {prompt}")

    try:
        result = generator(
            prompt,
            max_length=80,
            num_return_sequences=1,
            temperature=0.8,
            no_repeat_ngram_size=2,
            repetition_penalty=1.2,
            pad_token_id=50256
        )

        text = result[0]["generated_text"]

        # Cleanup
        if "." in text:
            text = text.rsplit(".", 1)[0] + "."
        text = text.strip()

        return {
            "input_objects": request.detected_objects,
            "generated_description": text
        }

    except Exception as e:
        logger.error("TEXT GENERATION ERROR:")
        logger.error(str(e))
        traceback.print_exc()

        return {
            "input_objects": request.detected_objects,
            "generated_description": "A mysterious and evocative artwork that inspires deep emotion."
        }
