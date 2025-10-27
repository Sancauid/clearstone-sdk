# clearstone/observability/provider.py

import atexit
from threading import Lock
from typing import Dict, Optional

from ..storage.sqlite import SpanBuffer, TraceStore
from .tracer import Tracer


class TracerProvider:
    """
    A central provider that manages the lifecycle of the entire tracing system,
    including the storage backend, buffer, and individual tracers.
    """

    def __init__(self, db_path: str = "clearstone_traces.db"):
        self._tracers: Dict[str, Tracer] = {}
        self._lock = Lock()

        self.trace_store = TraceStore(db_path=db_path)
        self.span_buffer = SpanBuffer(writer=self.trace_store)

        atexit.register(self.shutdown)

    def get_tracer(self, name: str, version: str = "0.1.0") -> Tracer:
        """
        Gets or creates a Tracer instance. All tracers created by this provider
        will share the same underlying storage and buffer.
        """
        with self._lock:
            if name not in self._tracers:
                tracer = Tracer(
                    name=name,
                    instrumentation_name=name,
                    instrumentation_version=version,
                    buffer=self.span_buffer,
                )
                self._tracers[name] = tracer
            return self._tracers[name]

    def shutdown(self):
        """
        Gracefully shuts down the tracing system, ensuring all buffered
        spans are written to storage.
        """
        print("Shutting down Clearstone TracerProvider, flushing spans...")
        self.span_buffer.shutdown()
        print("Clearstone shutdown complete.")


_global_provider: Optional[TracerProvider] = None
_provider_lock = Lock()


def get_tracer_provider(db_path: str = "clearstone_traces.db") -> TracerProvider:
    """
    Gets the global singleton TracerProvider instance.
    This is the primary entry point for initializing the Clearstone tracing system.
    """
    global _global_provider
    with _provider_lock:
        if _global_provider is None:
            _global_provider = TracerProvider(db_path=db_path)
        return _global_provider


def reset_tracer_provider():
    """Resets the global provider. Used for testing."""
    global _global_provider
    with _provider_lock:
        if _global_provider is not None:
            _global_provider.shutdown()
        _global_provider = None
