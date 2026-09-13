from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4


class Span:
    def __init__(self, trace, type, name, input=None, attributes=None, parent_span_id=None):
        self.trace = trace
        self.id = "span_" + uuid4().hex
        self.type, self.name = type, name
        self.parent_span_id = parent_span_id
        self.input, self.output = input, None
        self.attributes = dict(attributes or {})
        self.retrieval_results = []
        self.status = "success"
        self.started_at = self.ended_at = None
        self.duration_ms = 0

    def __enter__(self):
        self.started_at = datetime.now(timezone.utc)
        self._start = perf_counter()
        parent = self.trace._active_span.get()
        if self.parent_span_id is None and parent is not None:
            self.parent_span_id = parent.id
        self._token = self.trace._active_span.set(self)
        self.trace.spans.append(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        self.ended_at = datetime.now(timezone.utc)
        self.duration_ms = max(0, int((perf_counter() - self._start) * 1000))
        if exc is not None:
            self.status = "error"
            self.attributes["error"] = {"type": exc_type.__name__, "message": str(exc)}
        self.trace._active_span.reset(self._token)
        return False

    def set_output(self, output):
        self.output = output

    def set_attributes(self, attributes):
        self.attributes.update(attributes)

    def span(self, type, name, **kwargs):
        return self.trace.span(type=type, name=name, parent_span_id=self.id, **kwargs)
