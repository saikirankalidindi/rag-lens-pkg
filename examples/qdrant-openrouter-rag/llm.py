"""
LLM Chat Client using OpenRouter API.

Calls OpenRouter chat completions endpoint (e.g. openai/gpt-4o-mini)
and extracts generation text, token usage, latency, and cost for RAGLens logging.
"""

import os
import time
from typing import Any, Dict, List, Tuple
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
DEFAULT_CHAT_MODEL = os.getenv("CHAT_MODEL", "openai/gpt-4o-mini")


def generate_completion(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_CHAT_MODEL,
    temperature: float = 0.2,
    max_tokens: int = 512,
    api_key: str = None,
) -> Tuple[str, Dict[str, Any], int]:
    """
    Generate chat completion via OpenRouter.
    
    Returns:
        (content, usage_metadata, elapsed_ms)
    """
    key = api_key or os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise ValueError("OPENROUTER_API_KEY is not set.")

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/raglens/raglens",
        "X-Title": "RAGLens Qdrant Demo",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    t0 = time.perf_counter()
    response = requests.post(
        f"{OPENROUTER_API_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=45,
    )
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    if response.status_code != 200:
        raise RuntimeError(
            f"OpenRouter Chat API error [{response.status_code}]: {response.text}"
        )

    data = response.json()
    choice = data["choices"][0]
    content = choice["message"]["content"]
    usage = data.get("usage", {})
    cost = usage.get("cost", 0.0)

    metadata = {
        "model": model,
        "provider": data.get("provider", "openrouter"),
        "input_tokens": usage.get("prompt_tokens", 0),
        "output_tokens": usage.get("completion_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
        "estimated_cost": cost,
        "finish_reason": choice.get("finish_reason", "stop"),
    }

    return content, metadata, elapsed_ms
