#!/usr/bin/env python3
"""
BookMyShowBot — Test Project for RAGLens Observability & Evaluation.

This test project simulates a customer service AI bot for BookMyShow.
It runs queries through a complete RAG pipeline instrumented with the
RAGLens Python SDK to demonstrate how RAGLens evaluates RAG pipelines in real-time.

Usage:
    # Run all 6 evaluation scenarios (healthy, low confidence, waste, overflow, slow, error)
    python examples/bookmyshow-bot/app.py

    # Run a specific scenario
    python examples/bookmyshow-bot/app.py --scenario healthy
    python examples/bookmyshow-bot/app.py --scenario low-confidence
    python examples/bookmyshow-bot/app.py --scenario waste
    python examples/bookmyshow-bot/app.py --scenario context-overflow
    python examples/bookmyshow-bot/app.py --scenario slow-generation
    python examples/bookmyshow-bot/app.py --scenario error

    # Ask a custom question
    python examples/bookmyshow-bot/app.py --query "What are the showtimes for Oppenheimer in Bengaluru?"
"""

import argparse
import os
import sys
from pathlib import Path

# Add sdk-python to sys.path if not installed globally
repo_root = Path(__file__).resolve().parent.parent.parent
sdk_path = repo_root / "packages" / "sdk-python"
if sdk_path.exists() and str(sdk_path) not in sys.path:
    sys.path.insert(0, str(sdk_path))

from raglens import RAGLens
from pipeline import run_rag_pipeline

DEFAULT_PROJECT_ID = "project_aaw3236s8tx5qsr1gi0wefnyj7"
DEFAULT_API_KEY = "rgl_test_bookmyshow_demo_key_123"
DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_WEB_URL = "http://localhost:3000"

SCENARIOS = {
    "healthy": {
        "title": "Scenario 1: Healthy & High-Confidence RAG Query",
        "query": "Can I cancel my movie ticket and get a refund on BookMyShow?",
        "eval_focus": "Evaluates normal pipeline flow. Expect high similarity scores, healthy context utilization, and 0 diagnostic warnings.",
        "expected_diagnostics": "None (Status: SUCCESS)",
    },
    "low-confidence": {
        "title": "Scenario 2: Low Retrieval Confidence (Out-of-Domain Query)",
        "query": "How do I renew my driver's license or apply for an income tax refund?",
        "eval_focus": "Evaluates how RAGLens catches weak retrieval when knowledge base coverage is missing.",
        "expected_diagnostics": "low_retrieval_confidence (Warning: top similarity score < 0.70)",
    },
    "waste": {
        "title": "Scenario 3: Retrieval Waste & Low Context Utilization",
        "query": "Are outside snacks and water bottles allowed into the cinema hall?",
        "eval_focus": "Evaluates chunk selection efficiency when top-k retrieves too many irrelevant chunks.",
        "expected_diagnostics": "retrieval_waste (Info: retrieved/selected > 3.0) & low_context_utilization (Info: < 40% selected)",
    },
    "context-overflow": {
        "title": "Scenario 4: Excessive Context (Context Window Bloat)",
        "query": "List all cinema amenities, IMAX laser specifications, terms of service, and credit card offers.",
        "eval_focus": "Evaluates context window budgeting when oversized chunks risk lost-in-the-middle degradation.",
        "expected_diagnostics": "excessive_context (Warning: context tokens / max_tokens > 80%) & token_heavy_context",
    },
    "slow-generation": {
        "title": "Scenario 5: LLM Generation Bottleneck",
        "query": "Explain in deep technical detail the difference between IMAX with Laser, 4DX motion, and standard 2D projection.",
        "eval_focus": "Evaluates latency distribution when generation dominates over 85% of total pipeline latency.",
        "expected_diagnostics": "slow_generation (Info: LLM duration / total duration > 85%)",
    },
    "error": {
        "title": "Scenario 6: Span Failure & Error Handling",
        "query": "Check live seat inventory for Oppenheimer at PVR Forum Koramangala 09:15 PM show.",
        "eval_focus": "Evaluates pipeline resilience and error tracing when an external cinema partner API fails.",
        "expected_diagnostics": "failed_span (Error: Span threw ConnectionResetError; status: ERROR)",
    },
    "slow-retrieval": {
        "title": "Scenario 7: Slow Vector Retrieval Latency",
        "query": "Find all IMAX 3D showtimes for Oppenheimer in South Bengaluru theaters.",
        "eval_focus": "Evaluates vector index and retrieval infrastructure performance when vector search latency exceeds 500ms.",
        "expected_diagnostics": "slow_retrieval (Warning: retrieval duration_ms > 500ms)",
    },
}


