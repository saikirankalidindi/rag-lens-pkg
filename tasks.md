# Build RAGLens — RAG Pipeline Debugging Platform

You are building the actual MVP of **RAGLens**, a developer-first debugging and observability platform for Retrieval-Augmented Generation (RAG) applications.

This is NOT a landing page.

Build a functional developer application where engineers can instrument a RAG pipeline, send traces to RAGLens, and inspect exactly what happened during each RAG request.

The core mental model is:

> Chrome DevTools for RAG pipelines.

The primary workflow is:

```text
RAG Application
      ↓
RAGLens SDK / API
      ↓
Trace Ingestion
      ↓
Trace Storage
      ↓
RAGLens Dashboard
      ↓
Developer inspects:
Query
Retrieval
Reranking
Context
Prompt
LLM
Response

```

---

# 1. MVP Scope

For V1, implement these capabilities:

1. Projects
2. Trace ingestion
3. Trace explorer
4. Trace detail/debugger
5. Retrieval inspection
6. Reranking inspection
7. Context inspection
8. Prompt inspection
9. LLM generation inspection
10. Token / latency / cost metrics
11. Basic automated diagnostics
12. Python SDK
13. API key authentication
14. Search/filter traces

Do NOT build complex enterprise functionality yet.

Do NOT implement:

- billing
- SSO
- RBAC
- enterprise organizations
- Kubernetes deployment
- advanced evaluation framework
- automatic optimization
- complex agent tracing
- full OpenTelemetry compatibility
- production-scale distributed infrastructure

Architect the code so these can be added later.

---

# 2. Recommended Architecture

Use a monorepo.

```text
raglens/
│
├── apps/
│   ├── web/
│   └── api/
│
├── packages/
│   └── sdk-python/
│
├── docker/
│
├── docs/
│
├── docker-compose.yml
├── README.md
└── .env.example

```

---

# 3. Frontend

Use:

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query
- Zod
- Lucide icons

Use the existing RAGLens landing-page design language.

The product application should feel like:

- Linear
- Sentry
- Grafana
- Vercel
- browser DevTools

Use a dark-first developer interface.

Prioritize information density and readability over decorative UI.

---

# 4. Backend

Use:

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL

Use asynchronous FastAPI endpoints where appropriate.

Structure backend code cleanly:

```text
apps/api/
│
├── app/
│   ├── main.py
│   ├── config.py
│
│   ├── api/
│   │   ├── projects.py
│   │   ├── traces.py
│   │   ├── ingestion.py
│   │   └── api_keys.py
│   │
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── repositories/
│   ├── diagnostics/
│   └── database/
│
├── migrations/
└── tests/

```

Keep API routes thin.

Business logic belongs in services.

Database access belongs in repositories.

---

# 5. Core Domain Model

The most important abstraction in RAGLens is a:

**Trace**

One user request produces one trace.

Example:

```text
User Question
      ↓
Trace
      ├── Query
      ├── Query Rewrite
      ├── Retrieval
      ├── Reranking
      ├── Context
      ├── Prompt
      ├── Generation
      └── Response

```

A trace contains multiple spans.

Create a generic span model so the architecture isn't permanently hardcoded to one RAG implementation.

---

# 6. Trace Model

A trace should contain approximately:

```json
{
  "id": "trace_...",
  "project_id": "project_...",
  "name": "answer_question",
  "session_id": null,
  "user_id": null,

  "started_at": "...",
  "ended_at": "...",

  "duration_ms": 2840,

  "status": "success",

  "input": {
    "query": "What is our vacation carryover policy?"
  },

  "output": {
    "answer": "..."
  },

  "metrics": {
    "input_tokens": 6885,
    "output_tokens": 384,
    "total_tokens": 7269,
    "estimated_cost": 0.014
  },

  "metadata": {
    "environment": "development"
  }
}

```

---

# 7. Span Model

Every important operation inside the trace should be represented as a span.

Supported span types:

```text
query
query_rewrite
retrieval
reranking
context
prompt
llm
response
custom

```

Example:

```json
{
  "id": "span_...",
  "trace_id": "trace_...",
  "parent_span_id": null,

  "type": "retrieval",
  "name": "vector_search",

  "started_at": "...",
  "ended_at": "...",

  "duration_ms": 312,

  "input": {},
  "output": {},

  "attributes": {},

  "status": "success"
}

```

Support parent-child spans.

This is important for future pipelines like:

```text
retrieval
├── query_embedding
├── vector_search
├── keyword_search
└── merge_results

```

---

