"""
BookMyShow RAG Pipeline with RAGLens Tracing.

Simulates a production movie ticket booking customer support RAG system
with full instrumentation:
  1. Query parsing and expansion (HyDE)
  2. Dense vector retrieval with TF-IDF cosine similarity
  3. Cross-encoder reranking
  4. Context window assembly and token budgeting
  5. Chat prompt construction
  6. LLM answer generation with token & cost tracking
"""

from collections import Counter
import json
import math
from pathlib import Path
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from raglens import RAGLens, log_context, log_generation, log_prompt, log_retrieval

STOP_WORDS = {
    "a", "about", "above", "after", "again", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "can", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it", "its",
    "itself", "me", "more", "most", "my", "myself", "no", "nor", "not", "of", "off",
    "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
    "over", "own", "same", "shan't", "she", "should", "shouldn't", "so", "some",
    "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then",
    "there", "these", "they", "this", "those", "through", "to", "too", "under",
    "until", "up", "very", "was", "wasn't", "we", "were", "weren't", "what", "when",
    "where", "which", "while", "who", "whom", "why", "with", "won't", "would", "you"
}


def tokenize(text: str) -> List[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP_WORDS]


def load_documents() -> List[Dict[str, Any]]:
    path = Path(__file__).with_name("documents.json")
    return json.loads(path.read_text(encoding="utf-8"))


def retrieve_candidates(
    query: str,
    documents: List[Dict[str, Any]],
    top_k: int = 5,
    min_score_threshold: float = 0.20,
) -> List[Dict[str, Any]]:
    """TF-IDF vector retrieval with cosine similarity."""
    corpus_counts = [Counter(tokenize(d["title"] + " " + d["text"])) for d in documents]
    vocab = set().union(*corpus_counts)
    
    # Calculate IDF
    n_docs = len(documents)
    idf = {
        term: math.log((n_docs + 1) / (1 + sum(term in counts for counts in corpus_counts))) + 1.0
        for term in vocab
    }

    def embed(text: str) -> Dict[str, float]:
        counts = Counter(tokenize(text))
        vec = {w: counts[w] * idf[w] for w in counts if w in idf}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {w: v / norm for w, v in vec.items()}

    query_vec = embed(query)

    scored_docs = []
    for doc in documents:
        doc_vec = embed(doc["title"] + " " + doc["text"])
        score = sum(query_vec.get(w, 0.0) * doc_vec[w] for w in doc_vec)
        # Normalize score into a friendly 0.0 - 0.98 range
        normalized_score = round(min(0.98, max(0.05, score * 1.6)), 4)
        scored_docs.append((normalized_score, doc))

    # Sort descending
    scored_docs.sort(key=lambda item: item[0], reverse=True)
    top_candidates = scored_docs[:top_k]

    results = []
    for rank, (score, doc) in enumerate(top_candidates, 1):
        results.append({
            "rank": rank,
            "chunk_id": f"{doc['id']}-c1",
            "document_id": doc["id"],
            "document_name": doc["title"],
            "content": doc["text"],
            "score": score,
            "retrieval_method": "tfidf_cosine",
            "selected": score >= min_score_threshold,
            "metadata": {
                "category": doc.get("category", "general"),
                "source": "bookmyshow_kb_v1",
            }
        })
    return results


def simulate_reranking(
    results: List[Dict[str, Any]],
    query: str,
) -> List[Dict[str, Any]]:
    """
    Simulates a cross-encoder reranker (e.g. cross-encoder/ms-marco-MiniLM-L-6-v2).
    Adjusts ranks and assigns reranker_score to populate the RAGLens Reranking Inspector.
    """
    if not results:
        return results

    # Reorder slightly based on title relevance to simulate cross-encoder boosting
    def reranker_scoring(r):
        doc_title = r["document_name"].lower()
        q = query.lower()
        exact_title_overlap = sum(1 for word in tokenize(q) if word in doc_title)
        boost = 0.08 * exact_title_overlap
        rerank_score = round(min(0.99, r["score"] + boost), 4)
        return rerank_score

    scored = []
    for r in results:
        rr_score = reranker_scoring(r)
        scored.append((rr_score, r))

    # Sort by new reranker score
    scored.sort(key=lambda x: x[0], reverse=True)

    # Assign reranked_rank and reranker_score back into the result dicts
    for new_rank, (new_score, item) in enumerate(scored, 1):
        item["reranked_rank"] = new_rank
        item["reranker_score"] = new_score

    return results


