# clearstone/observability/__init__.py

from clearstone.observability.models import (
    Span,
    SpanEvent,
    SpanKind,
    SpanLink,
    SpanStatus,
    Trace,
)
from clearstone.observability.tracer import (
    SpanContextManager,
    Tracer,
    get_tracer,
    reset_tracer_registry,
)


def __getattr__(name):
    """Lazy import of provider to avoid circular dependency."""
    if name in ("TracerProvider", "get_tracer_provider", "reset_tracer_provider"):
        from clearstone.observability.provider import (  # noqa: F401
            TracerProvider,
            get_tracer_provider,
            reset_tracer_provider,
        )

        globals()[name] = locals()[name]
        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Span",
    "Trace",
    "SpanKind",
    "SpanStatus",
    "SpanEvent",
    "SpanLink",
    "Tracer",
    "SpanContextManager",
    "get_tracer",
    "reset_tracer_registry",
    "TracerProvider",
    "get_tracer_provider",
    "reset_tracer_provider",
]
