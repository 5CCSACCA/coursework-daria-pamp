from pathlib import Path
from typing import List, Dict, Any

from ultralytics import YOLO


_MODEL_PATH = "yolo11n.pt"
_yolo_model: YOLO | None = None


def get_yolo_model() -> YOLO:
    """
    Lazily load YOLO model (only once).
    """
    global _yolo_model
    if _yolo_model is None:
        _yolo_model = YOLO(_MODEL_PATH)
    return _yolo_model


def detect_objects(image_path: str) -> Dict[str, Any]:
    """
    Run object detection on an image and return detected objects.
    """
    img_path = Path(image_path)
    if not img_path.exists():
        raise FileNotFoundError(f"Image not found: {img_path}")

    model = get_yolo_model()

    results = model(str(img_path), device="cpu")
    r = results[0]

    class_ids = r.boxes.cls.tolist() if r.boxes is not None else []
    scores = r.boxes.conf.tolist() if r.boxes is not None else []

    names: List[str] = []
    for cls_id in class_ids:
        names.append(r.names[int(cls_id)])

    return {
        "objects": names,
        "confidences": scores,
        "num_objects": len(names),
    }

