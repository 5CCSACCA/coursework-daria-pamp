from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import tempfile
import shutil

from deepsymbol.vision import detect_objects
from deepsymbol.llm import generate_text

app = FastAPI(title="DeepSymbol API", description="YOLO + LLM symbolic interpretation")


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

    # 3) LLM interpretation
    llm_output = generate_text(prompt, max_new_tokens=200)

    return JSONResponse(
        {
            "objects": objects,
            "interpretation": llm_output["output_text"],
        }
    )

