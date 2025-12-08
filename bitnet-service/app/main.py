from fastapi import FastAPI
from pydantic import BaseModel
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BitNetService")

app = FastAPI(title="BitNet Dream Interpreter")

class BitNetRequest(BaseModel):
    prompt: str


# ---------------------------------------------------------
#  Simple pseudo-LLM mystical generator (student-friendly🔥)
# ---------------------------------------------------------
TEMPLATES = [
    "In this vision, {symbol} carries a gentle symbolic meaning. It reflects a quiet shift within your inner world.",
    "The presence of {symbol} suggests that you are entering a period of soft transformation and inner understanding.",
    "Symbolically, {symbol} points toward intuition awakening and clarity forming in subtle ways.",
    "Dreams involving {symbol} often indicate that guidance is nearby — calm, patient, and quietly supportive.",
    "This symbol, {symbol}, whispers of balance returning and new emotional harmony emerging.",
    "The dream uses {symbol} as a sign of reflection — a reminder to trust the calm voice within.",
]


def extract_symbol_from_prompt(prompt: str) -> str:
    """Extracts the YOLO object the worker placed in {brackets}."""
    try:
        start = prompt.index("{")
        end = prompt.index("}")
        return prompt[start + 1:end]
    except:
        return "this symbol"


def generate_mystical_text(prompt: str) -> str:
    symbol = extract_symbol_from_prompt(prompt)
    template = random.choice(TEMPLATES)
    return template.format(symbol=symbol)


# ---------------------------------------------------------
#  API Endpoint
# ---------------------------------------------------------
@app.post("/generate")
def generate_text(request: BitNetRequest):
    logger.info(f"BitNet received prompt: {request.prompt}")

    mystical_text = generate_mystical_text(request.prompt)

    return {
        "generated_description": mystical_text
    }

