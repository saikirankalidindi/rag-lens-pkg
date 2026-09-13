# RAGLens Python SDK

The full copyable walkthrough is in the repository's
[quick-start guide](../../docs/QUICKSTART.md). It covers every SDK helper and
the real Qdrant/OpenRouter example.

Install from this repository: `pip install -e packages/sdk-python` (Python 3.9+).

```python
from raglens import RAGLens, log_generation

client = RAGLens()  # reads RAGLENS_API_KEY and RAGLENS_BASE_URL
with client.trace("answer", input={"query": "What is RAG?"}) as trace:
    with trace.span("llm", "generate") as span:
        answer = "Retrieval-augmented generation"
        log_generation(span, answer, {"input_tokens": 12, "output_tokens": 4}, model="mock")
    trace.set_output({"answer": answer})
```

Spans nest automatically within a trace using context-local state. Use `span.span()`
for an explicit parent. Helpers `log_retrieval`, `log_context`, `log_prompt`, and
`log_generation` accept an existing span; matching `trace.log_*` methods create
instantaneous spans. Wrap the actual operation in a span for useful latency data.
Retrieval records require `chunk_id`, `document_id`, `document_name`, `content`, and
`score`; `rank` and `retrieval_method` are filled automatically. Set `selected` for
chunks used in context. `log_context` accepts `max_tokens` and a `chunks` list.

Set `RAGLENS_ENABLED=false` to disable delivery. Defaults: API URL
`http://localhost:8000`, enabled true, HTTP timeout two seconds. Constructor values
override environment variables. Delivery is synchronous on trace exit, without
retries (the ingestion API is not idempotent). Network, HTTP and serialization
failures warn without replacing the application's result or exception. Application
exceptions are recorded and propagate normally. Supply JSON-compatible dictionaries
for inputs, outputs, metrics and metadata; datetime and exception values serialize
into strings and structured errors. Avoid recording secrets or sensitive content.

After delivery `trace.id` contains the server-assigned ID. Set `project_id` and
optionally `web_url` on the client to populate `trace.url`.

## Tests and release

```sh
pip install -e 'packages/sdk-python[dev]'
pytest packages/sdk-python/tests
python -m build packages/sdk-python
python -m twine check packages/sdk-python/dist/*
```

Version is maintained in `pyproject.toml`; `raglens.__version__` reads the installed
metadata. For a release, bump that version, test, build into a clean `dist/`, then
upload the reviewed wheel and sdist using `python -m twine upload ...` with your
registry credentials. No package has been published by this implementation.