# 8. Retrieval Data Model

Retrieval spans need specialized information.

Example:

```json
{
  "query": "vacation carryover policy",

  "retriever": {
    "type": "vector",
    "top_k": 5,
    "similarity_threshold": 0.7
  },

  "results": [
    {
      "rank": 1,
      "chunk_id": "chunk_123",
      "document_id": "doc_456",

      "document_name": "Employee Handbook.pdf",

      "content": "...",

      "score": 0.9421,

      "metadata": {
        "page": 42,
        "department": "HR",
        "year": 2026
      },

      "selected": true
    }
  ]
}

```

Do NOT assume every retriever uses cosine similarity.

Allow:

```text
score
distance
retrieval_method

```

to remain extensible.

---

# 9. Reranking

Store:

```text
Original rank
New rank
Original score
Reranker score
Selected

```

The UI should make movement obvious.

Example:

```text
Before      After

#1          #3
#2          #1 ↑
#3          #2 ↑
#4          #4

```

---

# 10. Context Data

The developer needs to know what ACTUALLY reached the model.

Store:

```json
{
  "available_chunks": 10,
  "selected_chunks": 5,
  "token_count": 4821,

  "chunks": [
    {
      "chunk_id": "...",
      "content": "...",
      "position": 1,
      "tokens": 387,
      "truncated": false
    }
  ]
}

```

Distinguish:

```text
Retrieved
vs
Reranked
vs
Selected
vs
Final context

```

This distinction is fundamental to RAGLens.

---

# 11. Prompt Data

Capture:

```text
System prompt
User message
Conversation history
Retrieved context
Template variables
Final rendered prompt

```

Store token counts when available.

Never expose secrets such as provider API keys.

---

# 12. LLM Generation

Capture:

```json
{
  "provider": "openai",
  "model": "...",

  "temperature": 0.2,

  "input_tokens": 6885,
  "output_tokens": 384,

  "latency_ms": 2310,

  "estimated_cost": 0.014,

  "finish_reason": "stop"
}

```

Do not hardcode RAGLens around one provider.

Design adapters/interfaces for multiple model providers.

---

# 13. Dashboard Layout

After authentication, create an application shell.

Left sidebar:

```text
RAGLens

PROJECT
My RAG App

────────────

Overview
Traces
Playground      [future]
Evaluations     [future]

────────────

Settings
API Keys

```

Bottom:

```text
Documentation
GitHub

```

---

# 14. Overview Page

Route:

```text
/projects/{projectId}

```

Show:

```text
Requests

1,284
↑ 12%

Failure Rate

7.2%

Avg Latency

1.84s

Avg Tokens

6,291

```

Then charts:

```text
Requests over time

Latency over time

Failures over time

```

Then:

```text
Recent traces

```

Columns:

```text
Trace
Query
Status
Duration
Tokens
Cost
Timestamp

```

Clicking a row opens the trace debugger.

---

# 15. Trace Explorer

Route:

```text
/projects/{projectId}/traces

```

This is one of the main product pages.

Create a dense developer-oriented table.

Columns:

```text
Status

Query

Duration

Retrieval

Model

Tokens

Cost

Time

```

Support filters:

```text
Search

Status
Success
Warning
Error

Environment
Development
Staging
Production

Model

Duration

Date range

```

Click any trace to inspect it.

---

# 16. Trace Debugger

Route:

```text
/projects/{projectId}/traces/{traceId}

```

This is THE MOST IMPORTANT SCREEN.

Use approximately:

```text
┌───────────────────────────────────────────────────────────┐
│ Trace                                                     │
│                                                           │
│ "What is our vacation carryover policy?"                  │
│                                                           │
│ ✓ Success    2.84s    7,269 tokens    $0.014             │
├───────────────────────┬───────────────────────────────────┤
│                       │                                   │
│ TRACE                 │ INSPECTOR                         │
│                       │                                   │
│ ● Query          4ms  │ Selected span details             │
│ │                     │                                   │
│ ● Query Rewrite 28ms  │                                   │
│ │                     │                                   │
│ ● Retrieval     312ms │                                   │
│ │                     │                                   │
│ ● Reranking     184ms │                                   │
│ │                     │                                   │
│ ● Context        11ms │                                   │
│ │                     │                                   │
│ ● Prompt          3ms │                                   │
│ │                     │                                   │
│ ● LLM           2.31s │                                   │
│ │                     │                                   │
│ ● Response        1ms │                                   │
│                       │                                   │
└───────────────────────┴───────────────────────────────────┘

```

Selecting a span changes the inspector without navigating away.

