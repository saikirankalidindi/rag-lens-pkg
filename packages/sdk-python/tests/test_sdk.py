import asyncio
import json
from datetime import datetime, timezone

import httpx
import pytest

from raglens import RAGLens, log_retrieval
from raglens.serializers import serialize_trace


def client(handler):
    return RAGLens(api_key="test-key", project_id="project", transport=httpx.MockTransport(handler))


def test_complete_payload_and_nesting():
    captured = []
    def handle(request):
        assert request.url.path == "/v1/traces"
        assert request.headers["authorization"] == "Bearer test-key"
        captured.append(json.loads(request.content))
        return httpx.Response(201, json={"trace_id": "trace_test"})
    with client(handle).trace("test", input={"date": datetime.now(timezone.utc)}) as trace:
        with trace.span("query", "root") as root:
            with trace.span("retrieval", "search") as span:
                log_retrieval(span, [{"chunk_id": "c", "document_id": "d", "document_name": "Doc",
                                     "content": "text", "score": .9, "selected": True}])
            trace.log_context(context="text", tokens=1, max_tokens=10)
            trace.log_prompt(prompt="question", tokens=1)
            trace.log_generation(response="answer", tokens={"input_tokens": 2, "output_tokens": 1}, model="mock")
        trace.set_output({"answer": "answer"})
    payload = captured[0]
    assert len(payload["spans"]) == 5
    assert all(s["parent_span_id"] == root.id for s in payload["spans"][1:])
    assert payload["spans"][1]["retrieval_results"][0]["rank"] == 1
    assert payload["metrics"]["total_tokens"] == 3
    assert payload["ended_at"] >= payload["started_at"]
    assert trace.url == "http://localhost:3000/projects/project/traces/trace_test"


@pytest.mark.parametrize("failure", ["network", "http", "json", "serialize"])
def test_delivery_failures_do_not_replace_application_exception(failure):
    def handle(request):
        if failure == "network":
            raise httpx.ConnectError("offline")
        return httpx.Response(500 if failure == "http" else 201, text="invalid json")
    error = ValueError("application failure")
    with pytest.raises(ValueError) as caught:
        with client(handle).trace("failure") as trace:
            if failure == "serialize":
                trace.set_output({"unsupported": object()})
            with trace.span("custom", "fails"):
                raise error
    assert caught.value is error
    assert trace.status == trace.spans[0].status == "error"
    assert trace.id is None


def test_disabled_env_and_serialization(monkeypatch):
    monkeypatch.setenv("RAGLENS_ENABLED", "false")
    monkeypatch.setenv("RAGLENS_BASE_URL", "http://example.test")
    c = RAGLens(transport=httpx.MockTransport(lambda r: pytest.fail("HTTP called")))
    with c.trace("disabled", metadata={"error": ValueError("example")}) as trace:
        pass
    assert trace.id is None
    assert c.base_url == "http://example.test"
    assert serialize_trace(trace)["metadata"]["error"]["type"] == "ValueError"


def test_concurrent_span_parents_are_isolated():
    async def run():
        with RAGLens(enabled=False).trace("parallel") as trace:
            async def child(name):
                with trace.span("custom", name) as parent:
                    await asyncio.sleep(0)
                    with trace.span("custom", name + "-child") as nested:
                        assert nested.parent_span_id == parent.id
            await asyncio.gather(child("one"), child("two"))
        assert sum(s.parent_span_id is None for s in trace.spans) == 2
    asyncio.run(run())
