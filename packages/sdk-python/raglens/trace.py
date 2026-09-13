from contextvars import ContextVar
from datetime import datetime, timezone
from time import perf_counter

from .span import Span


class Trace:
    def __init__(self, client, name, input=None, metadata=None, session_id=None, user_id=None):
        self.client, self.name = client, name
        self.input, self.output = input, None
        self.metadata = dict(metadata or {})
        self.session_id, self.user_id = session_id, user_id
        self.metrics, self.spans = {}, []
        self.status = "success"
        self.started_at = self.ended_at = None
        self.duration_ms = 0
        self.id = None
        self._active_span = ContextVar("raglens_span", default=None)

    @property
    def url(self):
        if self.id and self.client.project_id:
            return f"{self.client.web_url}/projects/{self.client.project_id}/traces/{self.id}"
        return None

    def __enter__(self):
        self.started_at = datetime.now(timezone.utc)
        self._start = perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.ended_at = datetime.now(timezone.utc)
        self.duration_ms = max(0, int((perf_counter() - self._start) * 1000))
        if exc is not None:
            self.status = "error"
            self.metadata["error"] = {"type": exc_type.__name__, "message": str(exc)}
        self.id = self.client.send_trace(self)
        return False

    def span(self, type, name, **kwargs):
        return Span(self, type, name, **kwargs)

    def set_output(self, output):
        self.output = output

    def set_metrics(self, metrics):
        self.metrics.update(metrics)

    def log_retrieval(self, **kwargs):
        from .helpers import log_retrieval
        with self.span("retrieval", "retrieval") as span:
            log_retrieval(span, **kwargs)
        return span

    def log_context(self, **kwargs):
        from .helpers import log_context
        with self.span("context", "context") as span:
            log_context(span, **kwargs)
        return span

    def log_prompt(self, **kwargs):
        from .helpers import log_prompt
        with self.span("prompt", "prompt") as span:
            log_prompt(span, **kwargs)
        return span

    def log_generation(self, **kwargs):
        from .helpers import log_generation
        with self.span("llm", "generation") as span:
            log_generation(span, **kwargs)
        return span
