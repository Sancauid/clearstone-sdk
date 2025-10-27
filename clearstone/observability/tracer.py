# clearstone/observability/tracer.py

import uuid
import time
import threading
import traceback
from typing import Any, Dict, Optional, List, TYPE_CHECKING
from contextlib import contextmanager

from .models import Span, SpanKind, SpanStatus, Trace

if TYPE_CHECKING:
    from ..storage.sqlite import SpanBuffer

# Thread-local storage is used to maintain a stack of active spans for each thread.
# This allows for automatic parent-child linking in nested spans.
_thread_local = threading.local()

class SpanContextManager:
    """A context manager to handle the lifecycle of a single Span."""

    def __init__(self, tracer: 'Tracer', name: str, kind: SpanKind = SpanKind.INTERNAL):
        self.tracer = tracer
        
        # Determine parent_id from the current thread's span stack
        parent_id = None
        if hasattr(_thread_local, 'span_stack') and _thread_local.span_stack:
            parent_id = _thread_local.span_stack[-1].span_id
            
        self.span = Span(
            trace_id=tracer.trace_id,
            parent_span_id=parent_id,
            name=name,
            kind=kind,
            start_time_ns=time.time_ns(),
            instrumentation_name=tracer.instrumentation_name,
            instrumentation_version=tracer.instrumentation_version
        )

    def __enter__(self) -> Span:
        """Called when entering the 'with' block."""
        if not hasattr(_thread_local, 'span_stack'):
            _thread_local.span_stack = []
        
        _thread_local.span_stack.append(self.span)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Called when exiting the 'with' block."""
        self.span.end_time_ns = time.time_ns()

        if exc_type is not None:
            self.span.status = SpanStatus.ERROR
            self.span.error_message = str(exc_val)
            self.span.error_stacktrace = traceback.format_exc()
        else:
            self.span.status = SpanStatus.OK
        
        # Pop this span from the stack
        if hasattr(_thread_local, 'span_stack') and _thread_local.span_stack:
            _thread_local.span_stack.pop()
        
        # Pass the completed span to the tracer's buffer
        self.tracer._buffer_span(self.span)
        
        # Return False to re-raise any exceptions
        return False

class Tracer:
    """
    The primary API for creating and managing spans within a trace.
    Supports both integrated mode (with external buffer) and legacy mode (internal buffer).
    """
    def __init__(
        self,
        name: str,
        instrumentation_name: str = "clearstone",
        instrumentation_version: str = "0.1.0",
        buffer: Optional['SpanBuffer'] = None,
        trace_id: Optional[str] = None
    ):
        self.name = name
        self.instrumentation_name = instrumentation_name
        self.instrumentation_version = instrumentation_version
        self.trace_id = trace_id or uuid.uuid4().hex
        
        self._buffer = buffer
        if buffer is None:
            self._span_buffer: List[Span] = []
            self._buffer_lock = threading.Lock()
        else:
            self._span_buffer = None
            self._buffer_lock = None

    def span(self, name: str, kind: SpanKind = SpanKind.INTERNAL, attributes: Optional[Dict[str, Any]] = None) -> SpanContextManager:
        """
        Creates a new span that is managed by a context manager.

        Args:
            name: A human-readable name for the operation (e.g., "agent.think").
            kind: The OTel-aligned kind of the span (e.g., SpanKind.CLIENT).
            attributes: A dictionary of initial attributes for the span.

        Returns:
            A SpanContextManager to be used in a 'with' statement.
        """
        context_manager = SpanContextManager(self, name, kind)
        if attributes:
            context_manager.span.attributes.update(attributes)
        
        return context_manager

    def _buffer_span(self, span: Span):
        """Adds a completed span to the buffer (internal or external)."""
        if self._buffer is not None:
            self._buffer.add_span(span)
        else:
            with self._buffer_lock:
                self._span_buffer.append(span)

    def get_buffered_spans(self) -> List[Span]:
        """Returns a copy of the current in-memory span buffer (legacy mode only)."""
        if self._span_buffer is not None:
            with self._buffer_lock:
                return self._span_buffer.copy()
        return []

    def clear_buffer(self):
        """Clears the in-memory buffer (legacy mode only)."""
        if self._span_buffer is not None:
            with self._buffer_lock:
                self._span_buffer.clear()

# --- Global Tracer Registry (Legacy Mode for Testing) ---

_tracer_registry: Dict[str, Tracer] = {}
_registry_lock = threading.Lock()

def get_tracer(name: str) -> Tracer:
    """
    Gets or creates a tracer for a given name (legacy mode with internal buffer).
    For production use with persistent storage, use TracerProvider.get_tracer() instead.
    
    Args:
        name: The name of the tracer, typically the module or agent being instrumented.

    Returns:
        A thread-safe Tracer instance with internal buffering.
    """
    with _registry_lock:
        if name not in _tracer_registry:
            _tracer_registry[name] = Tracer(name)
        return _tracer_registry[name]

def reset_tracer_registry():
    """Clears the global tracer registry. Used for testing isolation."""
    with _registry_lock:
        _tracer_registry.clear()

