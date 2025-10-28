# Observability API Reference

This page documents the complete API for Clearstone's observability and tracing system.

## TracerProvider

The entry point for the tracing system.

```python
from clearstone.observability import TracerProvider

provider = TracerProvider(db_path="traces.db")
tracer = provider.get_tracer("my_agent", version="1.0")
```

::: clearstone.observability.provider.TracerProvider

## Tracer

Creates and manages spans.

```python
tracer = provider.get_tracer("my_agent")

with tracer.span("operation_name") as span:
    pass
```

::: clearstone.observability.tracer.Tracer

## Span Models

### Span

Represents a single operation with timing and metadata.

```python
with tracer.span("operation", attributes={"key": "value"}) as span:
    span.set_status("OK")
```

::: clearstone.observability.models.Span

### Trace

A complete execution flow (collection of spans).

```python
trace = provider.trace_store.get_trace(trace_id)

print(f"Root: {trace.root_span.name}")
for span in trace.spans:
    print(f"  - {span.name}")
```

::: clearstone.observability.models.Trace

### SpanKind

Enum defining the type of operation.

```python
from clearstone.observability import SpanKind

with tracer.span("api_call", kind=SpanKind.CLIENT):
    pass
```

::: clearstone.observability.models.SpanKind

## TraceStore

Query and analyze stored traces.

```python
trace_store = provider.trace_store

traces = trace_store.list_traces(limit=100)
trace = trace_store.get_trace(trace_id)
```

::: clearstone.storage.sqlite.TraceStore

## Storage Components

### SpanBuffer

Asynchronous buffer for batching span writes.

::: clearstone.storage.sqlite.SpanBuffer

