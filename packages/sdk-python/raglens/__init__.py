from importlib.metadata import version

from .client import RAGLens
from .helpers import log_context, log_generation, log_prompt, log_retrieval
from .span import Span
from .trace import Trace

__version__ = version("raglens")
__all__ = ["RAGLens", "Trace", "Span", "log_retrieval", "log_context", "log_prompt", "log_generation"]
