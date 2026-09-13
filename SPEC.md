# RAGLens Implementation Spec

## Overview

**Project Name:** RAGLens  
**Vision:** Chrome DevTools for RAG pipelines  
**Core Value:** For every RAG answer, help developers understand: What happened? Why did it happen? Where should I investigate?

**Architecture Reference:** #[[file:architecture.md]]

---

## Requirements

### Functional Requirements

#### FR1: User Management
- Users can register and log in to the system
- Authentication via JWT/session tokens
- Users can manage multiple projects

#### FR2: Project Management
- Users can create and view projects
- Each project has API keys for trace ingestion
- Projects display aggregate statistics and metrics
- Projects show recent traces and activity

#### FR3: API Key Management
- Users can create API keys with descriptive names
- Keys use format: `rgl_live_<32chars>` or `rgl_test_<32chars>`
- Full key shown once at creation, never stored in plain text
- Keys can be revoked
- Keys track last usage timestamp

#### FR4: Trace Ingestion
- External applications can POST traces via API
- API key authentication required
- Payload size limit: 5MB (configurable)
- Automatic timestamp and duration capture
- Support for nested span hierarchies

#### FR5: Trace Explorer
- List all traces for a project
- Filter by:
  - Status (success, warning, error)
  - Environment (development, staging, production)
  - Date range
  - Text search across trace names
- Pagination support
- Sort by date, duration, status

#### FR6: Trace Debugger
- View complete trace details including all spans
- Split-pane interface: timeline left, inspector right
- Nested span visualization with duration bars
- Click span to view detailed inspector
- Different inspectors for span types:
  - Retrieval Inspector
  - Reranking Inspector
  - Context Inspector
  - Prompt Inspector
  - LLM Inspector

#### FR7: Diagnostics
- Automatic diagnostic analysis on trace ingestion
- Rule-based checks for common issues:
  - Low retrieval confidence (score < 0.70)
  - Retrieval waste (retrieved >> selected)
  - Slow retrieval (> 500ms)
  - Excessive context (> 80% of context window)
  - Low context utilization
  - Slow generation (> 85% of trace duration)
  - Token-heavy context (> 85% of input tokens)
  - Failed spans
- Diagnostics panel in trace debugger
- Severity levels: info, warning, error
- Click diagnostic to highlight relevant span

#### FR8: Python SDK
- Context manager API for traces and spans
- Helper methods for common operations:
  - `log_retrieval()`
  - `log_context()`
  - `log_prompt()`
  - `log_generation()`
- Automatic timestamp and duration capture
- Exception handling and status tracking
- Graceful failure (never crash host application)
- Configurable via environment variables

#### FR9: Project Overview
- Display 4 key metric cards:
  - Total traces
  - Average latency
  - Success rate
  - Total tokens
- 3 charts:
  - Requests over time
  - Latency distribution
  - Token usage over time
- Recent traces table

#### FR10: Seed Data
- 7 realistic scenario traces for development:
  1. Successful RAG flow
  2. Poor retrieval (low scores)
  3. Excessive context
  4. Slow retrieval
  5. Slow LLM generation
  6. Failed request
  7. Reranking scenario

### Non-Functional Requirements

#### NFR1: Performance
- Trace list endpoint responds in < 200ms
- Trace detail endpoint responds in < 500ms
- Support pagination for large trace lists
- Efficient JSONB queries on PostgreSQL

#### NFR2: Security
- API keys hashed with SHA256 before storage
- No API keys in frontend bundles
- CORS configuration via environment variable
- All user-supplied content escaped (no XSS)
- Payload size limits enforced

#### NFR3: Scalability
- Support for nested span hierarchies
- JSONB for flexible span attributes
- Indexed queries on frequently filtered fields
- ULID-based sortable IDs

#### NFR4: Maintainability
- Clean separation: repositories → services → API routes
- Type-safe schemas (Pydantic backend, Zod frontend)
- Comprehensive error handling
- Clear logging for debugging

#### NFR5: Developer Experience
- Single command to start: `docker compose up`
- Seed data populates immediately
- Clear environment variable configuration
- TypeScript for frontend type safety

---

