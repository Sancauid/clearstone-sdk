# Observability

The Observability pillar provides production-grade distributed tracing for AI agents. This guide covers everything you need to instrument, trace, and analyze agent execution.

## Quick Start

Initialize tracing in three lines:

```python
from clearstone.observability import TracerProvider

provider = TracerProvider(db_path="traces.db")
tracer = provider.get_tracer("my_agent", version="1.0")

with tracer.span("agent_workflow"):
    pass

provider.shutdown()
```

## TracerProvider

The `TracerProvider` is the entry point for the tracing system.

### Initialization

```python
from clearstone.observability import TracerProvider

provider = TracerProvider(
    db_path="agent_traces.db",
    service_name="production_agent",
    batch_size=100,
    flush_interval_seconds=5.0
)
```

**Parameters:**
- `db_path`: Path to SQLite database for trace storage
- `service_name`: Name of your service (default: "clearstone")
- `batch_size`: Number of spans to batch before writing (default: 100)
- `flush_interval_seconds`: How often to flush spans (default: 5.0)

### Shutdown

Always call `shutdown()` to flush remaining spans:

```python
provider.shutdown()
```

## Creating Tracers

Get a tracer instance for your agent:

```python
tracer = provider.get_tracer(
    name="research_agent",
    version="2.1.0"
)
```

Tracers are lightweight and thread-safe. Create one per logical component.

## Creating Spans

### Basic Span

```python
with tracer.span("operation_name") as span:
    result = do_work()
```

### Span with Attributes

```python
with tracer.span("llm_call", attributes={
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 1000,
    "cost": 0.045
}) as span:
    result = call_llm()
```

### Span Kinds

Specify the type of operation:

```python
from clearstone.observability import SpanKind

with tracer.span("agent_workflow", kind=SpanKind.INTERNAL):
    pass

with tracer.span("api_call", kind=SpanKind.CLIENT):
    pass

with tracer.span("database_query", kind=SpanKind.CLIENT):
    pass
```

**SpanKind values:**
- `INTERNAL`: Default - internal operation
- `CLIENT`: Outbound call (API, database, LLM)
- `SERVER`: Inbound request
- `PRODUCER`: Message queue producer
- `CONSUMER`: Message queue consumer

## Automatic Hierarchy

Nested spans automatically link to their parents:

```python
with tracer.span("parent_operation") as parent:
    print(f"Parent Trace ID: {parent.trace_id}")
    
    with tracer.span("child_operation") as child:
        print(f"Child Trace ID: {child.trace_id}")
        print(f"Child Parent ID: {child.parent_span_id}")
        
        with tracer.span("grandchild_operation") as grandchild:
            print(f"Grandchild Parent ID: {grandchild.parent_span_id}")
```

All spans share the same `trace_id`. Each span's `parent_span_id` points to its parent.

## Exception Tracking

Exceptions are automatically captured:

```python
with tracer.span("risky_operation") as span:
    raise ValueError("Something went wrong")
```

The span automatically records:
- `status`: ERROR
- `error_message`: "Something went wrong"
- `error_stacktrace`: Full traceback

### Manual Status Setting

```python
with tracer.span("operation") as span:
    if error_occurred:
        span.set_status("ERROR")
    else:
        span.set_status("OK")
```

## TraceStore

Query and analyze stored traces.

### Getting the TraceStore

```python
trace_store = provider.trace_store
```

### Listing Traces

```python
traces = trace_store.list_traces(limit=100)

for trace in traces:
    print(f"Trace ID: {trace.trace_id}")
    print(f"Root Span: {trace.root_span.name}")
    print(f"Duration: {trace.root_span.duration_ms:.2f}ms")
    print(f"Status: {trace.root_span.status}")
```

### Getting a Specific Trace

```python
trace = trace_store.get_trace(trace_id="abc123")

print(f"Root: {trace.root_span.name}")
for span in trace.spans:
    print(f"  - {span.name} ({span.duration_ms:.2f}ms)")
```

### Querying Spans

```python
spans = trace_store.query_spans(
    trace_id="abc123",
    name="llm_call"
)

for span in spans:
    print(f"Model: {span.attributes.get('model')}")
    print(f"Cost: ${span.attributes.get('cost'):.4f}")
```

### Filtering Traces

```python
recent_errors = trace_store.list_traces(
    limit=50,
    status="ERROR"
)

expensive_traces = [
    t for t in trace_store.list_traces()
    if t.root_span.attributes.get("cost", 0) > 1.0
]
```

## Span Attributes

### Standard Attributes

```python
with tracer.span("operation", attributes={
    "operation.type": "search",
    "operation.retries": 3,
    "resource.name": "web_search_api",
    "cost.usd": 0.05
}) as span:
    pass
```

### LLM-Specific Attributes

```python
with tracer.span("llm_call", attributes={
    "llm.model": "gpt-4-turbo",
    "llm.temperature": 0.7,
    "llm.max_tokens": 2000,
    "llm.prompt_tokens": 150,
    "llm.completion_tokens": 450,
    "llm.total_tokens": 600,
    "llm.cost_usd": 0.045
}) as span:
    pass
```

### Tool-Specific Attributes

