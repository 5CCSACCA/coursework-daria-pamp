import os
import subprocess
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

MODEL_PATH = os.getenv("BITNET_MODEL", "/BitNet/model/ggml-model-i2_s.gguf")

class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[dict]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/v1/models")
def models():
    return {
        "object": "list",
        "data": [
            {"id": "ggml-model-i2_s.gguf", "object": "model", "owned_by": "local"}
        ],
    }

@app.post("/v1/chat/completions")
def chat(req: ChatRequest):
    # берём последний user message
    user_text = ""
    for m in req.messages:
        if m.get("role") == "user":
            user_text = m.get("content", "")

    prompt = user_text.strip() if user_text else "Hello"

    # kth8/bitnet image содержит run_inference.py
    # запускаем его как subprocess, чтобы получить текст
    cmd = [
        "python3",
        "/BitNet/run_inference.py",
        "-m",
        MODEL_PATH,
        "-p",
        prompt,
    ]

    completed = subprocess.run(cmd, capture_output=True, text=True, cwd="/BitNet")

    if completed.returncode != 0:
        return {
            "error": {
                "message": completed.stderr[-2000:],
                "type": "bitnet_runtime_error",
            }
        }

    output_text = completed.stdout.strip()

    # OpenAI-compatible shape (упрощённо)
    return {
        "id": "chatcmpl-local-bitnet",
        "object": "chat.completion",
        "choices": [
            {"index": 0, "message": {"role": "assistant", "content": output_text}, "finish_reason": "stop"}
        ],
    }

