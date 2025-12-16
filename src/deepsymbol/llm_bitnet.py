import os
import httpx
import re


def bitnet_chat_completion(prompt: str) -> str:
    """
    Call BitNet service (OpenAI-compatible /v1/chat/completions) and return text.
    """
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
                    "- Do NOT write headings (e.g., 'Solution').\n"
                    "- Do NOT ask follow-up questions.\n"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 90,
    }

    with httpx.Client(timeout=None) as client:
        r = client.post(url, json=payload)

    # BitNet sometimes returns JSON with {"error": ...} (sometimes even with 200),
    # so handle it safely:
    try:
        data = r.json()
    except Exception:
        raise RuntimeError(f"BitNet returned non-JSON response (status={r.status_code}): {r.text[:400]}")

    if r.status_code >= 400:
        # standard HTTP error
        raise RuntimeError(f"BitNet HTTP {r.status_code}: {data}")

    if "error" in data:
        raise RuntimeError(f"BitNet error response: {data['error']}")

    if "choices" not in data or not data["choices"]:
        raise RuntimeError(f"BitNet response missing 'choices': {data}")

    raw = data["choices"][0]["message"]["content"]
    
    # Remove prompt echo if it appears at the start
    t = raw.strip()
    p = prompt.strip()
    if t.startswith(p):
        t = t[len(p):].lstrip()
        
    # Remove common unwanted sections
    for marker in ["Solution:", "Follow-up questions:", "Follow up questions:"]:
        if marker in t:
            t = t.split(marker, 1)[0].strip()
            
    # Hard limit to keep it short
    t = t.strip()
    sentences = [s.strip() for s in t.replace("\n", " ").split(".") if s.strip()]
    t = ". ".join(sentences[:4]).strip()
    if t and not t.endswith("."):
        t += "."
        
    return t



def _clean_llm_text(text: str) -> str:
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    cleaned = []
    for s in sentences:
        s = s.strip()

        # skip instruction echoes
        if s.startswith(("You interpret", "No clear objects", "Write ONE", "Do not", "Return only")):
            continue

        # skip empty
        if not s:
            continue

        cleaned.append(s)

        # limit to 4 sentences max
        if len(cleaned) >= 4:
            break

    result = " ".join(cleaned)

    # fallback if model returned garbage
    if len(result) < 20:
        return "The image may symbolise an internal emotional state that is difficult to clearly define, suggesting uncertainty or introspection."

    return result

