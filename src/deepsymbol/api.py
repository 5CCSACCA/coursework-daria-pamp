from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import shutil
from datetime import datetime
from typing import Any, Dict

from deepsymbol.db import init_db, save_interpretation, get_history
from deepsymbol.vision import detect_objects
from deepsymbol.llm_bitnet import bitnet_chat_completion
from deepsymbol.firebase_store import get_output, list_outputs, update_output, delete_output

# NEW: Firebase store
from deepsymbol.firebase_store import (
    save_output,
    get_output,
    list_outputs,
    update_output,
    delete_output,
)

app = FastAPI(title="DeepSymbol API", description="YOLO + LLM symbolic interpretation")

init_db()


def build_prompt_from_objects(objects: list[str]) -> str:
    if not objects:
        return (
        "No clear objects were detected.\n"
    "Write ONE short paragraph (2-4 sentences).\n"
    "Do not repeat any instruction text.\n"
    "Do not list multiple symbols.\n"
    "Return only the interpretation."
        )

    objects_str = ", ".join(objects)
    return (
        f"Detected objects: {objects_str}.\n"
        "Interpret what these objects might symbolise psychologically (dream symbolism).\n"
        "Answer in 2-4 short sentences.\n"
        "Do NOT repeat the prompt. Do NOT add headings. Just the interpretation."
    )


@app.post("/interpret-image")
async def interpret_image(file: UploadFile = File(...)):
    # Save the uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    # 1) YOLO detection
    detection = detect_objects(tmp_path)
    objects = detection["objects"]

    # 2) Build LLM prompt
    prompt = build_prompt_from_objects(objects)

    try:
        interpretation = bitnet_chat_completion(prompt)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"BitNet unavailable: {str(e)[:200]}")


    # 4) Save locally (SQLite history)
    record_id = save_interpretation(objects, interpretation)

    # 5) NEW: Save to Firebase (Firestore)
    # Use record_id as document id for easy linking between local history and firebase
    save_output(
        str(record_id),
        {
            "objects": objects,
            "interpretation": interpretation,
            "created_at": datetime.utcnow().isoformat() + "Z",
        },
    )

    return JSONResponse(
        {
            "id": record_id,
            "objects": objects,
            "interpretation": interpretation,
        }
    )


@app.get("/history")
def history(limit: int = 20):
    return {"items": get_history(limit=limit)}


# ----------------------------
# NEW: Firebase CRUD endpoints
# ----------------------------

@app.get("/firebase/outputs")
def firebase_outputs(limit: int = 50):
    return {"items": list_outputs(limit=limit)}


@app.get("/firebase/outputs/{item_id}")
def firebase_get(item_id: str):
    item = get_output(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    # include id in response for convenience
    item["id"] = item_id
    return item


@app.put("/firebase/outputs/{item_id}")
def firebase_update(item_id: str, patch: Dict[str, Any]):
    # check exists (so we return 404 if missing)
    existing = get_output(item_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Not found")

    # do update
    update_output(item_id, patch)
    updated = get_output(item_id) or {}
    updated["id"] = item_id
    return updated


@app.delete("/firebase/outputs/{item_id}")
def firebase_delete(item_id: str):
    existing = get_output(item_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Not found")

    delete_output(item_id)
    return {"status": "deleted", "id": item_id}

