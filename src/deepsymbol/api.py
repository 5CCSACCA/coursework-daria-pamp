from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import tempfile
import shutil
from datetime import datetime
from typing import Any, Dict

from deepsymbol.db import init_db, save_interpretation, get_history
from deepsymbol.vision import detect_objects
from deepsymbol.llm_bitnet import bitnet_chat_completion
from deepsymbol.firebase_store import get_output, list_outputs, update_output, delete_output
from deepsymbol.queue import publish_postprocess_job
from deepsymbol.auth import require_firebase_user
from deepsymbol.prompts import build_prompt_from_objects

from prometheus_fastapi_instrumentator import Instrumentator

# NEW: Firebase store
from deepsymbol.firebase_store import (
    save_output,
    get_output,
    list_outputs,
    update_output,
    delete_output,
)

app = FastAPI(title="DeepSymbol API", description="YOLO + LLM symbolic interpretation")

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

init_db()


@app.post("/interpret-image")
async def interpret_image(
    file: UploadFile = File(...),
    user=Depends(require_firebase_user),
):
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
    
    publish_postprocess_job(
        {"id": record_id, "objects": objects, "interpretation": interpretation}
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
def firebase_outputs(limit: int = 50, user=Depends(require_firebase_user)):
    return {"items": list_outputs(limit=limit)}


@app.get("/firebase/outputs/{item_id}")
def firebase_get(item_id: str, user=Depends(require_firebase_user)):
    item = get_output(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    # include id in response for convenience
    item["id"] = item_id
    return item


@app.put("/firebase/outputs/{item_id}")
def firebase_update(item_id: str, patch: Dict[str, Any], user=Depends(require_firebase_user)):
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
def firebase_delete(item_id: str, user=Depends(require_firebase_user)):
    existing = get_output(item_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Not found")

    delete_output(item_id)
    return {"status": "deleted", "id": item_id}

@app.get("/health")
def health():
    return {"status": "ok"}