## Design

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│  Next.js 14 + TypeScript + Tailwind + shadcn/ui            │
│                                                             │
│  Pages:                                                     │
│  • Login/Register                                           │
│  • Project List & Overview                                  │
│  • Trace Explorer (table + filters)                         │
│  • Trace Debugger (timeline + inspectors)                   │
│  • API Key Management                                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ HTTP/JSON
                 │
┌────────────────┴────────────────────────────────────────────┐
│                      Backend API                            │
│              FastAPI + SQLAlchemy + Pydantic                │
│                                                             │
│  Endpoints:                                                 │
│  • /auth/register, /auth/login                             │
│  • /projects (CRUD)                                        │
│  • /projects/{id}/traces (list, filter)                   │
│  • /projects/{id}/traces/{tid} (detail)                   │
│  • /projects/{id}/api-keys (create, revoke)               │
│  • /v1/traces (ingestion)                                  │
│                                                             │
│  Components:                                                │
│  • Diagnostics Engine (rule-based)                         │
│  • Repositories (data access)                              │
│  • Services (business logic)                               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ SQLAlchemy ORM
                 │
┌────────────────┴────────────────────────────────────────────┐
│                     PostgreSQL 15+                          │
│                                                             │
│  Tables:                                                    │
│  • users                                                    │
│  • projects                                                 │
│  • api_keys                                                 │
│  • traces                                                   │
│  • spans (with parent_span_id for nesting)                 │
│  • retrieval_results                                        │
│  • diagnostics                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       Python SDK                            │
│                    raglens package                          │
│                                                             │
│  API:                                                       │
│  • RAGLens(api_key, base_url)                              │
│  • with Trace(...) as trace:                               │
│  •   with Span(...) as span:                               │
│  •     log_retrieval(...)                                  │
│                                                             │
│  POSTs to: /v1/traces                                      │
└─────────────────────────────────────────────────────────────┘
```

### Data Model

#### Entity Relationships

```
User (1) ──────< (many) Project
                           │
                           ├────< (many) ApiKey
                           │
                           └────< (many) Trace
                                         │
                                         ├────< (many) Span
                                         │              │
                                         │              └────< (many) RetrievalResult
                                         │
                                         └────< (many) Diagnostic
```

#### Core Entities

**User**
- id: string (ULID)
- email: string (unique)
- password_hash: string
- created_at: timestamp
- updated_at: timestamp

**Project**
- id: string (ULID with "project_" prefix)
- user_id: FK → User
- name: string
- description: string (optional)
- created_at: timestamp
- updated_at: timestamp

**ApiKey**
- id: string (ULID)
- project_id: FK → Project
- name: string (user label)
- key_prefix: string ("rgl_live_" or "rgl_test_")
- key_hash: string (SHA256)
- created_at: timestamp
- last_used_at: timestamp (nullable)
- revoked_at: timestamp (nullable)

**Trace**
- id: string (ULID with "trace_" prefix)
- project_id: FK → Project
- name: string
- session_id: string (optional)
- user_id: string (optional, end user ID)
- started_at: timestamp
- ended_at: timestamp
- duration_ms: integer
- status: enum (success, warning, error)
- input: JSONB
- output: JSONB
- metrics: JSONB {input_tokens, output_tokens, total_tokens, estimated_cost}
- metadata: JSONB {environment, version, etc.}

**Span**
- id: string (ULID with "span_" prefix)
- trace_id: FK → Trace
- parent_span_id: FK → Span (nullable, for nesting)
- type: enum (query, query_rewrite, retrieval, reranking, context, prompt, llm, response, custom)
- name: string
- started_at: timestamp
- ended_at: timestamp
- duration_ms: integer
- input: JSONB
- output: JSONB
- attributes: JSONB (span-type-specific data)
- status: enum (success, warning, error)

**RetrievalResult**
- id: string (ULID)
- span_id: FK → Span
- rank: integer
- chunk_id: string
- document_id: string
- document_name: string
- content: text
- score: float
- retrieval_method: string (cosine, bm25, hybrid, etc.)
- selected: boolean
- reranked_rank: integer (nullable)
- reranker_score: float (nullable)
- metadata: JSONB

**Diagnostic**
- id: string (ULID)
- trace_id: FK → Trace
- span_id: FK → Span (nullable)
- severity: enum (info, warning, error)
- category: enum (retrieval, context, latency, tokens, generation)
- title: string
- description: text
- evidence: JSONB
- suggestions: JSONB (array of strings)

### Database Indexes

```sql
-- Traces
CREATE INDEX idx_traces_project_id ON traces(project_id);
CREATE INDEX idx_traces_started_at ON traces(started_at DESC);
CREATE INDEX idx_traces_status ON traces(status);

