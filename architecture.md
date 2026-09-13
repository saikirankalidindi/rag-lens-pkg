# RAGLens — Architecture & Implementation Plan

> Chrome DevTools for RAG pipelines.
>
> For every RAG answer, RAGLens should help the developer answer three questions:
> **What happened? Why did it happen? Where should I investigate?**

---

## 1. Repository Layout

Monorepo with clear separation between the web frontend, API backend, Python SDK, and supporting tooling.

```
raglens/
│
├── apps/
│   ├── web/                    # Next.js frontend (developer dashboard)
│   └── api/                    # FastAPI backend
│
├── packages/
│   └── sdk-python/             # Python SDK (pip install raglens)
│
├── examples/
│   └── basic-rag/              # Demo RAG app showing full SDK integration
│
├── docker/
│   ├── api.Dockerfile
│   └── web.Dockerfile
│
├── docs/                       # Additional documentation
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 2. Tech Stack

### Frontend — `apps/web/`

| Concern         | Choice                        |
|-----------------|-------------------------------|
| Framework       | Next.js 14 (App Router)       |
| Language        | TypeScript                    |
| Styling         | Tailwind CSS                  |
| Component lib   | shadcn/ui                     |
| Data fetching   | TanStack Query (React Query)  |
| Schema/validation | Zod                         |
| Icons           | Lucide React                  |
| Design language | Dark-first, developer-dense   |

Design inspiration: Linear, Sentry, Grafana, Vercel, Chrome DevTools.

### Backend — `apps/api/`

| Concern         | Choice              |
|-----------------|---------------------|
| Language        | Python 3.11+        |
| Framework       | FastAPI (async)     |
| Validation      | Pydantic v2         |
| ORM             | SQLAlchemy 2 (async)|
| Migrations      | Alembic             |
| Database        | PostgreSQL 15+      |
| Auth (browser)  | JWT / session token |
| Auth (SDK)      | Project API key     |
| Testing         | pytest + httpx      |

### SDK — `packages/sdk-python/`

| Concern     | Choice                            |
|-------------|-----------------------------------|
| Language    | Python 3.9+                       |
| HTTP client | httpx (sync + async compatible)   |
| Packaging   | pyproject.toml / setuptools       |
| Package name| `raglens`                         |

### Infrastructure

| Service    | Image                 |
|------------|-----------------------|
| Database   | postgres:15-alpine    |
| API        | Custom (api.Dockerfile) |
| Web        | Custom (web.Dockerfile) |

Local dev: `docker compose up` starts everything.

---

## 3. Core Domain Model

### 3.1 Entity Hierarchy

```
User
 └── Project (1:many)
       ├── ApiKey (1:many)
       └── Trace (1:many)
             ├── Span (1:many, nested)
             │     └── RetrievalResult (1:many, for retrieval spans)
             └── Diagnostic (1:many)
```

### 3.2 Trace

One user question → one Trace.

```
Trace
 ├── id              string      "trace_<ulid>"
 ├── project_id      FK
 ├── name            string      e.g. "answer_question"
 ├── session_id      string?
 ├── user_id         string?
 ├── started_at      timestamptz
 ├── ended_at        timestamptz
 ├── duration_ms     int
 ├── status          enum        success | warning | error
 ├── input           JSONB       { query: "..." }
 ├── output          JSONB       { answer: "..." }
 ├── metrics         JSONB       { input_tokens, output_tokens, total_tokens, estimated_cost }
 └── metadata        JSONB       { environment: "development" }
```

### 3.3 Span

Every meaningful operation inside a trace is a Span. Spans nest via `parent_span_id`.

```
Span
 ├── id              string      "span_<ulid>"
 ├── trace_id        FK
 ├── parent_span_id  FK?         enables nested spans (e.g., retrieval subtypes)
 ├── type            enum        query | query_rewrite | retrieval | reranking |
 │                               context | prompt | llm | response | custom
 ├── name            string      e.g. "vector_search"
 ├── started_at      timestamptz
 ├── ended_at        timestamptz
 ├── duration_ms     int
 ├── input           JSONB
 ├── output          JSONB
 ├── attributes      JSONB       span-type-specific extras
 └── status          enum        success | warning | error