def run_scenario(client: RAGLens, scenario_key: str, scenario_data: dict, project_id: str, web_url: str):
    print("=" * 80)
    print(f"🎬 {scenario_data['title']}")
    print(f"📋 Question:  \"{scenario_data['query']}\"")
    print(f"🔍 Evaluation Focus: {scenario_data['eval_focus']}")
    print(f"🎯 Target RAGLens Diagnostic: {scenario_data['expected_diagnostics']}")
    print("-" * 80)

    try:
        answer, trace = run_rag_pipeline(
            client=client,
            query=scenario_data["query"],
            scenario_type=scenario_key,
            environment="production",
            project_id=project_id,
        )
        print(f"💬 Bot Response:\n   {answer}\n")
    except Exception as exc:
        print(f"⚠️  Exception caught during execution (as expected for error scenario): {type(exc).__name__}: {exc}\n")
        # In error scenario, the trace __exit__ still captures and sends the error trace
        trace = getattr(client, "_last_trace", None)

    trace_url = f"{web_url}/projects/{project_id}/traces/{trace.id}" if (trace and trace.id) else (trace.url if trace else None)
    
    if trace and trace.id:
        print(f"✅ Trace Ingested Successfully!")
        print(f"   Trace ID:  {trace.id}")
        print(f"   Status:    {trace.status.upper()}")
        print(f"   Dashboard: {trace_url}")
    else:
        print(f"ℹ️  Trace completed locally (offline mode or server unreachable).")
    print()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--scenario",
        choices=["healthy", "low-confidence", "waste", "context-overflow", "slow-generation", "slow-retrieval", "error", "all"],
        default="all",
        help="Specific test scenario to execute (default: all)",
    )
    parser.add_argument("--query", help="Run a custom question through the pipeline")
    parser.add_argument("--project-id", default=os.getenv("RAGLENS_PROJECT_ID", DEFAULT_PROJECT_ID), help="RAGLens project ID")
    parser.add_argument("--api-key", default=os.getenv("RAGLENS_API_KEY", DEFAULT_API_KEY), help="RAGLens project API key")
    parser.add_argument("--base-url", default=os.getenv("RAGLENS_BASE_URL", DEFAULT_API_URL), help="RAGLens API URL")
    parser.add_argument("--web-url", default=os.getenv("RAGLENS_WEB_URL", DEFAULT_WEB_URL), help="RAGLens Web URL")
    parser.add_argument("--offline", action="store_true", help="Run offline without sending traces to RAGLens")

    args = parser.parse_args()

    client = RAGLens(
        api_key=args.api_key,
        base_url=args.base_url,
        project_id=args.project_id,
        web_url=args.web_url,
        enabled=False if args.offline else True,
    )

    print("\n" + "=" * 80)
    print("🚀 BookMyShowBot RAGLens Test Project")
    print(f"   Project ID:  {args.project_id}")
    print(f"   API Server:  {args.base_url}")
    print(f"   Web UI:      {args.web_url}")
    print(f"   Traces Page: {args.web_url}/projects/{args.project_id}/traces")
    print("=" * 80 + "\n")

    if args.query:
        custom_data = {
            "title": "Custom Query Execution",
            "query": args.query,
            "eval_focus": "User-supplied query through full RAG pipeline.",
            "expected_diagnostics": "Dynamic based on query similarity.",
        }
        run_scenario(client, "healthy", custom_data, args.project_id, args.web_url)
        return

    scenarios_to_run = (
        ["healthy", "low-confidence", "waste", "context-overflow", "slow-generation", "slow-retrieval", "error"]
        if args.scenario == "all"
        else [args.scenario]
    )

    for key in scenarios_to_run:
        run_scenario(client, key, SCENARIOS[key], args.project_id, args.web_url)

    print("=" * 80)
    print("🎉 All test scenarios finished!")
    print(f"👉 Refresh your browser at: {args.web_url}/projects/{args.project_id}/traces")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