-- Spans
CREATE INDEX idx_spans_trace_id ON spans(trace_id);
CREATE INDEX idx_spans_type ON spans(type);

-- RetrievalResults
CREATE INDEX idx_retrieval_span_id ON retrieval_results(span_id);

-- ApiKeys
CREATE INDEX idx_api_keys_key_prefix ON api_keys(key_prefix);
```

### API Endpoints

#### Authentication
- `POST /auth/register` - Create new user
  - Body: `{email, password}`
  - Returns: `{user_id, email}`

- `POST /auth/login` - Authenticate user
  - Body: `{email, password}`
  - Returns: `{token, user}`

#### Projects
- `GET /projects` - List user's projects
  - Auth: User token
  - Returns: `[{id, name, description, created_at, trace_count, last_trace_at}]`

- `POST /projects` - Create project
  - Auth: User token
  - Body: `{name, description?}`
  - Returns: `{id, name, description, created_at}`

- `GET /projects/{id}` - Get project with stats
  - Auth: User token
  - Returns: `{project, stats: {total_traces, avg_latency, success_rate, total_tokens}}`

#### Traces
- `GET /projects/{id}/traces` - List traces with filters
  - Auth: User token
  - Query: `status?, environment?, start_date?, end_date?, search?, page?, limit?`
  - Returns: `{items: [...], total, page, limit}`

- `GET /projects/{id}/traces/{tid}` - Get trace detail
  - Auth: User token
  - Returns: `{trace, spans: [...], diagnostics: [...]}`

#### API Keys
- `POST /projects/{id}/api-keys` - Create API key
  - Auth: User token
  - Body: `{name}`
  - Returns: `{id, name, key: "rgl_live_...", key_prefix, created_at}` (key shown once only)

- `DELETE /projects/{id}/api-keys/{kid}` - Revoke API key
  - Auth: User token
  - Returns: `{success: true}`

- `GET /projects/{id}/api-keys` - List API keys
  - Auth: User token
  - Returns: `[{id, name, key_prefix, created_at, last_used_at, revoked_at}]`

#### Ingestion
- `POST /v1/traces` - Ingest trace
  - Auth: `Authorization: Bearer {api_key}`
  - Body: `{trace, spans: [...], retrieval_results?: [...]}`
  - Returns: `{trace_id, status: "ingested"}`

### Frontend Routes

```
/login                                      Auth page
/register                                   Auth page
/projects                                   Project list
/projects/[id]                             Project overview
/projects/[id]/traces                      Trace explorer (table + filters)
/projects/[id]/traces/[tid]                Trace debugger
/projects/[id]/settings                    Project settings
/projects/[id]/settings/api-keys           API key management
```

### Diagnostics Rules

| Rule ID | Severity | Trigger | Threshold |
|---------|----------|---------|-----------|
| `low_retrieval_confidence` | warning | Max retrieval score < threshold | 0.70 |
| `retrieval_waste` | info | Retrieved chunks / Selected chunks | > 3× |
| `slow_retrieval` | warning | Retrieval span duration | > 500ms |
| `excessive_context` | warning | Context tokens / Max tokens | > 80% |
| `low_context_utilization` | info | Selected chunks / Retrieved chunks | < 40% |
| `slow_generation` | warning | LLM duration / Total duration | > 85% |
| `token_heavy_context` | warning | Context tokens / Input tokens | > 85% |
| `failed_span` | error | Span status | = error |

---

## Implementation Tasks

### Phase 1: Foundation ✅ COMPLETE

**Goal:** Everything boots. Nothing crashes.

#### Task 1.1: Initialize Monorepo Structure
- Create directory structure per architecture.md
- Set up `apps/api/`, `apps/web/`, `packages/sdk-python/`
- Create `.env.example` with all required variables
- Create `docker-compose.yml` for PostgreSQL, API, Web

#### Task 1.2: Backend Foundation
- Initialize FastAPI application in `apps/api/app/main.py`
- Set up config.py with pydantic-settings
- Configure CORS middleware
- Create database connection module with async SQLAlchemy
- Add health check endpoint: `GET /health`
- Create basic error handlers

#### Task 1.3: Database Setup
- Configure Alembic for migrations
- Create first migration: users and projects tables
- Add database indexes
- Test migration up/down

#### Task 1.4: Frontend Foundation
- Initialize Next.js 14 with App Router in `apps/web/`
- Configure Tailwind CSS
- Install and configure shadcn/ui
- Create root layout with basic styling
- Create app shell with sidebar component
- Add TypeScript configuration

#### Task 1.5: Docker Configuration
- Create `api.Dockerfile`
- Create `web.Dockerfile`
- Test `docker compose up` boots all services
- Verify health endpoint returns OK

**Acceptance Criteria:**
- ✅ `docker compose up` starts PostgreSQL, API, and Web
- ✅ API returns `{"status": "ok"}` at `/health`
- ✅ Web app renders empty shell at `http://localhost:3000`
- ✅ No errors in any service logs

