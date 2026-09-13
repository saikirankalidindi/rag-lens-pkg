# RAGLens quick start

This guide takes you from an empty checkout to a trace you can inspect in the
RAGLens dashboard. It also shows the common instrumentation patterns: nested
pipeline spans, retrieval results, context assembly, prompts, model usage,
failed requests, disabled tracing, and the real Qdrant/OpenRouter example.

## 1. Start RAGLens

From the repository root, copy the environment template and start the API,
database, and dashboard:

```sh
cp .env.example .env
docker compose up --build
```

Open [http://localhost:3000](http://localhost:3000). Create an account, then
create a project. Open **Settings → API Keys**, create a key, and copy the raw
key immediately. It is displayed only once.

Keep these values for the examples below:

```sh
export RAGLENS_API_KEY='rgl_test_replace_with_your_key'
export RAGLENS_PROJECT_ID='project_replace_with_your_project_id'
export RAGLENS_BASE_URL='http://localhost:8000'
export RAGLENS_WEB_URL='http://localhost:3000'
```

The project ID is in the project URL, for example
`http://localhost:3000/projects/project_abc123`.

If you change Python or Node dependencies, rebuild the affected image. A plain
`docker compose up` may reuse an older image:

```sh
docker compose up -d --build api web
```

## 2. Install the SDK

For a checkout of this repository, install the SDK in editable mode:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e packages/sdk-python
```

The package requires Python 3.9 or newer. The SDK uses `httpx`, sends traces
to `POST /v1/traces`, and never replaces an application exception with an SDK
delivery error.

## 3. Smallest useful trace

Save this as `quick_trace.py` and run it from the repository root:

```python
from raglens import RAGLens

raglens = RAGLens(
    api_key="rgl_test_replace_with_your_key",
    base_url="http://localhost:8000",
    project_id="project_replace_with_your_project_id",
)

with raglens.trace(
    name="answer_question",
    input={"query": "What is retrieval augmented generation?"},
) as trace:
    answer = "RAG combines retrieval with generation."
    trace.set_output({"answer": answer})

print("Trace ID:", trace.id)
print("Dashboard:", trace.url)
```

When the context exits, the SDK adds UTC start/end timestamps and duration,
then sends the trace. `trace.id` is the server ID. With `project_id` set,
`trace.url` is a direct dashboard link.

## 4. A complete RAG trace

Use one span for each meaningful pipeline stage. Spans opened inside another
span automatically receive its `parent_span_id`, so the dashboard can render a
waterfall and nested tree.

```python
from raglens import (
    RAGLens,
    log_context,
    log_generation,
    log_prompt,
    log_retrieval,
)

raglens = RAGLens()  # reads RAGLENS_API_KEY and RAGLENS_BASE_URL
question = "How do I cancel an order?"

with raglens.trace(
    name="customer_support_rag",
    input={"query": question},
    session_id="session-42",
    user_id="user-7",
    metadata={"environment": "development", "tenant": "example"},
) as trace:
    with trace.span("query", "normalize_query", input={"query": question}) as span:
        normalized = question.strip()
        span.set_output({"normalized_query": normalized})

    with trace.span("retrieval", "vector_search") as span:
        documents = [
            {
                "chunk_id": "orders-12",
                "document_id": "orders",
                "document_name": "Order policy",
                "content": "Orders can be cancelled within 30 days.",
                "score": 0.91,
                "selected": True,
            },
            {
                "chunk_id": "shipping-4",
                "document_id": "shipping",
                "document_name": "Shipping policy",
                "content": "Shipping estimates are shown at checkout.",
                "score": 0.62,
                "selected": False,
            },
        ]
        log_retrieval(span, documents, method="qdrant_cosine", query=normalized)

    selected = [item for item in documents if item["selected"]]
    context = "\n\n".join(item["content"] for item in selected)
    with trace.span("context", "assemble_context") as span:
        log_context(
            span,
            context=context,
            tokens=12,
            max_tokens=4096,
            chunks=[{"content": item["content"], "source": item["document_name"]} for item in selected],
        )

    messages = [
        {"role": "system", "content": "Answer only from the supplied context."},
        {"role": "user", "content": f"Context: {context}\nQuestion: {normalized}"},
    ]
    with trace.span("prompt", "render_prompt") as span:
        log_prompt(
            span,
            prompt=messages,
            tokens=28,
            template_variables={"query": normalized, "sources": len(selected)},
        )

    with trace.span("llm", "generate_answer") as span:
        answer = "Orders can be cancelled within 30 days."
        log_generation(
            span,
            response=answer,
            tokens={"input_tokens": 28, "output_tokens": 9},
            model="your-provider-model",
            provider="your-provider",
            temperature=0.2,
            finish_reason="stop",
        )

    trace.set_metrics({"estimated_cost": 0.0001})
    trace.set_output({"answer": answer})

print(trace.url)
```

The five spans appear in the trace as query, retrieval, context, prompt, and
LLM stages. Retrieval cards show rank, score, document, content, and selected
status. Context and prompt inspectors show token counts and sources. The LLM
inspector shows model/provider, latency, token usage, and attributes such as
temperature.

## 5. Helper methods without manually opening a span

The trace-level helpers create a short span and return it. Use an explicit span
around a real operation when its duration matters; use these convenience
methods when the data is already available.

```python
with raglens.trace("helper_example") as trace:
    retrieval_span = trace.log_retrieval(
        results=[{
            "chunk_id": "c1", "document_id": "d1", "document_name": "FAQ",
            "content": "The answer is in the FAQ.", "score": 0.88, "selected": True,
        }],
        method="bm25",
        query="Where is the FAQ?",
    )
    context_span = trace.log_context(
        context="The answer is in the FAQ.",
        tokens=7,
        max_tokens=2048,
        chunks=[{"content": "The answer is in the FAQ.", "source": "FAQ"}],
    )
    prompt_span = trace.log_prompt(
        prompt="Answer from context: The answer is in the FAQ.",
        tokens=12,
    )
    llm_span = trace.log_generation(
        response="See the FAQ.",
        tokens={"input_tokens": 12, "output_tokens": 4},
        model="mock-model",
    )
```

`log_retrieval()` fills ranks when they are omitted. Retrieval records should
contain `chunk_id`, `document_id`, `document_name`, `content`, and `score`.
`selected=True` means the chunk was passed to the model.

## 6. Nested spans and failures

Use `span.span()` when an operation belongs to a specific parent. Exceptions
are recorded on the trace/span and then propagate normally, so your application
keeps its usual error handling.

```python
try:
    with raglens.trace("failed_request", input={"query": "example"}) as trace:
        with trace.span("retrieval", "search") as search:
            with search.span("custom", "vector_database_call") as call:
                raise TimeoutError("vector database timed out")
except TimeoutError:
    print("Application handled the timeout")

print(trace.status)             # error
print(trace.spans[-1].status)   # error
```

The diagnostics engine creates a `failed_span` finding for the failed stage.
Other deterministic findings include low retrieval confidence, retrieval waste,
slow retrieval, excessive context, low context utilization, slow generation,
and token-heavy context.

## 7. Configuration and safe shutdown behavior

The SDK reads these environment variables when constructor values are omitted:

| Variable | Default | Purpose |
|---|---|---|
| `RAGLENS_API_KEY` | empty | Project ingestion key |
| `RAGLENS_BASE_URL` | `http://localhost:8000` | RAGLens API URL |
| `RAGLENS_ENABLED` | `true` | Set to `false` to disable delivery |

```python
import os
from raglens import RAGLens

os.environ["RAGLENS_ENABLED"] = "false"
raglens = RAGLens()
with raglens.trace("local_only") as trace:
    trace.set_output({"answer": "This is never sent."})
assert trace.id is None
```

Delivery is synchronous on trace exit with a two-second default timeout and no
automatic retries. Missing keys, network failures, HTTP failures, malformed
responses, and serialization failures produce a warning and return control to
the application. Do not put passwords, API keys, or unnecessary personal data
in trace inputs, context, prompts, or outputs.

## 8. Run the bundled offline demo

The offline demo requires no API keys, model downloads, or GPU:

```sh
python -m pip install -r examples/basic-rag/requirements.txt
python examples/basic-rag/app.py --offline
```

It runs successful, no-match, and multi-document retrieval scenarios. For the
real BookMyShow pipeline with Qdrant and OpenRouter:

```sh
cp examples/qdrant-openrouter-rag/.env.example examples/qdrant-openrouter-rag/.env
# Set OPENROUTER_API_KEY, and optionally QDRANT_URL/QDRANT_API_KEY.
# Set RAGLENS_API_KEY and RAGLENS_PROJECT_ID to the project created above.
python examples/qdrant-openrouter-rag/app.py --demo
```

To use its web chat interface:

```sh
python examples/qdrant-openrouter-rag/chat_server.py --port 8501
```

Open [http://localhost:8501](http://localhost:8501), ask a question, expand the
retrieved chunks, and select **Inspect in RAGLens**. Leave `QDRANT_URL` and
`QDRANT_API_KEY` empty to use the local embedded Qdrant store. OpenRouter keys
are still required for embeddings and chat generation.

## 9. Verify that traces arrived

Open the project in the dashboard and select **Traces**. A trace should show a
success, warning, or error status and its spans. If it does not appear, check
that the API key is active, the base URL is reachable, the key belongs to the
same project, and `RAGLENS_ENABLED` is not `false`.

For local development, run the automated checks from the repository root:

```sh
pytest apps/api/tests packages/sdk-python/tests
cd apps/web && npm run build && npm run lint
```