Think:

**Chrome DevTools / distributed tracing UI.**

---

# 17. Retrieval Inspector

When Retrieval is selected, show:

```text
Retrieval

Vector Search

312 ms
top_k = 5
threshold = 0.70

```

Then:

```text
#1 Employee Handbook.pdf

Score
0.9421

Page
42

387 tokens

SELECTED

```

Clicking a result opens the chunk.

Display:

```text
CONTENT

Employees may carry forward...

METADATA

document_id
chunk_id
page
department
year

RETRIEVAL

rank
score
method

```

Allow users to compare retrieved chunks.

---

# 18. Reranking Inspector

Show rank movement visually.

Example:

```text
Employee Handbook

Retrieval rank     #3
Reranked rank      #1 ↑2

Retriever score    0.81
Reranker score     0.96

```

Make ranking changes easy to understand.

---

# 19. Context Inspector

Create three tabs:

```text
Selected
Excluded
Final Context

```

Show:

```text
5 / 10 chunks selected

4,821 tokens

70% of retrieved content retained

```

Display each context chunk in order.

Clearly indicate:

```text
Included
Excluded
Truncated

```

---

# 20. Prompt Inspector

Use tabs:

```text
Rendered Prompt
Messages
Variables
Tokens

```

Show syntax-highlighted prompt content.

For chat-based APIs display:

```text
SYSTEM

...

USER

...

ASSISTANT

...

```

Token visualization:

```text
System          712
Context       4,821
History       1,204
Question        148

─────────────────

Total          6,885

```

---

# 21. LLM Inspector

Show:

```text
Provider
OpenAI

Model
...

Latency
2.31s

Input tokens
6,885

Output tokens
384

Cost
$0.014

Temperature
0.2

Finish reason
stop

```

Then display:

```text
INPUT

...

OUTPUT

...

```

---

# 22. Diagnostics Engine

Implement a RULE-BASED diagnostics engine first.

Do NOT use another LLM for diagnostics yet.

Diagnostics should be deterministic and explainable.

Create:

```text
apps/api/app/diagnostics/

```

Implement rules such as:

### Low retrieval confidence

If the highest retrieval score is below a configured threshold:

```text
WARNING

Low retrieval confidence

The highest-ranked retrieved chunk scored only 0.54.

Investigate:
• embedding model
• query formulation
• document coverage

```

### Excessive context

If context consumes a large percentage of the configured model context window:

```text
WARNING

Large context

Retrieved context consumes 82% of the available context window.

```

### Retrieval waste

If many chunks were retrieved but few used:

```text
INFO

Low context utilization

20 chunks retrieved
3 chunks used

```

### Slow retrieval

```text
WARNING

Retrieval latency is unusually high.

842ms

```

### Slow generation

```text
WARNING

LLM generation accounts for 91% of request latency.

```

### Token-heavy request

```text
WARNING

Context accounts for 87% of input tokens.

```

Each diagnostic should contain:

```json
{
  "id": "...",
  "severity": "warning",
  "category": "retrieval",
  "title": "Low retrieval confidence",
  "description": "...",
  "evidence": {},
  "suggestions": []
}

```

Do not pretend these rules can determine semantic correctness.

Label diagnostics appropriately.

---

# 23. Diagnostics UI

At the top of trace details show:

```text
Diagnostics

2 warnings
1 insight

```

Example:

```text
⚠ LOW RETRIEVAL CONFIDENCE

Highest retrieval score: 0.54

Potential causes:
Embedding mismatch
Poor query representation
Missing source material

────────────────────────

⚠ HIGH CONTEXT USAGE

82% of model context consumed.

────────────────────────

ⓘ LATENCY

LLM generation accounts for
91% of total latency.

```

Clicking a diagnostic should highlight the relevant trace span.

---

# 24. Trace Ingestion API

Create an endpoint such as:

```text
POST /v1/traces

```

Authentication:

```text
Authorization: Bearer <project_api_key>

```

Support submitting complete traces initially.

Also architect toward eventual streaming/span ingestion.

Validate input with Pydantic.

Return:

```json
{
  "trace_id": "trace_..."
}

```

---

# 25. API Keys

Projects should have API keys.

Format similar to:

```text
rgl_live_...
rgl_test_...

```

Never store raw API keys.

Store:

```text
key_prefix
key_hash
created_at
last_used_at
revoked_at

```

Use a cryptographically secure random key.

Only show the complete key ONCE after creation.

---

# 26. Python SDK

Create:

```text
packages/sdk-python/

```

