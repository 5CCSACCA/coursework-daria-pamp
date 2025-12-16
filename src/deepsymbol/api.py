from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import tempfile
import shutil

from deepsymbol.db import init_db, save_interpretation, get_history
from deepsymbol.vision import detect_objects
from deepsymbol.llm_bitnet import bitnet_chat_completion

app = FastAPI(title="DeepSymbol API", description="YOLO + LLM symbolic interpretation")

init_db()


def build_prompt_from_objects(objects: list[str]) -> str:
    if not objects:
        return (
            "You are an AI oracle that interprets psychological symbols.\n"
            "No clear objects were detected. Interpret what this might symbolise in a dream."
        )

    objects_str = ", ".join(objects)
    return (
        "You are an AI oracle that interprets psychological symbols.\n"
        f"I detected: {objects_str}.\n"
        "Interpret what these objects might symbolise psychologically in a short explanation."
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

    interpretation = bitnet_chat_completion(prompt)
    
    record_id = save_interpretation(objects, interpretation)

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