```python
with tracer.span("tool_execution", attributes={
    "tool.name": "calculator",
    "tool.input": "2 + 2",
    "tool.output": "4",
    "tool.duration_ms": 12.5
}) as span:
    pass
```

## Performance Characteristics

### Non-Blocking Capture

Span creation takes < 1μs and doesn't block execution:

```python
import time

start = time.perf_counter()

with tracer.span("fast_operation"):
    pass

elapsed = time.perf_counter() - start
print(f"Overhead: {elapsed * 1000:.3f}ms")
```

### Batched Writes

Spans are written in batches of 100 (configurable) to minimize I/O:

```python
provider = TracerProvider(
    db_path="traces.db",
    batch_size=200,
    flush_interval_seconds=10.0
)
```

### Thread-Safe

Multiple threads can trace concurrently:

```python
import threading

def worker(tracer, worker_id):
    with tracer.span(f"worker_{worker_id}"):
        do_work()

threads = [
    threading.Thread(target=worker, args=(tracer, i))
    for i in range(10)
]

for t in threads:
    t.start()

for t in threads:
    t.join()
```

## Integration with Policies

Combine tracing with policy enforcement:

```python
from clearstone import PolicyEngine, create_context, context_scope
from clearstone.integrations.langchain import PolicyCallbackHandler

provider = TracerProvider(db_path="traces.db")
tracer = provider.get_tracer("governed_agent")
engine = PolicyEngine()
handler = PolicyCallbackHandler(engine)

with tracer.span("agent_run") as root_span:
    context = create_context(
        user_id="user_123",
        agent_id="agent_1",
        metadata={"tool_name": "web_search"}
    )
    
    with context_scope(context):
        with tracer.span("policy_check"):
            try:
                handler.on_tool_start(
                    serialized={"name": "web_search"},
                    input_str="search query"
                )
            except PolicyViolationError as e:
                root_span.set_status("ERROR")
                raise
        
        with tracer.span("tool_execution", attributes={"tool": "web_search"}):
            result = execute_tool()

provider.shutdown()
```

## Analyzing Traces

### Cost Analysis

```python
trace_store = provider.trace_store

total_cost = 0.0
for trace in trace_store.list_traces():
    for span in trace.spans:
        total_cost += span.attributes.get("cost", 0.0)

print(f"Total Cost: ${total_cost:.2f}")
```

### Performance Analysis

```python
slow_operations = []

for trace in trace_store.list_traces():
    for span in trace.spans:
        if span.duration_ms > 1000:
            slow_operations.append({
                "name": span.name,
                "duration_ms": span.duration_ms,
                "trace_id": span.trace_id
            })

slow_operations.sort(key=lambda x: x["duration_ms"], reverse=True)

for op in slow_operations[:10]:
    print(f"{op['name']}: {op['duration_ms']:.2f}ms")
```

### Error Rate Analysis

```python
total_traces = 0
error_traces = 0

for trace in trace_store.list_traces():
    total_traces += 1
    if trace.root_span.status == "ERROR":
        error_traces += 1

error_rate = error_traces / total_traces if total_traces > 0 else 0
print(f"Error Rate: {error_rate:.2%}")
```

## Export and Visualization

### Export to JSON

```python
import json

traces = trace_store.list_traces(limit=100)

trace_data = [
    {
        "trace_id": trace.trace_id,
        "root_span": trace.root_span.name,
        "duration_ms": trace.root_span.duration_ms,
        "status": trace.root_span.status,
        "spans": [
            {
                "name": span.name,
                "duration_ms": span.duration_ms,
                "attributes": span.attributes
            }
            for span in trace.spans
        ]
    }
    for trace in traces
]

with open("traces.json", "w") as f:
    json.dump(trace_data, f, indent=2)
```

### Export to CSV

```python
import csv

with open("spans.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "trace_id", "span_id", "name", "duration_ms",
        "status", "parent_span_id"
    ])
    
    for trace in trace_store.list_traces():
        for span in trace.spans:
            writer.writerow([
                span.trace_id,
                span.span_id,
                span.name,
                span.duration_ms,
                span.status,
                span.parent_span_id or ""
            ])
```

## Best Practices

### 1. Always Shutdown

```python
try:
    with tracer.span("operation"):
        do_work()
finally:
    provider.shutdown()
```

### 2. Use Meaningful Names

```python
with tracer.span("user_registration_workflow"):
    pass
```

### 3. Include Key Attributes

```python
with tracer.span("api_call", attributes={
    "http.method": "POST",
    "http.url": "https://api.example.com/users",
    "http.status_code": 201
}):
    pass
```

### 4. Set Span Status

```python
with tracer.span("operation") as span:
    try:
        result = do_work()
        span.set_status("OK")
    except Exception as e:
        span.set_status("ERROR")
        raise
```

### 5. Trace at the Right Granularity

Trace operations that are:
- Meaningful (e.g., "llm_call", not "add_two_numbers")
- Measurable (have meaningful duration)
- Observable (need monitoring)

## Next Steps

- **[Testing Guide](testing.md)**: Use traces for behavioral testing
- **[Time-Travel Debugging](time-travel-debugging.md)**: Debug with checkpoints
- **[API Reference](../api/observability.md)**: Complete API documentation

