"""
Seed data — creates a demo user, project, API key, and 7 realistic traces.

Scenarios:
  1. Successful RAG          — good retrieval, good context, correct answer
  2. Poor retrieval          — low similarity scores, vague answer
  3. Excessive context       — too many chunks, high token usage
  4. Slow retrieval          — retrieval latency dominates
  5. Slow LLM                — generation dominates latency
  6. Failed request          — provider exception
  7. Reranking               — retrieval rank changes significantly after reranking

Run once on first boot.  Safe to call multiple times — checks for existence first.
"""
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import hash_password
from app.models.api_key import ApiKey
from app.models.diagnostic import Diagnostic
from app.models.project import Project
from app.models.retrieval_result import RetrievalResult
from app.models.span import Span
from app.models.trace import Trace
from app.models.user import User
from app.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

# ── Seed constants ─────────────────────────────────────────────────────────────
SEED_EMAIL = "demo@raglens.dev"
SEED_PASSWORD = "raglens-demo"
SEED_PROJECT_NAME = "HR Knowledge Base"
SEED_API_KEY_RAW = "rgl_test_seed_key_demo_000000000"

_NOW = datetime.now(timezone.utc)


def _ago(**kwargs) -> datetime:
    return _NOW - timedelta(**kwargs)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mk_span(
    trace_id: str,
    type_: str,
    name: str,
    start_offset_ms: int,
    duration_ms: int,
    *,
    status: str = "success",
    input_: dict | None = None,
    output: dict | None = None,
    attributes: dict | None = None,
    parent_span_id: str | None = None,
) -> Span:
    started = _NOW - timedelta(hours=1) + timedelta(milliseconds=start_offset_ms)
    return Span(
        trace_id=trace_id,
        parent_span_id=parent_span_id,
        type=type_,
        name=name,
        started_at=started,
        ended_at=started + timedelta(milliseconds=duration_ms),
        duration_ms=duration_ms,
        status=status,
        input=input_,
        output=output,
        attributes=attributes,
    )


def _mk_retrieval_result(
    span_id: str,
    rank: int,
    doc_name: str,
    content: str,
    score: float,
    selected: bool = True,
    reranked_rank: int | None = None,
    reranker_score: float | None = None,
    metadata: dict | None = None,
) -> RetrievalResult:
    return RetrievalResult(
        span_id=span_id,
        rank=rank,
        chunk_id=f"chunk_{doc_name.lower().replace(' ', '_')}_{rank}",
        document_id=f"doc_{rank:03d}",
        document_name=doc_name,
        content=content,
        score=score,
        retrieval_method="cosine",
        selected=selected,
        reranked_rank=reranked_rank,
        reranker_score=reranker_score,
        metadata_=metadata or {"page": rank * 3, "department": "HR"},
    )


# ── Trace builders ────────────────────────────────────────────────────────────

