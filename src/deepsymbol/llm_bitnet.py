import os
import httpx


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
            {"role": "system", "content": "You are an AI oracle that interprets psychological symbols."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
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

    return data["choices"][0]["message"]["content"]