```

The `attributes` JSONB field carries span-type-specific structured data (retrieval config, reranking deltas, prompt tokens, LLM provider params, etc.). Core searchable fields are real columns; everything flexible goes into JSONB.

### 3.4 RetrievalResult

Dedicated table for retrieval span results — structured for querying and display.

```
RetrievalResult
 ├── id                string
 ├── span_id           FK (type=retrieval span)
 ├── rank              int
 ├── chunk_id          string
 ├── document_id       string
 ├── document_name     string
 ├── content           text
 ├── score             float
 ├── retrieval_method  string      cosine | bm25 | hybrid | ...
 ├── selected          bool
 ├── reranked_rank     int?
 ├── reranker_score    float?
 └── metadata          JSONB       { page, department, year, ... }
```

### 3.5 Diagnostic

Rule-based, deterministic diagnostics attached to a trace.

```
Diagnostic
 ├── id          string
 ├── trace_id    FK
 ├── span_id     FK?           which span triggered this
 ├── severity    enum          info | warning | error
 ├── category    enum          retrieval | context | latency | tokens | generation
 ├── title       string
 ├── description text
 ├── evidence    JSONB         { score: 0.54, threshold: 0.70, ... }
 └── suggestions JSONB         ["check embedding model", ...]
```

### 3.6 ApiKey

```
ApiKey
 ├── id           string
 ├── project_id   FK
 ├── name         string      user-given label
 ├── key_prefix   string      "rgl_live_" or "rgl_test_"  — stored plain for display
 ├── key_hash     string      bcrypt/sha256 of full key — NEVER store raw
 ├── created_at   timestamptz
 ├── last_used_at timestamptz?
 └── revoked_at   timestamptz?
