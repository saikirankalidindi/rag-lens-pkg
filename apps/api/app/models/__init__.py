"""
Import all models here so Alembic's autogenerate can detect every table.
Order matters: base models before dependent models.
"""
from app.models.user import User
from app.models.project import Project
from app.models.api_key import ApiKey
from app.models.trace import Trace
from app.models.span import Span
from app.models.retrieval_result import RetrievalResult
from app.models.diagnostic import Diagnostic

__all__ = [
    "User",
    "Project",
    "ApiKey",
    "Trace",
    "Span",
    "RetrievalResult",
    "Diagnostic",
]
