import json
from datetime import date, datetime


def _default(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, BaseException):
        return {"type": type(value).__name__, "message": str(value)}
    raise TypeError(f"Unsupported trace value: {type(value).__name__}")


def serialize_trace(trace):
    fields = ("name", "session_id", "user_id", "started_at", "ended_at", "duration_ms",
              "status", "input", "output", "metrics", "metadata")
    payload = {key: getattr(trace, key) for key in fields}
    span_fields = ("id", "parent_span_id", "type", "name", "started_at", "ended_at",
                   "duration_ms", "status", "input", "output", "attributes", "retrieval_results")
    payload["spans"] = [{key: getattr(span, key) for key in span_fields} for span in trace.spans]
    return json.loads(json.dumps(payload, default=_default, allow_nan=False))
