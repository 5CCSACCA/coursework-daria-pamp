from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BitNetService")

app = FastAPI(title="Text Generation Service (LLM)")

# ---------------------------------------------------
# Load model at startup
# ---------------------------------------------------
generator = None

@app.on_event("startup")
def load_model():
    global generator
    logger.info("Loading GPT-2 model (BitNet proxy)...")
    try:
        generator = pipeline(
            "text-generation",
            model="gpt2"
        )
        logger.info("LLM loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load LLM: {e}")
        raise RuntimeError("LLM could not be loaded.")


# ---------------------------------------------------
# Models
# ---------------------------------------------------
class TextRequest(BaseModel):
    detected_objects: list[str]
    style: str = "creative"


# ---------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def status_check():
    return {"status": "LLM Service is running", "model": "gpt2"}


# ---------------------------------------------------
# MAIN GENERATION ENDPOINT
# ---------------------------------------------------
@app.post("/generate")
def generate_text(request: TextRequest):

    if not generator:
        raise HTTPException(status_code=503, detail="Model is loading")

    # --- Security: Limit input size (Stage 11) ---
    if len(request.detected_objects) > 30:
        raise HTTPException(
            status_code=400,
            detail="Too many detected objects in prompt (max 30)."
        )

    # --- Deduplicate detected objects ---
    unique_objects = list(set(request.detected_objects))

    # ---------------------------------------------------
    # Prompt Construction (Smart Logic)
    # ---------------------------------------------------
    if unique_objects:
        # truncate long words (safety)
        short_objects = [o[:20] for o in unique_objects]
        objects_str = ", ".join(short_objects)
        prompt = f"I saw a painting containing {objects_str}. It makes me feel"
    else:
        prompt = "I saw a mysterious and beautiful masterpiece painting. It makes me feel"

    # ---------------------------------------------------
    # Style modifiers
    # ---------------------------------------------------
    style = request.style.lower()

    style_map = {
        "formal": "Describe the artwork in a formal academic tone. ",
        "poetic": "Write a poetic and emotional reflection. ",
        "simple": "Describe it using simple and clear language. ",
        "creative": "Express the emotion creatively. "
    }

    if style not in style_map:
        style = "creative"

    prompt = style_map[style] + prompt

    logger.info(f"Prompt sent to model: {prompt}")

    # ---------------------------------------------------
    # Model Generation
    # ---------------------------------------------------
    try:
        result = generator(
            prompt,
            max_length=90,
            num_return_sequences=1,
            truncation=True,
            temperature=0.8,
            pad_token_id=50256,
            no_repeat_ngram_size=2,
            repetition_penalty=1.15
        )
        full_text = result[0]["generated_text"]

        # ---------------------------------------------------
        # Cleanup: cut after the last full stop
        # ---------------------------------------------------
        if "." in full_text:
            cleaned = full_text.rsplit(".", 1)[0] + "."
        else:
            cleaned = full_text

        # Remove undesirable content (simple safety)
        cleaned = re.sub(r"(terror|kill|violence|war)", "art", cleaned, flags=re.IGNORECASE)

        return {
            "input_objects": unique_objects,
            "generated_description": cleaned.strip()
        }

    except Exception as e:
        logger.error(f"LLM generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Generation error: {e}")