async def _seed_trace_success(db: AsyncSession, project_id: str) -> None:
    """Scenario 1: Good retrieval → good context → correct answer."""
    t_start = _ago(hours=2)
    trace = Trace(
        project_id=project_id,
        name="answer_question",
        started_at=t_start,
        ended_at=t_start + timedelta(milliseconds=2840),
        duration_ms=2840,
        status="success",
        input={"query": "What is our vacation carryover policy?"},
        output={
            "answer": (
                "Employees may carry forward up to 5 unused vacation days to the following "
                "year. Days must be used by March 31st or they are forfeited. Employees on "
                "leave of absence may carry additional days with manager approval."
            )
        },
        metrics={
            "input_tokens": 6885,
            "output_tokens": 384,
            "total_tokens": 7269,
            "estimated_cost": 0.014,
            "context_tokens": 4821,
        },
        metadata_={"environment": "development", "model": "gpt-4o-mini"},
    )
    db.add(trace)
    await db.flush()

    spans = [
        _mk_span(trace.id, "query", "parse_query", 0, 4,
                 input_={"query": "What is our vacation carryover policy?"},
                 output={"normalized_query": "vacation carryover policy"}),
        _mk_span(trace.id, "query_rewrite", "rewrite_query", 4, 28,
                 input_={"query": "vacation carryover policy"},
                 output={"rewritten_query": "employee vacation days carry forward policy limit"}),
        _mk_span(trace.id, "retrieval", "vector_search", 32, 312,
                 attributes={"top_k": 5, "similarity_threshold": 0.70, "index": "hr-docs"}),
        _mk_span(trace.id, "reranking", "cross_encoder_rerank", 344, 184,
                 attributes={"model": "cross-encoder/ms-marco-MiniLM-L-6-v2", "top_n": 3}),
        _mk_span(trace.id, "context", "build_context", 528, 11,
                 output={"chunks_selected": 3, "chunks_available": 5, "token_count": 4821}),
        _mk_span(trace.id, "prompt", "render_prompt", 539, 3,
                 output={"token_count": 6885}),
        _mk_span(trace.id, "llm", "openai_chat_completion", 542, 2310,
                 attributes={"provider": "openai", "model": "gpt-4o-mini", "temperature": 0.2},
                 output={"finish_reason": "stop", "output_tokens": 384}),
        _mk_span(trace.id, "response", "format_response", 2852, 1),
    ]
    for s in spans:
        db.add(s)
    await db.flush()

    # Retrieval results for the retrieval span
    retrieval_span = spans[2]
    results = [
        _mk_retrieval_result(retrieval_span.id, 1, "Employee Handbook 2026.pdf",
            "Employees may carry forward up to 5 unused vacation days to the following year. "
            "Days must be used by March 31st or they are forfeited.",
            0.9421, True, reranked_rank=1, reranker_score=0.972,
            metadata={"page": 42, "department": "HR", "year": 2026}),
        _mk_retrieval_result(retrieval_span.id, 2, "Leave Policy Summary.pdf",
            "Annual leave accrues at 1.67 days per month. Unused days may be carried over "
            "subject to the carryover policy described in the Employee Handbook.",
            0.8934, True, reranked_rank=2, reranker_score=0.841,
            metadata={"page": 7, "department": "HR", "year": 2025}),
        _mk_retrieval_result(retrieval_span.id, 3, "HR FAQ 2026.pdf",
            "Employees on leave of absence may carry additional days with manager approval. "
            "Contact HR for the exception request form.",
            0.8721, True, reranked_rank=3, reranker_score=0.803,
            metadata={"page": 12, "department": "HR", "year": 2026}),
        _mk_retrieval_result(retrieval_span.id, 4, "Payroll & Benefits Guide.pdf",
            "Vacation payout at termination: accrued unused vacation is paid at the employee's "
            "current base hourly rate.",
            0.7413, False, reranked_rank=4, reranker_score=0.321,
            metadata={"page": 88, "department": "Payroll", "year": 2026}),
        _mk_retrieval_result(retrieval_span.id, 5, "Remote Work Policy.pdf",
            "Remote employees follow the same leave accrual schedule as on-site employees.",
            0.7102, False, reranked_rank=5, reranker_score=0.244,
            metadata={"page": 3, "department": "HR", "year": 2026}),
    ]
    for r in results:
        db.add(r)
    await db.flush()