```

Full key shown **once** at creation time. Never logged, never stored.

---

## 4. Backend Structure (`apps/api/`)

```
apps/api/
├── app/
│   ├── main.py              # FastAPI app factory, CORS, middleware, router registration
│   ├── config.py            # Settings via pydantic-settings + environment variables
│   │
│   ├── api/                 # Route handlers (thin — delegate to services)
│   │   ├── auth.py          # User login / register / session
│   │   ├── projects.py      # CRUD projects
│   │   ├── traces.py        # List, filter, get trace detail
│   │   ├── ingestion.py     # POST /v1/traces  (API-key auth)
│   │   └── api_keys.py      # Create / revoke API keys
│   │
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── api_key.py
│   │   ├── trace.py
│   │   ├── span.py
│   │   ├── retrieval_result.py
│   │   └── diagnostic.py
│   │
│   ├── schemas/             # Pydantic request/response schemas
│   │   ├── project.py
│   │   ├── trace.py
│   │   ├── span.py
│   │   ├── ingestion.py
│   │   └── diagnostic.py
│   │
│   ├── services/            # Business logic
│   │   ├── project_service.py
│   │   ├── trace_service.py
│   │   ├── ingestion_service.py
│   │   └── api_key_service.py
│   │
│   ├── repositories/        # Database access layer
│   │   ├── project_repo.py
│   │   ├── trace_repo.py
│   │   ├── span_repo.py
│   │   └── api_key_repo.py
│   │
│   ├── diagnostics/         # Rule-based diagnostics engine
│   │   ├── engine.py        # Runs all rules against a trace
│   │   ├── rules/
│   │   │   ├── retrieval.py     # low_confidence, retrieval_waste, slow_retrieval
│   │   │   ├── context.py       # excessive_context, low_context_utilization
│   │   │   ├── latency.py       # slow_retrieval, slow_generation, latency_breakdown
│   │   │   └── tokens.py        # token_heavy_context
│   │   └── models.py        # DiagnosticResult dataclass
│   │
│   ├── auth/
│   │   ├── dependencies.py  # FastAPI Depends: get_current_user, verify_api_key
│   │   └── hashing.py       # API key hashing utilities
│   │
│   └── database/
│       ├── connection.py    # Async SQLAlchemy engine + session factory
│       └── seed.py          # Realistic seed data (7 scenario traces)
│
├── migrations/              # Alembic migrations
│   ├── env.py
│   └── versions/
│
├── tests/
│   ├── test_traces.py
│   ├── test_ingestion.py
│   ├── test_api_keys.py
│   ├── test_diagnostics.py
│   └── conftest.py
│
├── pyproject.toml
└── alembic.ini
```

### API Surface

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | — | Create user |
| POST | `/auth/login` | — | Get session token |
| GET | `/projects` | user | List projects |
| POST | `/projects` | user | Create project |
| GET | `/projects/{id}` | user | Get project + stats |
| GET | `/projects/{id}/traces` | user | List + filter traces |
| GET | `/projects/{id}/traces/{tid}` | user | Full trace detail |
| POST | `/projects/{id}/api-keys` | user | Create API key |
| DELETE | `/projects/{id}/api-keys/{kid}` | user | Revoke API key |
| POST | `/v1/traces` | api_key | Ingest a trace |

All list endpoints are paginated. Heavy payloads (prompt content, chunk content) are excluded from list endpoints and returned only in the detail endpoint.

---

## 5. Frontend Structure (`apps/web/`)

```
apps/web/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   │
│   ├── projects/
│   │   ├── page.tsx                         # Project list / new project
│   │   └── [projectId]/
│   │       ├── layout.tsx                   # App shell (sidebar)
│   │       ├── page.tsx                     # Overview (stats + charts + recent traces)
│   │       ├── traces/
│   │       │   ├── page.tsx                 # Trace explorer (table + filters)
│   │       │   └── [traceId]/page.tsx       # Trace debugger
│   │       └── settings/
│   │           ├── page.tsx
│   │           └── api-keys/page.tsx
│   │
│   └── layout.tsx                           # Root layout
│
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx
│   │   └── AppShell.tsx
│   │
│   ├── traces/
│   │   ├── TraceTable.tsx
│   │   ├── TraceFilters.tsx
│   │   ├── TraceStatusBadge.tsx
│   │   └── EmptyTraceState.tsx              # "Send your first trace" onboarding
│   │
│   ├── debugger/
│   │   ├── TraceDebugger.tsx                # Main split-pane layout
│   │   ├── SpanTimeline.tsx                 # Left panel: span tree with durations
│   │   ├── SpanInspector.tsx                # Right panel: dispatches to specific inspector
│   │   ├── inspectors/
│   │   │   ├── RetrievalInspector.tsx
│   │   │   ├── RerankingInspector.tsx
│   │   │   ├── ContextInspector.tsx
│   │   │   ├── PromptInspector.tsx
│   │   │   └── LLMInspector.tsx
│   │   └── DiagnosticsPanel.tsx
│   │
│   ├── overview/
│   │   ├── MetricCard.tsx
│   │   ├── RequestsChart.tsx
│   │   ├── LatencyChart.tsx
│   │   └── RecentTraces.tsx
│   │
│   └── ui/                                  # shadcn/ui primitives (auto-generated)
│
├── lib/
│   ├── api.ts                               # Typed API client (fetch wrappers)
│   ├── types.ts                             # Shared TypeScript types (mirrors backend schemas)
│   └── utils.ts                             # cn(), formatters, etc.
│
├── hooks/
│   ├── useProject.ts
│   ├── useTraces.ts
│   └── useTrace.ts
│
├── tailwind.config.ts
├── next.config.ts
└── package.json
```

### Page Map

| Route | Description |
|-------|-------------|
| `/login` | Auth |
| `/projects` | Project list |
| `/projects/[id]` | Overview: stats, charts, recent traces |
| `/projects/[id]/traces` | Trace explorer: filterable, paginated table |
| `/projects/[id]/traces/[tid]` | Trace debugger: timeline + inspector |
| `/projects/[id]/settings` | Project settings |
| `/projects/[id]/settings/api-keys` | API key management |

---

## 6. Python SDK (`packages/sdk-python/`)

```
packages/sdk-python/
├── raglens/
│   ├── __init__.py          # Public API: RAGLens, Trace, Span
│   ├── client.py            # RAGLens(api_key, base_url) — HTTP transport
│   ├── trace.py             # Trace context manager
│   ├── span.py              # Span context manager
│   ├── helpers.py           # log_retrieval(), log_context(), log_prompt(), log_generation()
│   ├── serializers.py       # Convert Python objects → ingestion payload
│   └── exceptions.py        # RAGLensError, IngestionError (never propagated to caller)
│
├── tests/
│   ├── test_trace.py
│   ├── test_span.py
│   └── test_serializers.py
│
└── pyproject.toml
```

SDK design principles:
- Context manager on `Trace` and `Span` auto-captures `started_at`, `ended_at`, `duration_ms`, and exceptions.
- If HTTP ingestion fails for any reason, log a warning but **never raise** — the host application must not crash.
- All network calls happen on `__exit__` (or async equivalent) — no blocking mid-pipeline.
- `base_url` defaults to `http://localhost:8000` for local dev, configurable via `RAGLENS_BASE_URL` env var.

