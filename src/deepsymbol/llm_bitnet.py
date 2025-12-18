import os
import httpx
import re


def bitnet_chat_completion(prompt: str) -> str:
    base_url = os.getenv("BITNET_BASE_URL", "http://localhost:8080").rstrip("/")
    model = os.getenv("BITNET_MODEL", "ggml-model-i2_s.gguf")
    url = f"{base_url}/v1/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an AI oracle that interprets psychological symbols.\n"
                    "Rules:\n"
                    "- Answer with ONLY the interpretation.\n"
                    "- 2 to 4 sentences.\n"
                    "- Do NOT repeat the prompt.\n"
                    "- Do NOT write headings.\n"
                    "- Do NOT ask follow-up questions.\n"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 120,
    }

    with httpx.Client(timeout=None) as client:
        r = client.post(url, json=payload)

    try:
        data = r.json()
    except Exception:
        raise RuntimeError(f"BitNet returned non-JSON (status={r.status_code}): {r.text[:400]}")

    if r.status_code >= 400:
        raise RuntimeError(f"BitNet HTTP {r.status_code}: {data}")

    if "error" in data:
        raise RuntimeError(f"BitNet error response: {data['error']}")

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"BitNet response missing 'choices': {data}")

    raw = (choices[0].get("message") or {}).get("content", "") or ""
    raw = raw.strip()

    cleaned = _clean_llm_text(raw, prompt)

    # IMPORTANT: never return empty
    if not cleaned.strip():
        # fallback: try raw
        if raw.strip():
            return raw.strip()
        return "The image may symbolise an internal emotional state that is hard to define, suggesting uncertainty or introspection."

    return cleaned


def _clean_llm_text(text: str, prompt: str) -> str:
    t = text.strip()

    # Remove prompt echo at start
    p = (prompt or "").strip()
    if p and t.startswith(p):
        t = t[len(p):].lstrip()

    # Remove common “bad sections”
    for marker in ["Solution:", "Follow-up questions:", "Follow up questions:", "Answer:"]:
        if marker in t:
            # keep text AFTER "Answer:" but BEFORE follow-up sections
            if marker == "Answer:":
                t = t.split("Answer:", 1)[1].strip()
            else:
                t = t.split(marker, 1)[0].strip()

    # Compress whitespace
    t = re.sub(r"\s+", " ", t).strip()

    # Keep 2–4 sentences max (don’t over-cut)
    sentences = re.split(r"(?<=[.!?])\s+", t)
    sentences = [s.strip() for s in sentences if s.strip()]

    t2 = " ".join(sentences[:4]).strip()
    return t2

