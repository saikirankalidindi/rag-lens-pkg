"""Deterministic diagnostics; persistence belongs to the ingestion transaction."""
import logging

from app.config import get_settings
from app.diagnostics.rules import context, latency, retrieval, tokens

logger = logging.getLogger(__name__)


class DiagnosticEngine:
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self.rules = (retrieval.run, context.run, latency.run, tokens.run)

    def run_diagnostics(self, trace, spans, retrieval_results=()):
        findings = []
        for rule in self.rules:
            try:
                findings.extend(rule(trace, spans, retrieval_results, self.settings))
            except Exception:
                logger.exception("Diagnostic rule group %s failed", rule.__module__)
        return findings


def run_diagnostics(trace, spans, retrieval_results):
    return DiagnosticEngine().run_diagnostics(trace, spans, retrieval_results)