---

### Phase 2: Core Domain ✅ COMPLETE

**Goal:** Data model is complete and seed data makes the dashboard immediately useful.

#### Task 2.1: ORM Models
- Create all SQLAlchemy models:
  - `models/user.py`
  - `models/project.py`
  - `models/api_key.py`
  - `models/trace.py`
  - `models/span.py`
  - `models/retrieval_result.py`
  - `models/diagnostic.py`
- Add relationships and foreign keys
- Use ULID for primary keys with prefixes
- Add JSONB fields where specified

#### Task 2.2: Database Migration
- Create Alembic migration for all tables
- Add all indexes per design
- Test migration on fresh database
- Verify schema matches design

#### Task 2.3: Pydantic Schemas
- Create request/response schemas:
  - `schemas/project.py`
  - `schemas/trace.py`
  - `schemas/ingestion.py`
  - `schemas/diagnostic.py`
- Add validation rules
- Mirror TypeScript types for frontend

#### Task 2.4: Repositories
- Create repository pattern implementations:
  - `repositories/project_repo.py`
  - `repositories/trace_repo.py`
  - `repositories/user_repo.py`
  - `repositories/api_key_repo.py`
- Add query methods with filters
- Add pagination support

#### Task 2.5: Services Layer
- Create service implementations:
  - `services/project_service.py`
  - `services/trace_service.py`
  - `services/ingestion_service.py`
- Implement business logic
- Add error handling

#### Task 2.6: Seed Data
- Create `app/seed.py` script
- Implement 7 realistic trace scenarios:
  1. Successful RAG flow
  2. Poor retrieval (low scores)
  3. Excessive context
  4. Slow retrieval
  5. Slow LLM generation
  6. Failed request
  7. Reranking scenario
- Include nested spans
- Include retrieval results
- Add varied metadata

**Acceptance Criteria:**
- ✅ All migrations run successfully
- ✅ Seed script populates database without errors
- ✅ Can query all 7 traces via SQL
- ✅ All foreign key relationships work
- ✅ JSONB fields contain valid JSON

---

### Phase 3: Trace Explorer ✅ COMPLETE

**Goal:** The main product UI works against seed data.

#### Task 3.1: API Routes - Projects
- `GET /projects` - List projects
- `POST /projects` - Create project
- `GET /projects/{id}` - Get project with stats
- Add temporary auth bypass for development

#### Task 3.2: API Routes - Traces
- `GET /projects/{id}/traces` - List with filters
- `GET /projects/{id}/traces/{tid}` - Get detail
- Implement pagination
- Implement filters: status, environment, date range, search
- Exclude heavy payloads from list endpoint

#### Task 3.3: Frontend API Client
- Create typed API client in `lib/api.ts`
- Add fetch wrappers for all endpoints
- Add error handling
- Create TypeScript types mirroring backend schemas

#### Task 3.4: TanStack Query Setup
- Install and configure React Query
- Create hooks:
  - `useProjects()`
  - `useProject(id)`
  - `useTraces(projectId, filters)`
  - `useTrace(projectId, traceId)`

#### Task 3.5: Project Overview Page
- Create `/projects/[id]/page.tsx`
- Display 4 metric cards:
  - Total traces
  - Average latency
  - Success rate
  - Total tokens
