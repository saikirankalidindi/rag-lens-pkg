from datetime import UTC, datetime
from types import SimpleNamespace as Obj

from app.diagnostics.engine import DiagnosticEngine


def sample():
    start = datetime.now(UTC)
    trace = Obj(id="t", duration_ms=1000, started_at=start, metrics={"input_tokens": 100, "context_tokens": 90})
    spans = [Obj(id="r", type="retrieval", duration_ms=600, attributes={}, status="success", started_at=start),
             Obj(id="c", type="context", duration_ms=1, attributes={"token_count": 90, "max_tokens": 100}, status="success", started_at=start),
             Obj(id="l", type="llm", duration_ms=900, attributes={"error": "failure"}, status="error", started_at=start)]
    results = [Obj(span_id="r", score=.5, selected=i == 0) for i in range(4)]
    return trace, spans, results


def test_all_eight_rules_have_evidence_and_span_links():
    findings = DiagnosticEngine().run_diagnostics(*sample())
    assert {d.evidence["rule"] for d in findings} == {
        "low_retrieval_confidence", "retrieval_waste", "slow_retrieval", "excessive_context",
        "low_context_utilization", "slow_generation", "failed_span", "token_heavy_context"}
    assert all(d.trace_id == "t" and d.span_id and d.suggestions for d in findings)


def test_retrieval_stages_do_not_mask_each_other_and_zero_selection():
    trace, spans, results = sample()
    spans.append(Obj(id="r2", type="retrieval", duration_ms=1, attributes={}, status="success"))
    results.append(Obj(span_id="r2", score=.99, selected=True))
    for result in results[:4]:
        result.selected = False
    findings = DiagnosticEngine().run_diagnostics(trace, spans, results)
    low = [d for d in findings if d.evidence["rule"] == "low_retrieval_confidence"]
    assert len(low) == 1 and low[0].span_id == "r"
    waste = next(d for d in findings if d.evidence["rule"] == "retrieval_waste")
    assert waste.evidence["selected"] == 0


def test_exact_thresholds_do_not_trigger_and_overlaps_are_merged():
    trace, spans, results = sample()
    trace.metrics = {"input_tokens": 100, "context_tokens": 85}
    spans[0].duration_ms = 500
    spans[1].attributes["token_count"] = 80
    spans[2].status = "success"
    spans[2].duration_ms = 850
    spans.append(Obj(**vars(spans[2])))
    results = [Obj(span_id="r", score=.7, selected=True)]
    assert DiagnosticEngine().run_diagnostics(trace, spans, results) == []


def test_missing_metrics_and_zero_duration():
    trace, spans, results = sample()
    trace.duration_ms = 0
    trace.metrics = {}
    for span in spans:
        span.attributes = {}
        span.status = "success"
        span.duration_ms = 0
    assert DiagnosticEngine().run_diagnostics(trace, spans, []) == []
