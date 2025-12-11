import sys
from deepsymbol.vision import detect_objects
from deepsymbol.llm import generate_text


def build_prompt_from_objects(objects: list[str]) -> str:
    """
    Build a natural language prompt for the LLM based on detected objects.
    """
    if not objects:
        return (
            "You are an AI oracle that interprets psychological symbols.\n"
            "No clear objects were detected in the image. "
            "Explain what this might symbolise psychologically in a dream.\n"
            "Answer in 1–2 short paragraphs and do not repeat the prompt."
        )

    objects_str = ", ".join(objects)

    prompt = (
        "You are an AI oracle that interprets psychological symbols.\n"
        f"In an image, I detected the following objects: {objects_str}.\n"
        "Interpret what these objects might symbolise psychologically, "
        "as if they appeared in a dream or as visual motifs.\n"
        "Answer in 1–2 short paragraphs. Do not repeat the prompt text."
    )
    return prompt


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_deepsymbol_example.py <image_path>")
        raise SystemExit(1)

    image_path = sys.argv[1]

    # 1) YOLO: detect objects in the image
    detection = detect_objects(image_path)
    objects = detection["objects"]

    print("=== YOLO DETECTION ===")
    print("Objects:", objects)
    print("Confidences:", detection["confidences"])
    print("Total:", detection["num_objects"])

    # 2) Build a prompt for the LLM
    prompt = build_prompt_from_objects(objects)

    # 3) Ask the LLM (TinyLlama) to interpret the objects as symbols
    print("\n=== LLM INTERPRETATION ===")
    result = generate_text(prompt, max_new_tokens=200)
    print(result["output_text"])


if __name__ == "__main__":
    main()

