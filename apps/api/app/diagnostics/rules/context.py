from .common import finding, number, retrieval_groups


def run(trace, spans, results, settings):
    for span in spans:
        if span.type != "context":
            continue
        attrs = span.attributes or {}
        tokens, window = number(attrs.get("token_count")), number(attrs.get("max_tokens"))
        if window > 0 and tokens / window > settings.diag_excessive_context_pct:
            yield finding(trace, span, "excessive_context", "context", "Excessive context",
                          {"context_tokens": tokens, "max_tokens": window,
                           "pct": tokens / window, "threshold": settings.diag_excessive_context_pct},
                          ["Trim context chunks or increase the model context window"])
    for span, rows in retrieval_groups(spans, results):
        selected = sum(bool(r.selected) for r in rows)
        if rows and selected / len(rows) < settings.diag_low_context_utilization_pct:
            yield finding(trace, span, "low_context_utilization", "context", "Low context utilisation",
                          {"retrieved": len(rows), "selected": selected, "pct": selected / len(rows),
                           "threshold": settings.diag_low_context_utilization_pct},
                          ["Inspect discarded chunks and tune retrieval top_k"], "info")