async def _seed_trace_poor_retrieval(db: AsyncSession, project_id: str) -> None:
    """Scenario 2: Low similarity scores → vague answer."""
    t_start = _ago(hours=3)
    trace = Trace(
        project_id=project_id,
        name="answer_question",
        started_at=t_start,
        ended_at=t_start + timedelta(milliseconds=3210),
        duration_ms=3210,
        status="warning",
        input={"query": "Can I take a sabbatical?"},
        output={"answer": "I could not find specific information about sabbatical leave in the provided documents."},
        metrics={"input_tokens": 2140, "output_tokens": 112, "total_tokens": 2252, "estimated_cost": 0.004},
        metadata_={"environment": "development", "model": "gpt-4o-mini"},
    )
    db.add(trace)
    await db.flush()

    spans = [
        _mk_span(trace.id, "query", "parse_query", 0, 3),
        _mk_span(trace.id, "retrieval", "vector_search", 3, 298,
                 attributes={"top_k": 5, "similarity_threshold": 0.50}),
        _mk_span(trace.id, "context", "build_context", 301, 8),
        _mk_span(trace.id, "prompt", "render_prompt", 309, 2),
        _mk_span(trace.id, "llm", "openai_chat_completion", 311, 2910,
                 attributes={"provider": "openai", "model": "gpt-4o-mini", "temperature": 0.2},
                 output={"finish_reason": "stop"}),
        _mk_span(trace.id, "response", "format_response", 3221, 1),
    ]
    for s in spans:
        db.add(s)
    await db.flush()

    retrieval_span = spans[1]
    results = [
        _mk_retrieval_result(retrieval_span.id, 1, "Employee Handbook 2026.pdf",
            "Employees are encouraged to maintain a healthy work-life balance.",
            0.54, True, metadata={"page": 1}),
        _mk_retrieval_result(retrieval_span.id, 2, "Remote Work Policy.pdf",
            "Remote employees must maintain standard working hours in their local time zone.",
            0.51, True, metadata={"page": 5}),
        _mk_retrieval_result(retrieval_span.id, 3, "HR FAQ 2026.pdf",
            "For questions not covered in this FAQ, contact your HR business partner.",
            0.49, False, metadata={"page": 20}),
    ]
    for r in results:
        db.add(r)
    await db.flush()

    # Add diagnostic manually for the low retrieval score
    db.add(Diagnostic(
        trace_id=trace.id,
        span_id=retrieval_span.id,
        severity="warning",
        category="retrieval",
        title="Low retrieval confidence",
        description=(
            "The highest-ranked retrieved chunk scored only 0.54, which is below the 0.70 "
            "threshold. Low scores can indicate poor embedding alignment or missing documents."
        ),
        evidence={"top_score": 0.54, "threshold": 0.70},
        suggestions=[
            "Review the query formulation",
            "Ensure sabbatical policy documents are in the knowledge base",
            "Check embedding model alignment",
        ],
    ))
    await db.flush()


async def _seed_trace_excessive_context(db: AsyncSession, project_id: str) -> None:
    """Scenario 3: Too many chunks, high token usage."""
    t_start = _ago(hours=4)
    trace = Trace(
        project_id=project_id,
        name="answer_question",
        started_at=t_start,
        ended_at=t_start + timedelta(milliseconds=5890),
        duration_ms=5890,
        status="success",
        input={"query": "Summarise all HR policies"},
        output={"answer": "Here is a comprehensive summary of all HR policies..."},
        metrics={
            "input_tokens": 14200,
            "output_tokens": 821,
            "total_tokens": 15021,
            "estimated_cost": 0.033,
            "context_tokens": 12050,
        },
        metadata_={"environment": "development", "model": "gpt-4o"},
    )
    db.add(trace)
    await db.flush()

    spans = [
        _mk_span(trace.id, "query", "parse_query", 0, 4),
        _mk_span(trace.id, "retrieval", "vector_search", 4, 421,
                 attributes={"top_k": 20, "similarity_threshold": 0.40}),
        _mk_span(trace.id, "context", "build_context", 425, 18,
                 output={"chunks_selected": 18, "chunks_available": 20, "token_count": 12050}),
        _mk_span(trace.id, "prompt", "render_prompt", 443, 5,
                 output={"token_count": 14200}),
        _mk_span(trace.id, "llm", "openai_chat_completion", 448, 5450,
                 attributes={"provider": "openai", "model": "gpt-4o", "temperature": 0.3}),
        _mk_span(trace.id, "response", "format_response", 5898, 2),
    ]
    for s in spans:
        db.add(s)
    await db.flush()

    db.add(Diagnostic(
        trace_id=trace.id,
        span_id=None,
        severity="warning",
        category="tokens",
        title="Context dominates token usage",
        description=(
            "Retrieved context accounts for 85% of input tokens (12,050 / 14,200). "
            "This leaves little room for conversation history and instructions."
        ),
        evidence={"context_tokens": 12050, "input_tokens": 14200, "pct": 0.848},
        suggestions=[
            "Reduce top_k from 20 toward 5–8",
            "Apply stricter similarity filtering",
            "Truncate chunks to key passages",
        ],
    ))
    await db.flush()


