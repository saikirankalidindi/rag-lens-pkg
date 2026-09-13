from .common import finding, number, retrieval_groups


def run(trace, spans, results, settings):
    for span, rows in retrieval_groups(spans, results):
        if rows:
            score = max(number(r.score) for r in rows)
            threshold = settings.diag_low_retrieval_score_threshold
            if score < threshold:
                yield finding(trace, span, "low_retrieval_confidence", "retrieval", "Low retrieval confidence",
                              {"top_score": score, "threshold": threshold},
                              ["Review query wording and embedding alignment", "Check source coverage"])
            selected = sum(bool(r.selected) for r in rows)
            if selected == 0 or len(rows) / selected > settings.diag_retrieval_waste_ratio:
                yield finding(trace, span, "retrieval_waste", "retrieval", "Retrieval waste",
                              {"retrieved": len(rows), "selected": selected,
                               "ratio": len(rows) / selected if selected else None,
                               "threshold": settings.diag_retrieval_waste_ratio},
                              ["Reduce top_k or filter irrelevant chunks earlier"], "info")
        if number(span.duration_ms) > settings.diag_slow_retrieval_ms:
            yield finding(trace, span, "slow_retrieval", "latency", "Slow retrieval",
                          {"duration_ms": span.duration_ms, "threshold_ms": settings.diag_slow_retrieval_ms},
                          ["Review vector index performance and network latency"])