- Create 3 charts:
  - Requests over time (line chart)
  - Latency distribution (histogram)
  - Token usage over time (area chart)
- Add recent traces table (last 10)

#### Task 3.6: Trace Explorer Page
- Create `/projects/[id]/traces/page.tsx`
- Build `TraceTable` component with columns:
  - Status badge
  - Name
  - Duration
  - Started at
  - Environment
  - Actions (view button)
- Build `TraceFilters` component:
  - Status dropdown
  - Environment dropdown
  - Date range picker
  - Search input
- Implement pagination controls
- Add empty state component

**Acceptance Criteria:**
- ✅ Can view project overview with all 7 seed traces
- ✅ All 4 metric cards show correct calculations
- ✅ All 3 charts render with seed data
- ✅ Can filter traces by status, environment, date
- ✅ Search finds traces by name
- ✅ Pagination works correctly
- ✅ Clicking trace navigates to detail page

---

### Phase 4: RAG Inspectors 🚧 IN PROGRESS

**Goal:** Clicking a trace shows the full debugger experience.

#### Task 4.1: Trace Debugger Layout
- Create `/projects/[id]/traces/[tid]/page.tsx`
- Implement split-pane layout
- Add diagnostics panel at top
- Wire up trace detail API call

#### Task 4.2: Span Timeline Component
- Create `SpanTimeline` component
- Display spans in tree structure (handle parent_span_id)
- Show duration bars proportional to time
- Color-code by span type
- Highlight selected span
- Make spans clickable

#### Task 4.3: Span Inspector Dispatcher
- Create `SpanInspector` component
- Route to correct inspector based on span type
- Pass span data to inspector

#### Task 4.4: Inspector Components
- Create `RetrievalInspector`:
  - Display retrieval results table
  - Show rank, score, document, content preview
  - Highlight selected chunks
  - Show retrieval method
- Create `RerankingInspector`:
  - Display before/after rankings
  - Show score changes
  - Highlight rank changes
- Create `ContextInspector`:
  - Show assembled context
  - Display token count
  - Show chunk sources
- Create `PromptInspector`:
  - Display full prompt
  - Show token count
  - Syntax highlighting
- Create `LLMInspector`:
  - Show model, provider
  - Display input/output tokens
  - Show latency
  - Display parameters (temperature, max_tokens, etc.)

#### Task 4.5: Diagnostics Panel
- Create `DiagnosticsPanel` component
- Group by severity
- Show icon, title, description
- Make clickable to highlight relevant span
- Add severity badges

**Acceptance Criteria:**
- Trace debugger loads for all 7 seed traces
- Span timeline shows correct nesting
- Can click any span to view inspector
- All 5 inspector types render correctly
- Diagnostics panel shows (placeholder data for now)
- UI is responsive and performs well

---

### Phase 5: Ingestion + Auth

**Goal:** Real traces from real apps can be sent in.

#### Task 5.1: User Authentication
- Implement `POST /auth/register`
- Implement `POST /auth/login`
- Create JWT token generation and validation
- Create auth middleware/dependency
- Add password hashing (bcrypt)

#### Task 5.2: Frontend Auth Flow
- Create `/login` page
- Create `/register` page
- Implement auth state management
- Add token storage (httpOnly cookie or localStorage)
- Add protected route wrapper
- Add logout functionality

#### Task 5.3: API Key Management Backend
- Implement `POST /projects/{id}/api-keys`
  - Generate secure random key
  - Hash with SHA256
  - Return full key once
- Implement `GET /projects/{id}/api-keys`
- Implement `DELETE /projects/{id}/api-keys/{kid}`
- Create API key verification dependency

#### Task 5.4: API Key Management Frontend
- Create `/projects/[id]/settings/api-keys/page.tsx`
- Display API keys table
- Show key prefix, name, created_at, last_used_at
- Add "Create API Key" button and modal
- Show full key once in copy-able modal
- Add revoke button with confirmation

#### Task 5.5: Trace Ingestion Endpoint
- Implement `POST /v1/traces`
- Verify API key from Authorization header
- Validate payload with Pydantic
- Enforce size limit (5MB)
- Parse and store trace + spans + retrieval results
- Update api_key.last_used_at
- Return trace_id

#### Task 5.6: Ingestion Error Handling
- Handle invalid API key
- Handle malformed payload
- Handle oversized payload
- Handle database errors
- Log all ingestion attempts

