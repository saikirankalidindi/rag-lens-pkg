#!/usr/bin/env python3
"""
RAGLens + Qdrant + OpenRouter Real RAG Application.

Executes real RAG pipelines with:
  • Real dense vector embeddings (OpenRouter: text-embedding-3-small)
  • Real vector search in Qdrant Cloud (or embedded local fallback)
  • Real chat completions (OpenRouter: openai/gpt-4o-mini)
  • End-to-end trace observability & runtime evaluation in RAGLens

Usage:
    # Run interactive query
    python examples/qdrant-openrouter-rag/app.py --query "Can I cancel my ticket and get a refund?"

    # Run standard evaluation demo
    python examples/qdrant-openrouter-rag/app.py --demo
"""

import argparse
from pathlib import Path
import sys

# Ensure local imports work
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from pipeline import RAGPipeline


DEMO_QUESTIONS = [
    {
        "query": "What is the cancellation policy on BookMyShow and how are refunds processed?",
        "topic": "Cancellation & Refunds",
        "description": "Tests high-confidence retrieval and factual policy extraction.",
    },
    {
        "query": "What are the audio-visual specifications of IMAX with Laser versus 4DX?",
        "topic": "Cinema Formats",
        "description": "Tests multi-topic technical retrieval with detailed context.",
    },
    {
        "query": "How do I renew my passport or register for voter ID?",
        "topic": "Out-of-Domain Query",
        "description": "Tests RAGLens evaluation on low-confidence retrieval (<0.70 threshold).",
    },
]


def run_single_query(pipeline: RAGPipeline, query: str, top_k: int = 4):
    print("=" * 80)
    print(f"❓ User Question: \"{query}\"")
    print(f"🔌 Vector DB:     Qdrant [{pipeline.store.mode.upper()}] (Collection: {pipeline.store.collection_name})")
    print("-" * 80)

    answer, trace, results = pipeline.run(query=query, top_k=top_k)

    print("📚 Retrieved Documents from Qdrant:")
    for r in results:
        status_icon = "✅ SELECTED" if r["selected"] else "⚪ DISCARDED"
        print(f"   [{r['rank']}] Score: {r['score']:.4f} | {status_icon} | {r['document_name']}")

    print("\n🤖 OpenRouter LLM Response:")
    print(f"   {answer.strip()}")

    print("\n📊 RAGLens Observability & Evaluation:")
    if trace and trace.id:
        print(f"   Trace ID:   {trace.id}")
        print(f"   Status:     {trace.status.upper()}")
        print(f"   Tokens:     {trace.metrics.get('total_tokens', 'N/A')}")
        print(f"   Cost ($):   ${trace.metrics.get('estimated_cost', 0.0):.6f}")
        print(f"   Dashboard:  {trace.url or f'{pipeline.raglens.web_url}/projects/{pipeline.raglens.project_id}/traces/{trace.id}'}")
    else:
        print("   Trace sent to RAGLens API.")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--query", help="Ask a custom question to the RAG pipeline")
    parser.add_argument("--top-k", type=int, default=4, help="Number of chunks to retrieve from Qdrant (default: 4)")
    parser.add_argument("--demo", action="store_true", help="Run 3 standard evaluation benchmark queries")
    args = parser.parse_args()

    pipeline = RAGPipeline()

    if args.demo:
        print("\n" + "=" * 80)
        print("🚀 Running Real RAGLens + Qdrant + OpenRouter Benchmark Demo")
        print("=" * 80 + "\n")
        for item in DEMO_QUESTIONS:
            run_single_query(pipeline, item["query"], top_k=args.top_k)
        print("🎉 Benchmark complete! Check all traces in your RAGLens dashboard:")
        print(f"   👉 {pipeline.raglens.web_url}/projects/{pipeline.raglens.project_id}/traces\n")
    elif args.query:
        run_single_query(pipeline, args.query, top_k=args.top_k)
    else:
        # Default: run one clear query and show instructions
        run_single_query(
            pipeline,
            "Can I cancel my movie ticket and get a refund on BookMyShow?",
            top_k=args.top_k,
        )
        print("💡 Hint: Pass --query \"your question\" or --demo to run more queries.\n")


if __name__ == "__main__":
    main()
