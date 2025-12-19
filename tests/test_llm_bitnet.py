from deepsymbol.llm_bitnet import _clean_llm_text

def test_clean_llm_text_removes_prompt_echo_and_answer():
    prompt = "Detected objects: dog. Interpret in 2-4 sentences."
    raw = (
        "Detected objects: dog. Interpret in 2-4 sentences.\n\n"
        "Answer: A dog in a dream often symbolises loyalty and protection. "
        "It may reflect trust in a relationship. Follow-up questions: 1) ... "
        "Solution: blah blah"
    )
    cleaned = _clean_llm_text(raw, prompt)
    assert "Detected objects:" not in cleaned
    assert "Follow-up" not in cleaned
    assert "Solution:" not in cleaned
    assert len(cleaned) > 10


def test_clean_llm_text_limits_sentences():
    prompt = "x"
    raw = "One. Two. Three. Four. Five. Six."
    cleaned = _clean_llm_text(raw, prompt)
    # Should keep at most 4 sentences
    assert cleaned.count(".") <= 4
