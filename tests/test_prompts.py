from deepsymbol.prompts import build_prompt_from_objects

def test_prompt_no_objects():
    p = build_prompt_from_objects([])
    assert "No clear objects were detected" in p
    assert "Return only the interpretation" in p

def test_prompt_with_objects():
    p = build_prompt_from_objects(["cat", "tree"])
    assert "Detected objects: cat, tree" in p
    assert "2-4 short sentences" in p
