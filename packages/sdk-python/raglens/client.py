import logging
import os

import httpx

logger = logging.getLogger("raglens")


class RAGLens:
    """Synchronous, best-effort trace delivery with a bounded HTTP timeout."""

    def __init__(self, api_key=None, base_url=None, enabled=None, timeout=2.0,
                 project_id=None, web_url="http://localhost:3000", transport=None):
        self.api_key = api_key if api_key is not None else os.getenv("RAGLENS_API_KEY", "")
        self.base_url = (base_url or os.getenv("RAGLENS_BASE_URL", "http://localhost:8000")).rstrip("/")
        self.enabled = (os.getenv("RAGLENS_ENABLED", "true").lower() not in
                        {"0", "false", "no", "off"}) if enabled is None else enabled
        self.project_id = project_id
        self.web_url = web_url.rstrip("/")
        self.timeout = timeout
        self.transport = transport

    def trace(self, name, **kwargs):
        from .trace import Trace
        return Trace(self, name, **kwargs)

    def send_trace(self, trace):
        if not self.enabled:
            return None
        try:
            if not self.api_key:
                logger.warning("Trace delivery skipped: RAGLENS_API_KEY is not configured")
                return None
            from .serializers import serialize_trace
            payload = serialize_trace(trace)
            with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
                response = client.post(self.base_url + "/v1/traces", json=payload,
                                       headers={"Authorization": "Bearer " + self.api_key})
                response.raise_for_status()
                return response.json()["trace_id"]
        except Exception as exc:
            # Avoid logging payloads, credentials or exception URLs.
            logger.warning("Trace delivery failed (%s)", type(exc).__name__)
            return None
