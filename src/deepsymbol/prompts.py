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
