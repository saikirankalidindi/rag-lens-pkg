# BookMyShowBot — RAGLens Test & Evaluation Project

A complete, self-contained RAG assistant test project designed to instrument and evaluate RAG pipelines using **RAGLens**.

This project simulates a customer service AI assistant for **BookMyShow** answering questions about movie tickets, IMAX/4DX specifications, cancellation and refund policies, food & beverage rules, and credit card offers.

---

## ⚡ Quickstart

From the repository root:

```bash
# 1. Activate the environment (with raglens installed)
source .venv/bin/activate

# 2. Run all evaluation scenarios to populate the dashboard
python examples/bookmyshow-bot/app.py

# 3. Refresh your browser at:
# http://localhost:3000/projects/project_aaw3236s8tx5qsr1gi0wefnyj7/traces
```

---

## 🎯 Evaluation Scenarios

Run individual scenarios to see how RAGLens evaluates different RAG pipeline behaviors:

### 1. Healthy RAG Pipeline (Baseline)
```bash
python examples/bookmyshow-bot/app.py --scenario healthy
```
- **Query**: *"Can I cancel my movie ticket and get a refund on BookMyShow?"*
- **What it tests**: High similarity retrieval score (>0.90), balanced context window usage, normal latency waterfall.
- **RAGLens Evaluation**: Status `SUCCESS`, 0 diagnostic warnings.

### 2. Low Retrieval Confidence (Out-of-Domain Detection)
```bash
python examples/bookmyshow-bot/app.py --scenario low-confidence
```
- **Query**: *"How do I renew my driver's license or apply for an income tax refund?"*
- **What it tests**: Semantic gap when indexed documents don't cover the query.
- **RAGLens Evaluation**: Triggers `low_retrieval_confidence` (Warning: top similarity score < 0.70) with actionable advice to review query wording and embedding alignment.

### 3. Retrieval Waste & Low Context Utilization
```bash
python examples/bookmyshow-bot/app.py --scenario waste
```
- **Query**: *"Are outside snacks and water bottles allowed into the cinema hall?"*
- **What it tests**: High `top_k` retrieval where 10 chunks are fetched but only 1 is selected for generation.
- **RAGLens Evaluation**: Triggers `retrieval_waste` (Info: retrieved/selected > 3.0) and `low_context_utilization` (Info: < 40% chunks selected).

### 4. Excessive Context (Context Window Bloat)
```bash
python examples/bookmyshow-bot/app.py --scenario context-overflow
```
- **Query**: *"List all cinema amenities, IMAX laser specifications, terms of service, and credit card offers."*
- **What it tests**: Bloated context window pushing >80% capacity of the LLM context limit (lost-in-the-middle risk).
- **RAGLens Evaluation**: Triggers `excessive_context` (Warning: context tokens / max_tokens > 80%) and `token_heavy_context`.

### 5. LLM Generation Latency Bottleneck
```bash
python examples/bookmyshow-bot/app.py --scenario slow-generation
```
- **Query**: *"Explain in deep technical detail the difference between IMAX with Laser, 4DX motion, and standard 2D projection."*
- **What it tests**: Generation time disproportionately dominating total pipeline duration.
- **RAGLens Evaluation**: Triggers `slow_generation` (Info: LLM duration / total duration > 85%).

### 6. Slow Vector Retrieval Latency
```bash
python examples/bookmyshow-bot/app.py --scenario slow-retrieval
```
- **Query**: *"Find all IMAX 3D showtimes for Oppenheimer in South Bengaluru theaters."*
- **What it tests**: Vector database or network latency bottleneck during chunk retrieval.
- **RAGLens Evaluation**: Triggers `slow_retrieval` (Warning: retrieval duration > 500ms).

### 7. Span Failure & Pipeline Resilience
```bash
python examples/bookmyshow-bot/app.py --scenario error
```
- **Query**: *"Check live seat inventory for Oppenheimer at PVR Forum Koramangala 09:15 PM show."*
- **What it tests**: External partner API failure during a sub-operation.
- **RAGLens Evaluation**: Trace status `ERROR`, red error indicator, and `failed_span` diagnostic with exception stack trace.

---

## 💬 Ask Custom Questions

You can test any question interactively:

```bash
python examples/bookmyshow-bot/app.py --query "What are the showtimes for Kalki 2898 AD in INOX Garuda Mall?"
```

---

## 🔬 How RAGLens Evaluates RAG Systems

RAGLens acts as **Chrome DevTools for RAG pipelines**, answering three core questions for every user interaction:
1. **What happened?** (Complete request timeline, span waterfall, and token/cost metrics)
2. **Why did it happen?** (Granular inspection of every intermediate artifact)
3. **Where should I investigate?** (Automated rule-based diagnostic evaluation engine)

### 1. Span Waterfall & Latency Breakdown
Instead of treating RAG as a black box, RAGLens captures every stage as a typed span:
- `query`: Query parsing and intent classification
- `query_rewrite`: HyDE or search term expansion
- `retrieval`: Vector/keyword chunk search with similarity scores
- `reranking`: Cross-encoder score adjustment and rank shifts
- `context`: Chunk concatenation, deduplication, and token budgeting
- `prompt`: Structured system/user chat message construction
- `llm`: Token usage, throughput (tokens/sec), generation latency, and dollar cost

### 2. Dedicated RAG Inspectors
- **Retrieval Inspector**: Visualizes retrieved chunks, similarity scores, rank, whether chunks were selected for context, and raw chunk content.
- **Reranking Inspector**: Visualizes before/after rank delta (promotions, demotions, unchanged), score deltas, and reranker models.
- **Context Inspector**: Tracks context window utilization, chunk boundary assembly, tokens per chunk, and alerts on token bloat (>80% utilization).
- **Prompt Inspector**: Breaks down role-based messages (system, user, assistant), prompt variables, and token counts.
- **LLM Inspector**: Measures generation latency, throughput (tokens/sec), cost, and model hyperparameters.

### 3. Automated Diagnostic Engine (Runtime Deterministic Evaluation)
Upon trace ingestion, RAGLens evaluates traces against 8 deterministic diagnostic rules:
| Diagnostic Rule | Severity | Trigger Condition | RAG Evaluation Dimension |
|---|---|---|---|
| `low_retrieval_confidence` | Warning | Top retrieval score < 0.70 | Knowledge base coverage & semantic relevance |
| `retrieval_waste` | Info | Retrieved / Selected ratio > 3.0 | Top-k retrieval efficiency |
| `low_context_utilization` | Info | Selected / Retrieved ratio < 0.40 | Context filtering efficiency |
| `excessive_context` | Warning | Context tokens / Max tokens > 0.80 | Context window budgeting & lost-in-the-middle risk |
| `token_heavy_context` | Warning | Context tokens / Input tokens > 0.85 | Prompt payload efficiency |
| `slow_retrieval` | Warning | Retrieval duration > 500ms | Vector search infrastructure performance |
| `slow_generation` | Info | LLM duration / Total duration > 0.85 | Pipeline latency bottleneck distribution |
| `failed_span` | Error | Any span throws an unhandled error | System resilience & error tracing |

### 4. Current State vs Future Roadmap
- **Today (Live in App)**: Full span tracing, 5 rich inspectors, and automated deterministic diagnostic evaluations run on every trace in real time.
- **Future Roadmap ("Evaluations (Soon)" in sidebar)**: Dedicated offline evaluation suites, golden test datasets, and LLM-as-a-judge metrics (Faithfulness, Context Relevance, Answer Relevance).
