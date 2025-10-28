# clearstone/storage/types.py

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from clearstone.observability.models import Span, Trace


class BaseTraceStore(ABC):
    """Abstract base class for a trace storage backend."""

    @abstractmethod
    def write_spans(self, spans: List["Span"]):
        """Write a batch of spans to storage."""
        pass

    @abstractmethod
    def get_trace(self, trace_id: str) -> "Trace":
        """Retrieve a complete trace by its ID."""
        pass


class BaseSpanBuffer(ABC):
    """Abstract base class for a span buffer."""

    @abstractmethod
    def add_span(self, span: "Span"):
        """Add a span to the buffer."""
        pass

    @abstractmethod
    def shutdown(self):
        """Shutdown the buffer and flush remaining spans."""
        pass
