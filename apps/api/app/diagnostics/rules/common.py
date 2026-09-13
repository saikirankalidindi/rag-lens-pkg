import math

from app.models.diagnostic import Diagnostic


def number(value):
    return value if isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value) else 0


def finding(trace, span, rule, category, title, evidence, suggestions, severity="warning"):
    return Diagnostic(trace_id=trace.id, span_id=span.id if span else None,
                      severity=severity, category=category, title=title,
                      description=title + ". Review the evidence and the linked pipeline stage.",
                      evidence={"rule": rule, **evidence}, suggestions=suggestions)


def retrieval_groups(spans, results):
    for span in spans:
        if span.type == "retrieval":
            yield span, [r for r in results if r.span_id == span.id]
