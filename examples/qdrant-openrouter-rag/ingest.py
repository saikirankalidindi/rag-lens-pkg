#!/usr/bin/env python3
"""
Ingestion Script: Index documents into Qdrant using OpenRouter embeddings.

Usage:
    python examples/qdrant-openrouter-rag/ingest.py
"""

import json
from pathlib import Path
import sys

# Add project directory to path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from embeddings import get_embedding
from qdrant_store import QdrantStore


def run_ingestion(force: bool = False):
    print("=" * 70)
    print("📥 Starting Real Document Ingestion into Qdrant")
    print("=" * 70)

    # 1. Load documents
    kb_path = current_dir / "data" / "knowledge_base.json"
    if not kb_path.exists():
        raise FileNotFoundError(f"Knowledge base not found at {kb_path}")

    docs = json.loads(kb_path.read_text(encoding="utf-8"))
    print(f"📖 Loaded {len(docs)} documents from {kb_path.name}")

    # 2. Connect to Qdrant
    store = QdrantStore()
    print(f"🔌 Qdrant connection mode: [{store.mode.upper()}] (Collection: '{store.collection_name}')")
    if store.mode == "cloud":
        print(f"   Connected to cluster: {store.url}")
    else:
        print(f"   Using local embedded storage at: {current_dir / 'qdrant_storage'}")

    current_count = store.count()
    if current_count > 0 and not force:
        print(f"ℹ️  Collection already contains {current_count} points.")
        print("   Skipping re-embedding (pass force=True to re-index).")
        return current_count

    # 3. Generate real embeddings via OpenRouter
    print(f"🤖 Generating real vector embeddings via OpenRouter...")
    texts_to_embed = [f"{d['title']}\n{d['content']}" for d in docs]
    embeddings = get_embedding(texts_to_embed)
    print(f"✅ Generated {len(embeddings)} vectors (Dimension: {len(embeddings[0])})")

    # 4. Index into Qdrant
    print(f"🚀 Upserting vectors into Qdrant collection '{store.collection_name}'...")
    total_indexed = store.index_documents(docs, embeddings)
    print(f"🎉 Successfully indexed {total_indexed} points into Qdrant!")
    print("=" * 70)
    return total_indexed


if __name__ == "__main__":
    force_reindex = "--force" in sys.argv
    run_ingestion(force=force_reindex)
