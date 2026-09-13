# RAGLens Python SDK

Observability and evaluation SDK for RAG (Retrieval-Augmented Generation) pipelines.

- **Documentation & Walkthrough**: [Full Quickstart Guide](https://github.com/saikirankalidindi/RAGLens/blob/main/docs/QUICKSTART.md)
- **Repository**: [github.com/saikirankalidindi/RAGLens](https://github.com/saikirankalidindi/RAGLens)

---

## Installation

Requires Python 3.9+:

```bash
pip install raglens-sdk
```

---

## Quickstart

```python
from raglens import RAGLens, log_generation

# Reads RAGLENS_API_KEY and RAGLENS_BASE_URL from environment
client = RAGLens()

with client.trace("answer", input={"query": "What is RAG?"}) as trace:
    with trace.span("llm", "generate") as span:
        answer = "Retrieval-augmented generation"
        log_generation(
            span,
            answer,
            usage={"input_tokens": 12, "output_tokens": 4},
            model="mock",
        )
    trace.set_output({"answer": answer})
```

---

## Core Concepts

### Traces and Spans
- Spans nest automatically within a trace using context-local state.
- Use `span.span()` to declare an explicit parent.
- Wrap the actual operation inside a span to capture accurate latency metrics.
- After delivery on context exit, `trace.id` contains the server-assigned ID.
- Set `project_id` and optionally `web_url` on the client to automatically populate `trace.url`.

### Logging Helpers
RAGLens provides specialized logging helpers for common RAG steps:
- **`log_retrieval(span, chunks=...)`**: Records retrieved documents. Requires `chunk_id`, `document_id`, `document_name`, `content`, and `score`. `rank` and `retrieval_method` are populated automatically. Set `selected=True` for chunks that are passed into the context window.
- **`log_context(span, chunks=..., max_tokens=...)`**: Records the assembled context window.
- **`log_prompt(span, prompt=...)`**: Logs prompt templates or formatted prompts.
- **`log_generation(span, output=..., usage=..., model=...)`**: Records LLM completion outputs and token usage metrics.

> **Tip**: The helpers accept an existing span context. Matching `trace.log_*` methods are also available to log instantaneous events.

---

## Configuration

You can configure the client via environment variables or constructor arguments (constructor values override environment variables):

| Variable | Default | Description |
| :--- | :--- | :--- |
| `RAGLENS_BASE_URL` | `http://localhost:8000` | Ingestion API URL |
| `RAGLENS_API_KEY` | *(None)* | Your RAGLens API key |
| `RAGLENS_ENABLED` | `true` | Set to `false` to disable delivery in testing/CI |

### Delivery Behavior
- Delivery is synchronous on trace exit.
- HTTP timeout defaults to 2 seconds.
- Serialization and delivery failures produce warnings without crashing or replacing application exceptions. Application errors propagate normally.

---

## Development

```bash
pip install -e '.[dev]'
pytest tests/
```
