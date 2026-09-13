# Basic RAG demo

Run from the repository root with Python 3.9 or newer:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r examples/basic-rag/requirements.txt
python examples/basic-rag/app.py --offline
```

The six bundled documents use local TF-IDF vectors and cosine similarity. Generation
is an extractive mock, so no paid API, model download, or GPU is needed. Token counts
are word-count estimates. Three scenarios exercise relevant, missing, and multiple
sources; use `--question "..."` for your own query.

To inspect traces, start RAGLens (`docker compose up`), register in the dashboard,
create a project and its API key, then run:

```sh
export RAGLENS_API_KEY='your-project-api-key'
export RAGLENS_PROJECT_ID='your-project-id'
export RAGLENS_BASE_URL='http://localhost:8000'
python examples/basic-rag/app.py
```

Each request records nested query, retrieval, context, prompt and generation spans.
A successful delivery prints a dashboard URL when the project ID is configured.
Low similarity scores in this small TF-IDF corpus may trigger the default confidence
threshold, which is tuned for other embedding models; this is expected.

If no trace appears, check the API URL and key, ensure the key is active, and check
that `RAGLENS_ENABLED` is not false. Without a project ID the script prints the trace
ID instead of a URL. HTTP failures log a warning and leave the answer available.
