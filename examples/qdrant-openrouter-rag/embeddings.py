"""
Embeddings Client using OpenRouter API.

Calls OpenRouter's embeddings endpoint to generate real dense vector embeddings
(e.g. text-embedding-3-small, 1536 dimensions).
"""

import os
import time
from typing import List, Union
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
DEFAULT_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


def get_embedding(
    text_or_texts: Union[str, List[str]],
    model: str = DEFAULT_EMBEDDING_MODEL,
    api_key: str = None,
) -> Union[List[float], List[List[float]]]:
    """
    Generate dense vector embedding(s) using OpenRouter.
    
    Args:
        text_or_texts: A single text string or list of text strings.
        model: Embedding model name (default: text-embedding-3-small).
        api_key: Optional API key; defaults to OPENROUTER_API_KEY env var.
    
    Returns:
        A list of floats for a single string, or a list of float lists for batch inputs.
    """
    key = api_key or os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise ValueError(
            "OPENROUTER_API_KEY is not set. Please add it to your .env file or environment."
        )

    is_single = isinstance(text_or_texts, str)
    inputs = [text_or_texts] if is_single else text_or_texts

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/raglens/raglens",
        "X-Title": "RAGLens Qdrant Demo",
    }
    payload = {
        "model": model,
        "input": inputs,
    }

    t0 = time.perf_counter()
    response = requests.post(
        f"{OPENROUTER_API_URL}/embeddings",
        headers=headers,
        json=payload,
        timeout=30,
    )
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    if response.status_code != 200:
        raise RuntimeError(
            f"OpenRouter Embeddings API error [{response.status_code}]: {response.text}"
        )

    data = response.json()
    embeddings = [item["embedding"] for item in data["data"]]
    
    return embeddings[0] if is_single else embeddings
