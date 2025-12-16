import os
import httpx


def bitnet_chat_completion(prompt: str) -> str:
    """
    Call BitNet service (OpenAI-compatible /v1/chat/completions) and return text.
    """
    base_url = os.getenv("BITNET_BASE_URL", "http://localhost:8080").rstrip("/")
    url = f"{base_url}/v1/chat/completions"

    payload = {
        "model": "bitnet",
        "messages": [
            {
            "role": "system", 
            "content": (
            "You interpret psychological symbols.\n"
            "Rules:\n"
            "- Do NOT repeat the prompt\n"
            "- Do NOT add headings or explanations about the task\n"
            "- Output ONLY the interpretation text\n"
            "- Keep it concise (3–5 sentences)\n"
            ),
            },
            
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.6,
    }

    # Some LLM calls can take time on CPU, so keep timeout generous
    with httpx.Client(timeout=None) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()

    # OpenAI-style response format:
    # choices[0].message.content
    return data["choices"][0]["message"]["content"]