async def _seed_trace_slow_retrieval(db: AsyncSession, project_id: str) -> None:
    """Scenario 4: Slow vector search dominates latency."""
    t_start = _ago(hours=1, minutes=30)
    trace = Trace(
        project_id=project_id,
        name="answer_question",
        started_at=t_start,
        ended_at=t_start + timedelta(milliseconds=4120),
        duration_ms=4120,
        status="success",
        input={"query": "What is the parental leave policy?"},
        output={"answer": "Employees are entitled to 12 weeks of paid parental leave."},
        metrics={"input_tokens": 5200, "output_tokens": 210, "total_tokens": 5410, "estimated_cost": 0.010},
        metadata_={"environment": "staging", "model": "gpt-4o-mini"},
    )
    db.add(trace)
    await db.flush()

    spans = [
        _mk_span(trace.id, "query", "parse_query", 0, 3),
        _mk_span(trace.id, "retrieval", "vector_search", 3, 2840,
                 attributes={"top_k": 5, "similarity_threshold": 0.70, "index": "hr-docs-v2"}),
        _mk_span(trace.id, "context", "build_context", 2843, 9),
        _mk_span(trace.id, "prompt", "render_prompt", 2852, 3),
        _mk_span(trace.id, "llm", "openai_chat_completion", 2855, 1260,
                 attributes={"provider": "openai", "model": "gpt-4o-mini"}),
        _mk_span(trace.id, "response", "format_response", 4115, 1),
    ]
    for s in spans:
        db.add(s)
    await db.flush()

    retrieval_span = spans[1]
    results = [
        _mk_retrieval_result(retrieval_span.id, 1, "Parental Leave Policy 2026.pdf",
            "Employees are entitled to 12 weeks of fully paid parental leave upon the birth "
            "or adoption of a child.",
            0.9312, True, metadata={"page": 2}),
        _mk_retrieval_result(retrieval_span.id, 2, "Employee Handbook 2026.pdf",
            "Leave entitlements are described in detail in the Parental Leave Policy document.",
            0.8801, True, metadata={"page": 55}),
    ]
    for r in results:
        db.add(r)
    await db.flush()

    db.add(Diagnostic(
        trace_id=trace.id,
        span_id=retrieval_span.id,
        severity="warning",
        category="latency",
        title="Slow retrieval",
        description=(
            "Retrieval span 'vector_search' took 2,840 ms, which exceeds the 500 ms threshold."
        ),
        evidence={"duration_ms": 2840, "threshold_ms": 500},
        suggestions=[
            "Check vector database performance and indexing",
            "Consider HNSW or IVF approximate nearest-neighbour indexing",
            "Review network latency to the vector store",
        ],
    ))
    await db.flush()


