"""Offline vector retrieval and extractive mock generation, instrumented with RAGLens."""
import argparse
from collections import Counter
import json
import math
import os
from pathlib import Path
import re

from raglens import RAGLens, log_context, log_generation, log_prompt, log_retrieval


STOP_WORDS = {"the", "a", "an", "of", "and", "is", "are", "in", "to", "what", "how", "do", "does"}


def terms(text):
    return [word for word in re.findall(r"[a-z]+", text.lower()) if word not in STOP_WORDS]


def retrieve(query, documents, top_k=4):
    # A local TF-IDF embedding keeps the default demo free of model downloads.
    counts = [Counter(terms(doc["text"])) for doc in documents]
    vocab = set().union(*counts)
    idf = {word: math.log((len(counts) + 1) / (1 + sum(word in c for c in counts))) + 1 for word in vocab}
    def embed(text):
        count = Counter(terms(text))
        vector = {word: count[word] * idf[word] for word in vocab}
        norm = math.sqrt(sum(value * value for value in vector.values())) or 1
        return {word: value / norm for word, value in vector.items()}
    q = embed(query)
    ranked = sorted(((sum(q[word] * value for word, value in embed(doc["text"]).items()), doc)
                     for doc in documents), key=lambda item: item[0], reverse=True)[:top_k]
    return [{"rank": i, "chunk_id": doc["id"] + "-1", "document_id": doc["id"],
             "document_name": doc["title"], "content": doc["text"], "score": score,
             "selected": score > 0.1} for i, (score, doc) in enumerate(ranked, 1)]


def answer(client, query):
    documents = json.loads(Path(__file__).with_name("documents.json").read_text())
    with client.trace("basic-rag", input={"query": query}, metadata={"environment": "demo"}) as trace:
        with trace.span("query", "answer question"):
            with trace.span("retrieval", "local TF-IDF search") as span:
                results = retrieve(query, documents)
                log_retrieval(span, results, method="tfidf_cosine", query=query)
            with trace.span("context", "assemble context") as span:
                selected = [r for r in results if r["selected"]]
                context = "\n\n".join(r["content"] for r in selected)
                log_context(span, context, len(context.split()), max_tokens=512,
                            chunks=[{"content": r["content"], "source": r["document_name"]} for r in selected])
            with trace.span("prompt", "build prompt") as span:
                prompt = f"Answer using only the context.\nContext: {context}\nQuestion: {query}"
                log_prompt(span, prompt, len(prompt.split()))
            with trace.span("llm", "extractive mock generation") as span:
                response = " ".join(r["content"] for r in selected) or "No relevant documents found."
                log_generation(span, response, {"input_tokens": len(prompt.split()),
                               "output_tokens": len(response.split())}, model="extractive-mock")
            trace.set_output({"answer": response})
    return response, trace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", help="Run a custom question instead of the three scenarios")
    parser.add_argument("--offline", action="store_true", help="Run without sending traces")
    parser.add_argument("--project-id", default=os.getenv("RAGLENS_PROJECT_ID"))
    args = parser.parse_args()
    client = RAGLens(enabled=False if args.offline else None, project_id=args.project_id,
                     web_url=os.getenv("RAGLENS_WEB_URL", "http://localhost:3000"))
    questions = [args.question] if args.question else ["How do solar panels produce electricity?",
                 "Explain quantum entanglement", "What renewable energy sources produce electricity?"]
    for question in questions:
        response, trace = answer(client, question)
        print(f"\nQuestion: {question}\nAnswer: {response}")
        print(f"Trace: {trace.url or trace.id or 'not sent (offline or ingestion unavailable)'}")


if __name__ == "__main__":
    main()
