# RAGLens

> Chrome DevTools for RAG pipelines.

RAGLens is a developer-first observability platform for Retrieval-Augmented Generation (RAG) applications. Instrument your RAG pipeline once, then inspect every request in detail: what was retrieved, how chunks were ranked, what context reached the model, what prompt was sent, and how the model responded.

**For every RAG answer, RAGLens helps you answer three questions:**
- What happened?
- Why did it happen?
- Where should I investigate?

---

## Architecture

```
┌────────────────────────────────────────────┐
│           RAG Application                  │
│   (Python, LangChain, LlamaIndex, etc.)    │
└──────────────────┬─────────────────────────┘
                   │ RAGLens SDK (pip install raglens)
                   ▼
┌────────────────────────────────────────────┐
│           RAGLens API (FastAPI)            │
│   POST /v1/traces  ←  API key auth         │
│   GET  /projects/{id}/traces  ← JWT auth   │
└──────────────────┬─────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────┐
│           PostgreSQL                       │
│   traces · spans · retrieval_results       │
│   diagnostics · projects · api_keys        │
└──────────────────┬─────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────┐
│           RAGLens Web (Next.js)            │
│   Trace explorer · Span debugger           │
│   Retrieval · Reranking · Prompt · LLM     │
└────────────────────────────────────────────┘
```

### Repository Structure

```
raglens/
├── apps/
│   ├── api/              FastAPI backend
│   └── web/              Next.js frontend
├── packages/
│   └── sdk-python/       Python SDK (pip install raglens)
├── examples/
│   └── basic-rag/        Demo RAG application
├── docker/
│   ├── api.Dockerfile
│   └── web.Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## Quick Start

For the complete setup and instrumentation walkthrough, including retrieval,
context, prompt, LLM, nesting, errors, disabled tracing, and the Qdrant/OpenRouter
demo, see [docs/QUICKSTART.md](docs/QUICKSTART.md).

### Prerequisites

- [Docker](https://www.docker.com/get-started) and Docker Compose
- A terminal

### 1. Clone and configure

```bash
git clone https://github.com/your-org/raglens.git
cd raglens

cp .env.example .env
# Edit .env if you want to change ports or the secret key
```

### 2. Start everything

```bash
docker compose up
```

This starts:
- PostgreSQL on port `5432`
- RAGLens API on port `8000`
- RAGLens Web on port `3000`

On first boot the API automatically runs database migrations.

After pulling code or dependency changes, rebuild the images with `docker compose up --build`.
To refresh only the API while services are running, use `docker compose up -d --build --no-deps api`.
A plain `docker compose up` can reuse an older image with outdated dependencies.

### 3. Open the dashboard

```
http://localhost:3000
```

### 4. Verify the API is healthy

```bash
curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0"}
```

---

## Development

### Backend (FastAPI)

```bash
cd apps/api

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Start PostgreSQL (via Docker Compose)
docker compose up db -d

# Copy and configure environment
cp ../../.env.example .env
# Make sure DATABASE_URL and DATABASE_SYNC_URL point to localhost:5432

# Run migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

### Frontend (Next.js)

```bash
cd apps/web

npm install
npm run dev
```

Frontend available at: `http://localhost:3000`

### Running tests

```bash
# Backend and SDK (from repository root)
pip install -e "apps/api[dev]" -e "packages/sdk-python[dev]"
pytest apps/api/tests packages/sdk-python/tests

# Frontend
cd apps/web
npm run build  # includes TypeScript validation
npm run lint
```

---

## Browser regression tests

Start a disposable stack with `docker compose up --build`, then from `apps/web` run:

```sh
npx playwright install chromium
npm run test:e2e
```

These tests create test accounts and project data and use the bundled demo account
for inspector coverage. Use `E2E_WEB_URL` and `E2E_API_URL` to target another test stack.
They cover registration, project creation/view/settings, keys, charts, filters,
pagination, inspectors, error recovery and session restoration.

## Creating a Project

1. Register an account at `http://localhost:3000`
2. Create a new project
3. Navigate to **Settings → API Keys**
4. Create an API key (shown once)

---

## Sending Your First Trace

### Install the SDK

```bash
pip install -e packages/sdk-python
```

See [SDK documentation](packages/sdk-python/README.md) and the [offline demo](examples/basic-rag/README.md). Registry publication is a separate release step.

### Instrument your pipeline

```python
from raglens import RAGLens

raglens = RAGLens(api_key="rgl_test_...")

with raglens.trace(name="answer_question", input={"query": question}) as trace:

    with trace.span(type="retrieval", name="vector_search") as span:
        documents = retriever.invoke(question)
        span.set_output({"results": [...]})

    with trace.span(type="llm", name="generate") as span:
        response = llm.invoke(prompt)
        span.set_output({"answer": response.content})

    trace.set_output({"answer": response.content})
```

### View the trace

Open `http://localhost:3000`, navigate to your project, and the trace will appear in the trace explorer.

---

## Implementation Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Foundation (monorepo, API skeleton, web shell, Docker) | ✅ Complete |
| 2 | Core domain (models, migrations, seed data) | ✅ Complete |
| 3 | Trace explorer (overview, table, filters) | ✅ Complete |
| 4 | RAG inspectors (retrieval, reranking, context, prompt, LLM) | ✅ Complete |
| 5 | Ingestion + auth (API keys, JWT, ingestion endpoint) | ✅ Complete |
| 6 | Python SDK | ✅ Complete |
| 7 | Diagnostics engine | ✅ Complete |
| 8 | Demo application | ✅ Complete |

---

## Environment Variables

See [`.env.example`](.env.example) for the full list with documentation.

Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Async PostgreSQL URL (asyncpg) | `postgresql+asyncpg://raglens:raglens@localhost:5432/raglens` |
| `DATABASE_SYNC_URL` | Sync PostgreSQL URL (Alembic) | `postgresql://raglens:raglens@localhost:5432/raglens` |
| `SECRET_KEY` | JWT signing secret — **change in production** | `changeme-...` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000` |
| `NEXT_PUBLIC_API_URL` | API base URL for the browser | `http://localhost:8000` |

---

## License

MIT