async def _seed_trace_slow_llm(db: AsyncSession, project_id: str) -> None:
    """Scenario 5: Generation dominates latency."""
    t_start = _ago(minutes=45)
    trace = Trace(
        project_id=project_id,
        name="answer_question",
        started_at=t_start,
        ended_at=t_start + timedelta(milliseconds=12400),
        duration_ms=12400,
        status="success",
        input={"query": "Write a detailed report on our performance review process."},
        output={"answer": "## Performance Review Process\n\n..."},
        metrics={"input_tokens": 8100, "output_tokens": 1842, "total_tokens": 9942, "estimated_cost": 0.029},
        metadata_={"environment": "production", "model": "gpt-4o"},
    )
    db.add(trace)
    await db.flush()

    spans = [
        _mk_span(trace.id, "query", "parse_query", 0, 5),
        _mk_span(trace.id, "retrieval", "vector_search", 5, 380,
                 attributes={"top_k": 8, "similarity_threshold": 0.65}),
        _mk_span(trace.id, "context", "build_context", 385, 12),
        _mk_span(trace.id, "prompt", "render_prompt", 397, 4),
        _mk_span(trace.id, "llm", "openai_chat_completion", 401, 12010,
                 attributes={"provider": "openai", "model": "gpt-4o", "temperature": 0.4},
                 output={"finish_reason": "stop", "output_tokens": 1842}),
        _mk_span(trace.id, "response", "format_response", 12411, 1),
    ]
    for s in spans:
        db.add(s)
    await db.flush()

    db.add(Diagnostic(
        trace_id=trace.id,
        span_id=spans[4].id,
        severity="info",
        category="latency",
        title="Generation dominates latency",
        description=(
            "LLM generation accounts for 97% of total request latency "
            "(12,010 ms out of 12,400 ms)."
        ),
        evidence={"llm_ms": 12010, "total_ms": 12400, "pct": 0.968},
        suggestions=[
            "Consider streaming the response to improve perceived latency",
            "Reduce input context to lower time-to-first-token",
            "Switch to a faster model for latency-sensitive paths",
        ],
    ))
    await db.flush()


async def _seed_trace_failed(db: AsyncSession, project_id: str) -> None:
    """Scenario 6: Provider exception — trace failed."""
    t_start = _ago(minutes=20)
    trace = Trace(
        project_id=project_id,
        name="answer_question",
        started_at=t_start,
        ended_at=t_start + timedelta(milliseconds=1840),
        duration_ms=1840,
        status="error",
        input={"query": "What are the expense reimbursement limits?"},
        output={"error": "OpenAI API error: Rate limit exceeded (429)"},
        metrics={},
        metadata_={"environment": "production", "model": "gpt-4o"},
    )
    db.add(trace)
    await db.flush()

    spans = [
        _mk_span(trace.id, "query", "parse_query", 0, 3),
        _mk_span(trace.id, "retrieval", "vector_search", 3, 304,
                 attributes={"top_k": 5}),
        _mk_span(trace.id, "context", "build_context", 307, 7),
        _mk_span(trace.id, "prompt", "render_prompt", 314, 2),
        _mk_span(trace.id, "llm", "openai_chat_completion", 316, 1530,
                 status="error",
                 attributes={"provider": "openai", "model": "gpt-4o"},
                 output={"error": "RateLimitError: Rate limit exceeded", "status_code": 429}),
    ]
    for s in spans:
        db.add(s)
    await db.flush()