---

## 7. Diagnostics Engine

All diagnostics are deterministic rule-based checks. No external LLM calls.

Each rule receives a trace + its spans and returns zero or more `DiagnosticResult` objects.

| Rule | Severity | Trigger |
|------|----------|---------|
| `low_retrieval_confidence` | warning | max retrieval score < threshold (default 0.70) |
| `retrieval_waste` | info | chunks retrieved >> chunks selected (ratio > 3×) |
| `slow_retrieval` | warning | retrieval span duration > threshold (default 500ms) |
| `excessive_context` | warning | context token% of model context window > threshold (default 80%) |
| `low_context_utilization` | info | many chunks retrieved, few used |
| `slow_generation` | warning | llm span > X% of total trace duration (default 85%) |
| `token_heavy_context` | warning | context accounts for > 85% of input tokens |
| `failed_span` | error | any span has status=error |

Thresholds are configurable via environment variables or project settings in the future.

---

## 8. Database Schema Notes

- Use `ULID` string IDs (sortable, prefixed: `trace_`, `span_`, `project_`, etc.) for all primary keys. Prefix makes logs readable.
- `JSONB` for `input`, `output`, `attributes`, `metadata`, `evidence`, `suggestions` — flexible without losing structure.
- Real columns for everything that will be filtered/sorted: `status`, `started_at`, `duration_ms`, `project_id`, `trace_id`, `span_type`.

### Indexes

```sql
-- traces
CREATE INDEX idx_traces_project_id    ON traces(project_id);
CREATE INDEX idx_traces_started_at    ON traces(started_at DESC);
CREATE INDEX idx_traces_status        ON traces(status);

-- spans
CREATE INDEX idx_spans_trace_id       ON spans(trace_id);
CREATE INDEX idx_spans_type           ON spans(type);

-- retrieval_results
CREATE INDEX idx_retrieval_span_id    ON retrieval_results(span_id);

-- api_keys
CREATE INDEX idx_api_keys_key_prefix  ON api_keys(key_prefix);
```

---

## 9. Security Baseline

- API keys: `sha256(key)` stored; full key shown once at creation, never again.
- Key format: `rgl_live_<32 random chars>` / `rgl_test_<32 random chars>`.
- CORS: configured via `CORS_ORIGINS` env var; no wildcard in production.
- Payload size: configurable `MAX_TRACE_PAYLOAD_BYTES` enforced at ingestion.
- Rate limiting: hook in middleware (implementation in Phase 5+).
- No raw HTML rendered from trace payloads — escape all user-supplied content.
- No API keys in frontend bundles — ingestion endpoint is backend-only.

---

## 10. Environment Variables (`.env.example`)

```env
# Database
DATABASE_URL=postgresql+asyncpg://raglens:raglens@localhost:5432/raglens

# API
SECRET_KEY=changeme-use-a-real-secret-in-production
CORS_ORIGINS=http://localhost:3000
MAX_TRACE_PAYLOAD_BYTES=5242880   # 5 MB

# Web
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional
LOG_LEVEL=INFO
```

---

## 11. Implementation Phases

### Phase 1 — Foundation

**Goal:** Everything boots. Nothing crashes.

- Init monorepo directory structure
- `apps/api/`: FastAPI + SQLAlchemy + Alembic + config + database connection + health endpoint
- `apps/web/`: Next.js + Tailwind + shadcn/ui + app shell (sidebar, layout)
- `docker-compose.yml`: PostgreSQL + API + Web
- `.env.example`
- First Alembic migration (users, projects tables)

Deliverable: `docker compose up` → API returns `{"status": "ok"}`, web renders shell.

---

### Phase 2 — Core Domain

**Goal:** Data model is complete and seed data makes the dashboard immediately useful.

- ORM models: user, project, api_key, trace, span, retrieval_result, diagnostic
- Alembic migrations for all tables + indexes
- Pydantic schemas
- Repositories + services for projects and traces
- Seed script with 7 realistic scenario traces:
  - Successful RAG
  - Poor retrieval (low scores)
  - Excessive context
  - Slow retrieval
  - Slow LLM
  - Failed request
  - Reranking scenario

