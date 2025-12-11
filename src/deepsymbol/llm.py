from typing import Dict, Any

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Chat-oriented, compact LLM (1.1B parameters).
# Much smarter than distilgpt2 but still CPU-friendly.
MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

_tokenizer: AutoTokenizer | None = None
_model: AutoModelForCausalLM | None = None


def get_llm() -> tuple[AutoTokenizer, AutoModelForCausalLM]:
    """
    Lazily load TinyLlama chat model on CPU.
    """
    global _tokenizer, _model

    if _tokenizer is None or _model is None:
        device = torch.device("cpu")

        _tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

        _model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float32,  # bf16 на CPU может глючить, поэтому float32
        )
        _model.to(device)
        _model.eval()

    return _tokenizer, _model


def generate_text(prompt: str, max_new_tokens: int = 128) -> Dict[str, Any]:
    """
    Generate a response from TinyLlama given a natural language prompt.
    """
    tokenizer, model = get_llm()
    device = next(model.parameters()).device

    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            top_p=0.9,
            temperature=0.7,
        )

    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return {
        "prompt": prompt,
        "output_text": generated,
    }