**Acceptance Criteria:**
- Can register and login as user
- Auth protects all project routes
- Can create API key and see full key once
- API key list shows prefix only
- Can revoke API key
- `curl` can POST trace with valid API key
- Invalid API key returns 401
- Ingested trace appears in UI immediately
- All validation errors return clear messages

---

### Phase 6: Python SDK

**Goal:** `pip install raglens` and instrument a Python app in 10 lines.

#### Task 6.1: SDK Package Structure
- Create `packages/sdk-python/raglens/` directory
- Set up `pyproject.toml` with dependencies
- Create `__init__.py` with public API exports
- Configure package metadata

#### Task 6.2: Core Client
- Create `client.py`:
  - `RAGLens` class with `api_key` and `base_url`
  - HTTP client using `httpx`
  - `send_trace()` method
  - Error handling (never raise to caller)

#### Task 6.3: Trace Context Manager
- Create `trace.py`:
  - `Trace` class as context manager
  - Auto-capture `started_at`, `ended_at`, `duration_ms`
  - Exception handling sets status to error
  - Store spans list
  - Send on `__exit__`

#### Task 6.4: Span Context Manager
- Create `span.py`:
  - `Span` class as context manager
  - Support parent span for nesting
  - Auto-capture timing
  - Exception handling
  - Store in parent trace

#### Task 6.5: Helper Methods
- Create `helpers.py`:
  - `log_retrieval(span, results, method)`
  - `log_context(span, context, tokens)`
  - `log_prompt(span, prompt, tokens)`
  - `log_generation(span, response, tokens, model)`
- Each helper creates structured data in span attributes

#### Task 6.6: Serializers
- Create `serializers.py`:
  - Convert trace/span objects to API payload format
  - Handle datetime serialization
  - Handle exception serialization
  - Validate payload structure

#### Task 6.7: SDK Configuration
- Support `RAGLENS_API_KEY` env var
- Support `RAGLENS_BASE_URL` env var (default: localhost:8000)
- Support `RAGLENS_ENABLED` env var (disable SDK without code changes)

#### Task 6.8: SDK Tests
- Test trace context manager
- Test span context manager
- Test exception handling
- Test failed ingestion (network error)
- Test serialization
- Test nested spans
- Mock HTTP calls

**Acceptance Criteria:**
- SDK installs via pip
- Can create trace with context manager
- Can create nested spans
- Exceptions are caught and logged
- Failed ingestion logs warning but doesn't crash
- Helper methods populate span attributes correctly
- Payload matches API schema
- All tests pass

---

### Phase 7: Diagnostics

**Goal:** Every trace shows useful, deterministic diagnostic insights.

#### Task 7.1: Diagnostics Engine
- Create `diagnostics/engine.py`:
  - `DiagnosticEngine` class
  - `run_diagnostics(trace, spans)` method
  - Execute all rules
  - Store results in database

#### Task 7.2: Diagnostic Rules - Retrieval
- Create `diagnostics/rules/retrieval.py`:
  - `low_retrieval_confidence` rule (max score < 0.70)
  - `retrieval_waste` rule (retrieved/selected > 3)
  - `slow_retrieval` rule (duration > 500ms)

#### Task 7.3: Diagnostic Rules - Context
- Create `diagnostics/rules/context.py`:
  - `excessive_context` rule (> 80% of context window)
  - `low_context_utilization` rule (selected/retrieved < 40%)

#### Task 7.4: Diagnostic Rules - Performance
- Create `diagnostics/rules/latency.py`:
  - `slow_generation` rule (LLM% > 85%)
  - `failed_span` rule (status = error)

#### Task 7.5: Diagnostic Rules - Tokens
- Create `diagnostics/rules/tokens.py`:
  - `token_heavy_context` rule (context/input > 85%)

#### Task 7.6: Diagnostics Integration
- Run diagnostics engine on trace ingestion
- Store diagnostic results in database
- Link diagnostics to traces and spans

#### Task 7.7: Diagnostics UI Enhancement
- Wire up `DiagnosticsPanel` to real data
- Add click handler to highlight span
- Style by severity
- Add diagnostic icons
- Format evidence nicely