Package name:

```text
raglens

```

Initial usage:

```python
from raglens import RAGLens

raglens = RAGLens(
    api_key="rgl_test_..."
)

```

Support:

```python
with raglens.trace(
    name="answer_question",
    input={"query": question}
) as trace:

    with trace.span(
        type="retrieval",
        name="vector_search"
    ) as span:

        documents = retriever.invoke(question)

        span.set_output({
            "results": [...]
        })

```

Then:

```python
with trace.span(
    type="llm",
    name="generate"
) as span:

    response = llm.invoke(prompt)

```

The SDK should automatically capture:

```text
start timestamp
end timestamp
duration
exceptions
status

```

The SDK should never crash the host application if RAGLens ingestion fails.

Observability must fail gracefully.

---

# 27. Convenience API

Because manually instrumenting everything is tedious, provide helpers.

Example:

```python
trace.log_retrieval(
    query=query,
    results=documents,
    top_k=5
)

```

And:

```python
trace.log_context(...)
trace.log_prompt(...)
trace.log_generation(...)
trace.set_output(...)

```

Manual instrumentation is acceptable for MVP.

Automatic framework integrations come later.

---

# 28. Demo RAG Application

Create a small example application:

```text
examples/basic-rag/

```

Use a simple local RAG implementation.

It should demonstrate:

```text
Question
↓
Retrieval
↓
Context
↓
Prompt
↓
LLM
↓
Answer

```

Instrument the application using the RAGLens SDK.

Include a mode that does not require paid external APIs so the full tracing workflow can be demonstrated locally.

---

# 29. Seed Data

Create realistic seed traces.

Do not use lorem ipsum.

Include scenarios:

### Successful RAG

Good retrieval → good context → answer.

### Poor retrieval

Low similarity results.

### Excessive context

Too many chunks.

### Slow retrieval

Simulated high retrieval latency.

### Slow LLM

Generation dominates latency.

### Failed request

Provider exception.

### Reranking

Documents change ranking.

These traces should make the dashboard useful immediately after setup.

---

# 30. Database

Create normalized tables approximately for:

```text
users
projects
api_keys
traces
spans
retrieval_results
diagnostics

```

Use JSONB strategically for flexible provider-specific metadata.

Do not put absolutely everything into JSON.

Core searchable/filterable properties should be real columns.

Create indexes for:

```text
project_id
trace_id
created_at
status
span_type

```

---

# 31. Authentication

For MVP, implement straightforward user authentication.

Keep user authentication separate from project API-key authentication.

Browser:

```text
User authentication

```

Trace ingestion:

```text
Project API key

```

Do not expose ingestion keys in frontend client bundles.

---

# 32. Security

Important requirements:

- Never log API keys.
- Hash project API keys.
- Sanitize sensitive error messages.
- Validate payload sizes.
- Add ingestion rate-limit hooks.
- Avoid arbitrary code execution.
- Do not render raw HTML from trace payloads.
- Escape user-provided trace data.
- Add configurable maximum trace payload size.
- Add CORS configuration through environment variables.
- Do not use wildcard CORS in production configuration.

---

# 33. Privacy

Design trace ingestion so future users can disable sensitive fields.

Architect support for:

```text
capture_query
capture_context
capture_prompt
capture_response

```

For MVP these can be project configuration fields.

Eventually this enables metadata-only tracing.

---

# 34. Error Handling

Use consistent API errors:

```json
{
  "error": {
    "code": "TRACE_NOT_FOUND",
    "message": "Trace not found"
  }
}

```

Frontend should provide useful:

- loading states
- empty states
- error states
- retry actions

Do not silently swallow product errors.

The SDK itself should fail gracefully and optionally log debug information.

---

# 35. Local Development

The entire product should run locally with:

```bash
docker compose up

```

At minimum start:

```text
PostgreSQL
RAGLens API
RAGLens Web

```

Provide:

```text
.env.example

```

with documented environment variables.

---

# 36. README

Create a professional README.

Include:

```text
RAGLens

What it is

Architecture

Quick Start

Installation

Running locally

Creating a project

Creating an API key

Sending your first trace

Using the Python SDK

Viewing the trace

Development

Testing

Repository structure

```

A new developer should be able to clone the repository and understand how to run the project.

---

# 37. Testing

Backend:

Use pytest.

Test:

```text
trace creation
span creation
API key validation
invalid API key
diagnostics
project isolation
trace retrieval
trace filtering

```

SDK:

Test:

```text
trace context manager
span context manager
exception handling
failed ingestion
serialization

```

