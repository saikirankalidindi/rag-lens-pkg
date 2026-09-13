from .common import finding, number


def run(trace, spans, results, settings):
    for span in spans:
        if span.status == "error":
            yield finding(trace, span, "failed_span", "generation", "Failed span",
                          {"status": span.status, "error": (span.attributes or {}).get("error")},
                          ["Inspect this stage's error and verify its inputs and dependencies"], "error")
    llm = [s for s in spans if s.type == "llm"]
    duration = number(trace.duration_ms)
    if not llm or duration <= 0:
        return
    # Merge intervals to avoid double-counting overlapping or nested LLM calls.
    intervals = sorted((max(0, (s.started_at - trace.started_at).total_seconds() * 1000),
                        min(duration, (s.started_at - trace.started_at).total_seconds() * 1000 + number(s.duration_ms)))
                       for s in llm if s.started_at is not None)
    total, end = 0, 0
    for start, stop in intervals:
        total += max(0, stop - max(start, end))
        end = max(end, stop)
    if total / duration > settings.diag_slow_generation_pct:
        yield finding(trace, max(llm, key=lambda s: number(s.duration_ms)), "slow_generation", "latency",
                      "Generation dominates latency", {"llm_ms": total, "total_ms": duration,
                      "pct": total / duration, "threshold": settings.diag_slow_generation_pct},
                      ["Consider streaming, reducing input tokens, or using a faster model"], "info")