Deliverable: Seed runs without error; can query traces from the DB.

---

### Phase 3 — Trace Explorer

**Goal:** The main product UI works against seed data.

- Overview page: 4 stat cards + 3 charts + recent traces table
- Trace explorer: dense table, filters (status, environment, date range, search)
- Pagination on all list endpoints
- TanStack Query wiring in frontend

Deliverable: Can browse and filter all 7 seed traces in the browser.

---

### Phase 4 — RAG Inspectors

**Goal:** Clicking a trace shows the full debugger experience.

- Trace debugger: split-pane (span timeline left, inspector right)
- `SpanTimeline` with nested spans and duration bars
- Per-span inspectors: Retrieval, Reranking, Context, Prompt, LLM
- `DiagnosticsPanel` at top of trace detail

Deliverable: All 7 seed trace scenarios are fully explorable in the UI.

---

### Phase 5 — Ingestion + Auth

**Goal:** Real traces from real apps can be sent in.

- User registration + login (JWT)
- `POST /v1/traces` with API-key authentication
- API key creation/revocation UI
- Payload validation (Pydantic), size limits
- `curl` test documented in README

Deliverable: `curl -X POST /v1/traces -H "Authorization: Bearer rgl_test_..."` ingests a trace that appears in the UI.

---

### Phase 6 — Python SDK

**Goal:** `pip install raglens` and instrument a Python app in 10 lines.

- `RAGLens`, `Trace`, `Span` context managers
- Helper methods: `log_retrieval()`, `log_context()`, `log_prompt()`, `log_generation()`
- Auto-capture of timestamps, duration, exceptions
- Graceful failure (never crashes host)
- Unit tests: trace CM, span CM, exception handling, failed ingestion, serialization

Deliverable: SDK sends a trace from a Python script; trace appears in RAGLens dashboard.

---

### Phase 7 — Diagnostics

**Goal:** Every trace shows useful, deterministic diagnostic insights.

- Diagnostics engine + all 8 rules
- Diagnostics stored on trace ingest (run automatically)
- `DiagnosticsPanel` in the trace debugger UI
- Clicking a diagnostic highlights the relevant span in the timeline

Deliverable: Low-confidence retrieval seed trace shows a "Low retrieval confidence" warning.

---

### Phase 8 — Demo App

**Goal:** End-to-end workflow is demonstrable without paid APIs.

- `examples/basic-rag/`: minimal RAG using local data + a local/free LLM option
- Fully instrumented with the RAGLens SDK
- README section: "Run the demo"
- Verify the complete 16-step MVP success criteria from `tasks.md §42`

Deliverable: `python examples/basic-rag/app.py` → trace appears in RAGLens → all inspectors show real data.

---

## 12. Key Design Decisions & Rationale

**Why not OpenTelemetry?** OTel is powerful but introduces significant complexity for the MVP. The trace/span model is architecturally compatible with OTel concepts, making a future bridge feasible without committing now.

**Why ULID instead of UUID?** ULIDs are sortable by creation time (useful for trace ordering), URL-safe, and the prefix (e.g. `trace_`, `span_`) makes logs and debugging far more readable at zero cost.

**Why JSONB for input/output/attributes?** RAG pipelines differ wildly between teams. Forcing a rigid schema on span attributes would make RAGLens unusable for non-standard pipelines. JSONB gives flexibility while core fields stay typed.

**Why rule-based diagnostics (not LLM-based)?** Deterministic rules are explainable, testable, fast, and free. Adding LLM-based semantic evaluation is a Phase 2+ feature — the architecture supports it without changes to the diagnostic contract.

**Why separate ingestion auth from user auth?** Project API keys are embedded in backend services. User sessions belong in browsers. Mixing them would create security and architectural confusion.

**Why store retrieval results in a dedicated table?** It enables SQL-level queries like "which projects have average top-1 retrieval scores below 0.7" — impossible if results are buried in JSONB. This is the foundation for future aggregate analytics.

---

## 13. What Is NOT in the MVP

These are explicitly deferred and should be marked "Coming soon" in the UI:

- Playground
- Evaluations
- Billing / SSO / RBAC
- OpenTelemetry compatibility
- Auto-instrumentation (LangChain, LlamaIndex integrations)
- Production-scale distributed ingestion
- LLM-based semantic diagnostics
- Kubernetes deployment
- Enterprise organizations
