"""Opt-in integration: point DATABASE_URL at a migrated, disposable PostgreSQL DB."""
import importlib.util
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from raglens import RAGLens

pytestmark = pytest.mark.skipif(os.getenv("RAGLENS_TEST_POSTGRES") != "1", reason="requires disposable PostgreSQL")


def test_register_ingest_read_and_revoke():
    from app.main import create_app
    with TestClient(create_app()) as api:
        credentials = {"email": f"test-{uuid4().hex}@example.com", "password": "validation-password"}
        register = api.post("/auth/register", json=credentials)
        assert register.status_code == 201, register.text
        login = api.post("/auth/login", json=credentials)
        assert login.status_code == 200
        headers = {"Authorization": "Bearer " + login.json()["access_token"]}
        project = api.post("/projects", json={"name": "  SDK\tvalidation  "}, headers=headers)
        assert project.status_code == 201, project.text
        pid = project.json()["id"]
        # Names are unique per owner after case/whitespace normalization.
        assert api.post("/projects", json={"name": "  SDK   VALIDATION  "}, headers=headers).status_code == 409
        assert api.post("/projects", json={"name": "   "}, headers=headers).status_code == 422
        other = api.post("/projects", json={"name": "Another project"}, headers=headers).json()
        assert api.patch(f"/projects/{other['id']}", json={"name": "sdk validation"}, headers=headers).status_code == 409
        assert api.patch(f"/projects/{pid}", json={"name": "SDK validation"}, headers=headers).status_code == 200
        with ThreadPoolExecutor(max_workers=4) as pool:
            responses = list(pool.map(lambda _: api.post("/projects", json={"name": "Concurrent project"}, headers=headers), range(4)))
        assert sorted(r.status_code for r in responses) == [201, 409, 409, 409]
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda project_id: api.patch(f"/projects/{project_id}", json={"name": "Concurrent rename"}, headers=headers), [pid, other["id"]]))
        assert sorted(r.status_code for r in responses) == [200, 409]
        second = api.post("/auth/register", json={"email": f"second-{uuid4().hex}@example.com", "password": "validation-password"}).json()
        second_headers = {"Authorization": "Bearer " + second["access_token"]}
        assert api.post("/projects", json={"name": "Concurrent rename"}, headers=second_headers).status_code == 201
        key = api.post(f"/projects/{pid}/api-keys", json={"name": "test"}, headers=headers).json()
        def send(request):
            return api.post("/v1/traces", content=request.content,
                            headers={"Authorization": request.headers["authorization"], "Content-Type": "application/json"})
        sdk = RAGLens(api_key=key["raw_key"], transport=httpx.MockTransport(send))
        with sdk.trace("persisted") as trace:
            with trace.span("query", "root"):
                trace.log_retrieval(results=[{"chunk_id": "c", "document_id": "d", "document_name": "Doc",
                                             "content": "text", "score": .2, "selected": False}])
                trace.log_context(context="text", tokens=90, max_tokens=100)
        assert trace.id
        detail = api.get(f"/projects/{pid}/traces/{trace.id}", headers=headers)
        assert detail.status_code == 200, detail.text
        data = detail.json()
        assert len(data["spans"]) == 3
        assert len(data["diagnostics"]) == 4
        assert all(d["span_id"] in {s["id"] for s in data["spans"]} for d in data["diagnostics"])
        demo_path = Path(__file__).resolve().parents[3] / "examples/basic-rag/app.py"
        spec = importlib.util.spec_from_file_location("basic_rag", demo_path)
        demo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(demo)
        for question in ["solar panels electricity", "quantum entanglement", "renewable energy"]:
            answer, demo_trace = demo.answer(sdk, question)
            assert demo_trace.id and answer
            persisted = api.get(f"/projects/{pid}/traces/{demo_trace.id}", headers=headers).json()
            assert len(persisted["spans"]) == 5
            assert persisted["output"]["answer"] == answer
            if question == "quantum entanglement":
                assert answer == "No relevant documents found."
        summary = api.get("/projects", headers=headers)
        assert summary.status_code == 200
        summary_project = next(p for p in summary.json() if p["id"] == pid)
        assert summary_project["trace_count"] == 4
        assert summary_project["last_trace_at"]
        assert summary_project["total_tokens"] > 0
        keys = api.get(f"/projects/{pid}/api-keys", headers=headers).json()
        assert keys[0]["last_used_at"]
        revoked = api.delete(f"/projects/{pid}/api-keys/{key['api_key']['id']}", headers=headers)
        assert revoked.status_code == 204
        with sdk.trace("revoked") as rejected:
            pass
        assert rejected.id is None