**Acceptance Criteria:**
- All 8 diagnostic rules implemented
- Diagnostics run automatically on ingestion
- Low-confidence seed trace shows warning
- Slow retrieval seed trace shows warning
- Failed trace shows error diagnostic
- UI highlights correct span when diagnostic clicked
- Evidence shows actual values vs thresholds
- Suggestions are actionable

---

### Phase 8: Demo App

**Goal:** End-to-end workflow is demonstrable without paid APIs.

#### Task 8.1: Demo App Setup
- Create `examples/basic-rag/` directory
- Set up Python environment
- Add requirements.txt
- Create README with setup instructions

#### Task 8.2: Demo Data
- Create sample document set (5-10 documents)
- Topics: general knowledge, no sensitive content
- Store as text files or JSON

#### Task 8.3: RAG Pipeline
- Implement simple vector search (local embeddings)
- Use sentence-transformers or similar
- Implement basic retrieval (top-K)
- Use local LLM or mock LLM responses
- Implement context assembly
- Implement answer generation

#### Task 8.4: RAGLens Instrumentation
- Instrument with RAGLens SDK
- Trace the full pipeline
- Log retrieval results
- Log context assembly
- Log prompt
- Log LLM call
- Log final response

#### Task 8.5: Demo Script
- Create `app.py` with sample questions
- Run multiple scenarios:
  - Successful retrieval
  - No relevant results
  - Multiple document retrieval
- Print trace URL after each run

#### Task 8.6: Documentation
- Create demo README
- Document setup steps
- Document how to view traces
- Add troubleshooting section

**Acceptance Criteria:**
- `python examples/basic-rag/app.py` runs without errors
- Traces appear in RAGLens dashboard
- All span types present in trace
- Retrieval inspector shows documents
- Context inspector shows assembled context
- Prompt inspector shows full prompt
- LLM inspector shows response
- Diagnostics show relevant insights
- Demo works without any paid API keys

---

## Testing Strategy

### Backend Tests
- Unit tests for repositories
- Unit tests for services
- Unit tests for diagnostic rules
- Integration tests for API endpoints
- Test auth flows
- Test payload validation

### Frontend Tests
- Component tests for inspectors
- Integration tests for trace explorer
- End-to-end tests for critical flows:
  - Register → Create project → View traces
  - Create API key → Ingest trace → View in debugger

### SDK Tests
- Unit tests for context managers
- Unit tests for serializers
- Integration tests against real API
- Test error handling
- Test nested spans

---

## Deployment Considerations

### Local Development
- `docker compose up` for all services
- Hot reload for frontend and backend
- Seed data auto-populated

### Environment Variables
Required:
- `DATABASE_URL`
- `SECRET_KEY`
- `CORS_ORIGINS`

Optional:
- `MAX_TRACE_PAYLOAD_BYTES`
- `LOG_LEVEL`
- `NEXT_PUBLIC_API_URL`

### Database Migrations
- Run `alembic upgrade head` on deployment
- Keep migrations in version control
- Test rollback procedures

---

## Success Criteria

### MVP Complete When:
1. ✅ User can register and login
2. ✅ User can create project
3. ✅ User can create API key
4. ✅ Python SDK can send trace via API
5. ✅ Trace appears in trace explorer
6. ✅ Can filter traces by status, environment, date
7. ✅ Can click trace to view debugger
8. ✅ Span timeline shows nested spans
9. ✅ Can click span to view inspector
10. ✅ Retrieval inspector shows documents with scores
11. ✅ Context inspector shows assembled context
12. ✅ Prompt inspector shows full prompt
13. ✅ LLM inspector shows model and tokens
14. ✅ Diagnostics panel shows issues
15. ✅ Demo app runs and traces appear in UI
16. ✅ All 7 seed scenarios work in UI

### Quality Gates
- No critical bugs
- All planned tests pass
- Documentation complete
- Demo runs without manual intervention
- Performance meets NFRs

---

## Future Enhancements (Out of Scope for MVP)

- Playground for testing prompts
- Evaluations framework
- OpenTelemetry compatibility
- LangChain/LlamaIndex auto-instrumentation
- LLM-based semantic diagnostics
- Team collaboration features
- SSO and RBAC
- Kubernetes deployment configs
- Billing and usage tracking
- Public API documentation site

---

## References

- Architecture Document: #[[file:architecture.md]]
- README: #[[file:README.md]]
