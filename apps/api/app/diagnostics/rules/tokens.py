from .common import finding, number


def run(trace, spans, results, settings):
    metrics = trace.metrics or {}
    context_spans = [s for s in spans if s.type == "context"]
    context = number(metrics.get("context_tokens", sum(number((s.attributes or {}).get("token_count")) for s in context_spans)))
    inputs = number(metrics.get("input_tokens", sum(number((s.attributes or {}).get("input_tokens")) for s in spans if s.type == "llm")))
    if inputs > 0 and context / inputs > settings.diag_token_heavy_context_pct:
        yield finding(trace, context_spans[0] if context_spans else None, "token_heavy_context", "tokens",
                      "Context dominates token usage", {"context_tokens": context, "input_tokens": inputs,
                      "pct": context / inputs, "threshold": settings.diag_token_heavy_context_pct},
                      ["Select fewer chunks or shorten each passage"])
