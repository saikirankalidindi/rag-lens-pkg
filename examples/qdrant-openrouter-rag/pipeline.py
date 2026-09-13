"""
RAG Pipeline: Qdrant Vector Search + OpenRouter LLM + RAGLens Tracing.

Full end-to-end real RAG execution:
  1. Dense vector embedding generation via OpenRouter
  2. Nearest-neighbor vector retrieval via Qdrant Cloud / Local
  3. Context window budgeting and formatting
  4. Role-based chat prompt rendering
  5. Real LLM generation via OpenRouter
  6. Granular span observability and automated evaluation via RAGLens
"""

import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

current_dir = Path(__file__).resolve().parent
repo_root = current_dir.parent.parent
sdk_path = repo_root / "packages" / "sdk-python"
if sdk_path.exists() and str(sdk_path) not in sys.path:
    sys.path.insert(0, str(sdk_path))

load_dotenv(current_dir / ".env")

from embeddings import get_embedding
from llm import generate_completion
from qdrant_store import QdrantStore
from raglens import RAGLens, log_context, log_generation, log_prompt, log_retrieval


class RAGPipeline:
    def __init__(
        self,
        raglens_client: Optional[RAGLens] = None,
        qdrant_store: Optional[QdrantStore] = None,
    ):
        self.raglens = raglens_client or RAGLens(
            api_key=os.getenv("RAGLENS_API_KEY", "rgl_test_bookmyshow_demo_key_123"),
            base_url=os.getenv("RAGLENS_BASE_URL", "http://localhost:8000"),
            project_id=os.getenv("RAGLENS_PROJECT_ID", "project_aaw3236s8tx5qsr1gi0wefnyj7"),
            web_url=os.getenv("RAGLENS_WEB_URL", "http://localhost:3000"),
            enabled=os.getenv("RAGLENS_ENABLED", "true").lower() not in {"false", "0", "no"},
        )
        self.store = qdrant_store or QdrantStore()

    def ensure_indexed(self):
        """Auto-index knowledge base if Qdrant collection is empty."""
        if self.store.count() == 0:
            from ingest import run_ingestion
            run_ingestion()

    def run(
        self,
        query: str,
        top_k: int = 4,
        confidence_threshold: float = 0.40,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Any, List[Dict[str, Any]]]:
        """
        Execute RAG query and record full trace into RAGLens.
        
        Returns:
            (generated_answer, raglens_trace, retrieved_chunks)
        """
        self.ensure_indexed()

        meta = {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "qdrant_mode": self.store.mode,
            "qdrant_collection": self.store.collection_name,
            **(metadata or {}),
        }

        with self.raglens.trace(
            name="bookmyshow_rag_qdrant",
            input={"query": query},
            metadata=meta,
        ) as trace:

            # ── 1. Query Analysis Span ──────────────────────────────────────────
            with trace.span(type="query", name="parse_query", input={"query": query}) as span:
                cleaned_query = query.strip()
                span.set_output({"normalized_query": cleaned_query})

            # ── 2. Retrieval Span (Qdrant Vector Search) ───────────────────────
            with trace.span(type="retrieval", name="qdrant_vector_search") as span:
                # Real dense embedding from OpenRouter
                query_vector = get_embedding(cleaned_query)
                # Real vector cosine search in Qdrant
                results = self.store.search(
                    query_vector=query_vector,
                    top_k=top_k,
                )
                for r in results:
                    # Mark chunk as selected if it meets confidence threshold
                    r["selected"] = bool(r["score"] >= confidence_threshold)

                log_retrieval(span, results, method="qdrant_cosine", query=cleaned_query)

            # ── 3. Context Assembly Span ─────────────────────────────────────────
            selected_chunks = [r for r in results if r["selected"]]
            with trace.span(type="context", name="assemble_context") as span:
                if selected_chunks:
                    context_str = "\n\n".join(
                        f"[{r['document_name']}]: {r['content']}" for r in selected_chunks
                    )
                else:
                    context_str = "No relevant context found in knowledge base."

                # Token count estimate for context
                context_tokens = max(10, int(len(context_str.split()) * 1.3))
                max_window = 4096
                log_context(
                    span=span,
                    context=context_str,
                    tokens=context_tokens,
                    max_tokens=max_window,
                    chunks=[{"content": r["content"], "source": r["document_name"]} for r in selected_chunks],
                )

            # ── 4. Prompt Construction Span ─────────────────────────────────────
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are the official BookMyShow customer assistant. Answer the user's question "
                        "accurately and concisely based strictly on the provided context. If the context does not "
                        "contain the answer, state that BookMyShow does not have this information on file."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context_str}\n\nUser Question: {cleaned_query}",
                },
            ]
            prompt_tokens = context_tokens + 50
            with trace.span(type="prompt", name="render_chat_prompt") as span:
                log_prompt(
                    span=span,
                    prompt=messages,
                    tokens=prompt_tokens,
                    template_variables={"query": cleaned_query, "num_sources": len(selected_chunks)},
                )

            # ── 5. LLM Generation Span (OpenRouter) ──────────────────────────────
            with trace.span(type="llm", name="openrouter_chat_completion") as span:
                answer, llm_meta, llm_elapsed_ms = generate_completion(
                    messages=messages,
                    model=os.getenv("CHAT_MODEL", "openai/gpt-4o-mini"),
                    temperature=0.2,
                )
                log_generation(
                    span=span,
                    response=answer,
                    tokens={
                        "input_tokens": llm_meta["input_tokens"],
                        "output_tokens": llm_meta["output_tokens"],
                    },
                    model=llm_meta["model"],
                    provider=llm_meta["provider"],
                    latency_ms=llm_elapsed_ms,
                    estimated_cost=llm_meta["estimated_cost"],
                )

            # ── 6. Response Output & Metrics ───────────────────────────────────
            trace.set_metrics({
                "estimated_cost": llm_meta.get("estimated_cost", 0.0),
                "total_tokens": llm_meta.get("total_tokens", 0),
            })
            trace.set_output({"answer": answer})

        return answer, trace, results