async def _seed_trace_reranking(db: AsyncSession, project_id: str) -> None:
    """Scenario 7: Significant rank changes after cross-encoder reranking."""
    t_start = _ago(minutes=10)
    trace = Trace(
        project_id=project_id,
        name="answer_question",
        started_at=t_start,
        ended_at=t_start + timedelta(milliseconds=3180),
        duration_ms=3180,
        status="success",
        input={"query": "How do I submit an expense claim?"},
        output={"answer": "To submit an expense claim, log in to the expense portal at expenses.company.com..."},
        metrics={"input_tokens": 5840, "output_tokens": 298, "total_tokens": 6138, "estimated_cost": 0.011},
        metadata_={"environment": "development", "model": "gpt-4o-mini"},
    )
    db.add(trace)
    await db.flush()

    spans = [
        _mk_span(trace.id, "query", "parse_query", 0, 3),
        _mk_span(trace.id, "retrieval", "vector_search", 3, 294,
                 attributes={"top_k": 6, "similarity_threshold": 0.65}),
        _mk_span(trace.id, "reranking", "cross_encoder_rerank", 297, 198,
                 attributes={"model": "cross-encoder/ms-marco-MiniLM-L-6-v2", "top_n": 3}),
        _mk_span(trace.id, "context", "build_context", 495, 9),
        _mk_span(trace.id, "prompt", "render_prompt", 504, 3),
        _mk_span(trace.id, "llm", "openai_chat_completion", 507, 2680,
                 attributes={"provider": "openai", "model": "gpt-4o-mini"},
                 output={"finish_reason": "stop"}),
        _mk_span(trace.id, "response", "format_response", 3187, 1),
    ]
    for s in spans:
        db.add(s)
    await db.flush()

    retrieval_span = spans[1]
    # Retrieval rank ≠ reranker rank — demonstrates the reranking inspector
    results = [
        _mk_retrieval_result(retrieval_span.id, 1, "General FAQ.pdf",
            "Our company has offices in New York, London, and Singapore.",
            0.812, False, reranked_rank=5, reranker_score=0.112,
            metadata={"page": 1}),
        _mk_retrieval_result(retrieval_span.id, 2, "Remote Work Policy.pdf",
            "Expense reimbursement for home-office equipment is capped at $500 per year.",
            0.791, True, reranked_rank=3, reranker_score=0.701,
            metadata={"page": 9}),
        _mk_retrieval_result(retrieval_span.id, 3, "Expense Policy 2026.pdf",
            "All expense claims must be submitted within 30 days of the expense date via the "
            "expense portal at expenses.company.com.",
            0.781, True, reranked_rank=1, reranker_score=0.964,
            metadata={"page": 2}),
        _mk_retrieval_result(retrieval_span.id, 4, "Expense Policy 2026.pdf",
            "Receipts are required for all expenses over $25. Attach photos of receipts "
            "directly in the expense portal.",
            0.761, True, reranked_rank=2, reranker_score=0.882,
            metadata={"page": 3}),
        _mk_retrieval_result(retrieval_span.id, 5, "Travel Policy.pdf",
            "Business travel expenses including flights, hotels, and meals are reimbursable "
            "subject to the per diem limits in Appendix B.",
            0.742, False, reranked_rank=4, reranker_score=0.411,
            metadata={"page": 1}),
    ]
    for r in results:
        db.add(r)
    await db.flush()


# ── Main seeder ────────────────────────────────────────────────────────────────

async def run_seed(db: AsyncSession) -> bool:
    """
    Seed the database with a demo user, project, and traces.

    Returns True if seeding was performed, False if already seeded.
    """
    repo = UserRepository(db)
    existing = await repo.get_by_email(SEED_EMAIL)
    if existing:
        logger.info("Seed already exists — skipping")
        return False

    logger.info("Seeding demo data...")

    # User
    user = User(
        email=SEED_EMAIL,
        hashed_password=hash_password(SEED_PASSWORD),
        full_name="Demo User",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.flush()

    # Project
    project = Project(
        owner_id=user.id,
        name=SEED_PROJECT_NAME,
        description="HR knowledge base RAG pipeline for employee queries.",
        slug="hr-knowledge-base",
        is_active=True,
    )
    db.add(project)
    await db.flush()

    # API key
    key_hash = hashlib.sha256(SEED_API_KEY_RAW.encode()).hexdigest()
    api_key = ApiKey(
        project_id=project.id,
        name="Development key",
        key_prefix=SEED_API_KEY_RAW[:20],
        key_hash=key_hash,
    )
    db.add(api_key)
    await db.flush()

    # Traces
    await _seed_trace_success(db, project.id)
    await _seed_trace_poor_retrieval(db, project.id)
    await _seed_trace_excessive_context(db, project.id)
    await _seed_trace_slow_retrieval(db, project.id)
    await _seed_trace_slow_llm(db, project.id)
    await _seed_trace_failed(db, project.id)
    await _seed_trace_reranking(db, project.id)

    await db.commit()
    logger.info(
        "Seeded: user=%s, project=%s, 7 traces", user.email, project.name
    )
    logger.info("Demo login: %s / %s", SEED_EMAIL, SEED_PASSWORD)
    logger.info("Demo API key: %s", SEED_API_KEY_RAW)
    return True