Frontend:

Add tests for critical components and flows where practical.

---

# 38. Developer UX

The first-run experience is extremely important.

When a project contains no traces, don't just display:

```text
No traces.

```

Show:

```text
Send your first RAG trace

1. Install the SDK

pip install raglens

2. Configure

from raglens import RAGLens

raglens = RAGLens(
    api_key="..."
)

3. Instrument your pipeline

...

4. Run your application

5. Your trace will appear here automatically.

```

Provide copy buttons.

---

# 39. Performance

Do not prematurely build for billions of traces.

However:

- paginate trace lists
- use database indexes
- avoid N+1 queries
- lazy-load large span content where appropriate
- don't load full prompts/context for the trace listing
- keep list endpoints lightweight

The trace detail endpoint can return richer information.

---

# 40. Architecture Principle

RAGLens must NOT assume a pipeline always looks like:

```text
retrieval → LLM

```

A real pipeline may look like:

```text
Query
 ↓
Rewrite
 ↓
┌──────────────┐
│              │
Vector       BM25
Search       Search
│              │
└──────┬───────┘
       ↓
Merge
       ↓
Rerank
       ↓
Filter
       ↓
Context
       ↓
LLM

```

Therefore:

**Trace + nested spans must remain the fundamental architecture.**

The RAG-specific inspectors should interpret those spans.

---

# 41. Product Terminology

Use consistently:

```text
Project
Trace
Span
Retrieval
Retrieved Chunk
Reranking
Context
Prompt
Generation
Diagnostic

```

Avoid introducing unnecessary terminology.

---

# 42. MVP Success Criteria

The MVP is successful when a developer can:

```text
1. Start RAGLens locally

2. Create a project

3. Generate an API key

4. pip install the RAGLens SDK

5. Instrument a Python RAG application

6. Ask the RAG application a question

7. Open RAGLens

8. See the request appear as a trace

9. Open the trace

10. Inspect retrieval results

11. Inspect ranking

12. Inspect selected context

13. Inspect the final prompt

14. Inspect model/token/latency information

15. Inspect the generated answer

16. See useful diagnostics explaining suspicious pipeline behavior

```

If this workflow works end-to-end, we have a legitimate RAGLens MVP.

---

# 43. Implementation Order

Do NOT attempt everything simultaneously.

Implement in this order.

## Phase 1 — Foundation

Create:

- monorepo
- FastAPI
- Next.js
- PostgreSQL
- Docker Compose
- configuration
- database connection
- migrations
- base UI shell

Verify everything runs.

## Phase 2 — Core Domain

Implement:

- projects
- traces
- spans
- retrieval results
- database models
- schemas
- repositories
- services

Add seed data.

## Phase 3 — Trace Explorer

Implement:

- overview
- traces table
- filtering
- trace detail page
- trace timeline

Use seeded traces first.

## Phase 4 — RAG Inspectors

Implement:

- retrieval inspector
- reranking inspector
- context inspector
- prompt inspector
- LLM inspector

## Phase 5 — Ingestion

Implement:

- API keys
- trace ingestion API
- authentication
- validation

Test with curl before building the SDK.

## Phase 6 — Python SDK

Implement:

- RAGLens client
- Trace
- Span
- context managers
- HTTP ingestion
- graceful failure

## Phase 7 — Diagnostics

Implement deterministic diagnostics and connect them to the trace UI.

## Phase 8 — Demo

Build the example RAG application and verify the complete workflow.

---

# 44. Important Engineering Rules

Do not create fake functionality merely to make the UI look complete.

If something isn't implemented, clearly mark it as:

```text
Coming soon

```

Prefer working functionality over feature quantity.

Avoid giant files.

Use reusable components.

Use typed contracts between frontend and backend.

Keep provider-specific logic behind adapters.

Add useful logging.

Use migrations.

Do not put secrets in source code.

Do not create unnecessary abstractions.

Do not overengineer the MVP.

---

# 45. Before Coding

First inspect the existing repository.

The RAGLens landing page already exists.

Do NOT replace it.

Determine:

- existing framework
- package manager
- project structure
- styling system
- reusable components
- existing routes
- environment configuration

Preserve the landing page.

Then present a concise implementation plan and proposed repository changes.

After that, start implementing **Phase 1**.

Do not generate the entire product as a giant mockup in one pass.

Build it as real software, phase by phase, and verify each phase before proceeding.

The most important product principle throughout development is:

> **For every RAG answer, RAGLens should help the developer answer three questions: What happened? Why did it happen? Where should I investigate?**