def run_rag_pipeline(
    client: RAGLens,
    query: str,
    scenario_type: str = "healthy",
    environment: str = "production",
    project_id: Optional[str] = None,
) -> Tuple[str, Any]:
    """
    Executes the full RAG pipeline and records structured traces to RAGLens.
    Supports injecting specific conditions for evaluating how RAGLens catches issues.
    """
    documents = load_documents()

    trace_obj = None
    try:
        with client.trace(
            name="bookmyshow_assistant",
            input={"query": query},
            metadata={"environment": environment, "scenario": scenario_type, "channel": "web_chat"},
        ) as trace:
            trace_obj = trace

            # ── Step 1: Query Stage ────────────────────────────────────────────────
            with trace.span(type="query", name="parse_user_query", input={"raw_query": query}) as span:
                normalized_q = " ".join(tokenize(query))
                span.set_output({"normalized_query": normalized_q, "intent": "cinema_inquiry"})

            # ── Step 2: Query Rewrite (HyDE / expansion) ──────────────────────────
            with trace.span(type="query_rewrite", name="hyde_rewrite", input={"query": normalized_q}) as span:
                rewritten_q = f"BookMyShow policy and theater details: {query}"
                span.set_output({"rewritten_query": rewritten_q, "technique": "hyde_expansion"})

            # ── Step 3: Retrieval Stage ────────────────────────────────────────────
            top_k = 10 if scenario_type == "waste" else 5
            min_threshold = 0.70 if scenario_type == "waste" else 0.20

            with trace.span(type="retrieval", name="dense_vector_search") as span:
                # Simulate slow retrieval if configured
                if scenario_type == "slow-retrieval":
                    time.sleep(0.65)  # triggers diag_slow_retrieval_ms (> 500ms)

                results = retrieve_candidates(query, documents, top_k=top_k, min_score_threshold=min_threshold)

                # In healthy scenario: ensure top score is well above 0.70 threshold
                if scenario_type == "healthy" and results:
                    results[0]["score"] = 0.932
                    results[0]["selected"] = True
                    if len(results) > 1:
                        results[1]["score"] = 0.865
                        results[1]["selected"] = True

                # In low-confidence scenario, simulate poor scores (< 0.70)
                if scenario_type == "low-confidence":
                    for r in results:
                        r["score"] = round(min(0.48, r["score"] * 0.35), 4)  # drops score to ~0.25-0.45
                        r["selected"] = False

                # In waste scenario: 10 chunks retrieved, but only 1 selected
                if scenario_type == "waste":
                    for i, r in enumerate(results):
                        r["selected"] = (i == 0)

                log_retrieval(span, results, method="dense_vector_cosine", query=query)

            # ── Step 4: Reranking Stage ────────────────────────────────────────────
            with trace.span(type="reranking", name="cross_encoder_rerank") as span:
                results = simulate_reranking(results, query)
                span.set_attributes({
                    "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
                    "reranked_count": len(results),
                })
                span.set_output({"reranked_top_score": max((r.get("reranker_score", 0.0) for r in results), default=0.0)})

            # ── Step 5: Context Assembly ───────────────────────────────────────────
            selected_results = [r for r in results if r["selected"]]
            if not selected_results and results and scenario_type != "low-confidence":
                selected_results = results[:2]
                for r in selected_results:
                    r["selected"] = True

            with trace.span(type="context", name="assemble_context_window") as span:
                if scenario_type == "context-overflow":
                    # Duplicate and bloat context to trigger excessive_context (>80% of max_tokens)
                    bloated_texts = [r["content"] for r in results] * 12
                    context_str = "\n\n".join(bloated_texts)
                    context_tokens = len(context_str.split()) * 2  # ~1950 tokens
                    max_window = 2048  # 1950 / 2048 = 95% > 80% threshold
                else:
                    context_str = "\n\n".join(f"[{r['document_name']}]: {r['content']}" for r in selected_results)
                    context_tokens = max(30, int(len(context_str.split()) * 1.3))
                    max_window = 4096

                log_context(
                    span=span,
                    context=context_str,
                    tokens=context_tokens,
                    max_tokens=max_window,
                    chunks=[{"content": r["content"], "source": r["document_name"]} for r in selected_results]
                )

            # ── Step 6: Prompt Rendering ──────────────────────────────────────────
            messages = [
                {"role": "system", "content": "You are a helpful BookMyShow customer support agent. Answer questions using only the verified context."},
                {"role": "user", "content": f"Context:\n{context_str}\n\nCustomer Inquiry: {query}"}
            ]
            prompt_tokens = context_tokens + 45
            with trace.span(type="prompt", name="render_chat_prompt") as span:
                log_prompt(
                    span=span,
                    prompt=messages,
                    tokens=prompt_tokens,
                    template_variables={"inquiry": query, "cinema_brand": "BookMyShow"}
                )

            # ── Optional: Error injection scenario ────────────────────────────────
            if scenario_type == "error":
                with trace.span(type="custom", name="cinema_partner_inventory_api") as span:
                    time.sleep(0.1)
                    raise ConnectionResetError("Cinema Partner API (PVR Gateway) timed out after 3000ms")

            # ── Step 7: LLM Generation Stage ──────────────────────────────────────
            with trace.span(type="llm", name="generate_response") as span:
                if scenario_type == "slow-generation":
                    time.sleep(1.2)  # dominates >85% of latency

                if selected_results:
                    answer = "Based on BookMyShow policies: " + selected_results[0]["content"]
                else:
                    answer = "I could not find relevant information in BookMyShow's knowledge base for your inquiry."

                output_tokens = len(answer.split())
                log_generation(
                    span=span,
                    response=answer,
                    tokens={"input_tokens": prompt_tokens, "output_tokens": output_tokens},
                    model="gpt-4o-mini",
                    provider="openai",
                    temperature=0.2,
                    top_p=0.95
                )

            # Calculate metrics
            trace.set_metrics({
                "estimated_cost": round(prompt_tokens * 0.00000015 + output_tokens * 0.0000006, 6),
            })
            trace.set_output({"answer": answer})

        return answer, trace_obj
    except Exception as exc:
        if scenario_type == "error":
            return f"Error handled gracefully: {exc}", trace_obj
        raise
