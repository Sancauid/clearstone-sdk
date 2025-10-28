# Core Concepts

Clearstone is built around three foundational pillars that work together to make AI agents safe, observable, and debuggable. Understanding these core concepts will help you use Clearstone effectively.

## The Three Pillars

### 1. Governance (Policy-as-Code)

**Policies** are declarative rules that control agent behavior at runtime. They intercept agent actions before they execute and decide whether to allow, block, modify, or pause them.

**Key Components:**
- **@Policy Decorator**: Turns a Python function into a policy
- **PolicyContext**: Provides metadata about the current execution
- **Decision Actions**: ALLOW, BLOCK, ALERT, PAUSE, REDACT
- **PolicyEngine**: Evaluates all policies and enforces decisions

**Example:**
```python
from clearstone import Policy, ALLOW, BLOCK

@Policy(name="cost_control", priority=100)
def cost_control_policy(context):
    session_cost = context.metadata.get("session_cost", 0.0)
    
    if session_cost > 50.0:
        return BLOCK(f"Cost limit exceeded: ${session_cost:.2f}")
    
    return ALLOW
```

### 2. Observability (Distributed Tracing)

**Tracing** captures a complete record of what your agent does at runtime. Every operation is recorded as a **span** with precise timing, inputs, outputs, and relationships to other spans.

**Key Components:**
- **TracerProvider**: Initializes the tracing system
- **Tracer**: Creates and manages spans
- **Span**: Represents a single operation with timing and metadata
- **Trace**: A complete execution flow (collection of spans)
- **TraceStore**: Persists traces to SQLite for later analysis

**Example:**
```python
from clearstone.observability import TracerProvider, SpanKind

provider = TracerProvider(db_path="traces.db")
tracer = provider.get_tracer("my_agent", version="1.0")

with tracer.span("agent_workflow", kind=SpanKind.INTERNAL) as root:
    with tracer.span("llm_call", attributes={"model": "gpt-4"}):
        result = call_llm()
    
    with tracer.span("tool_execution", attributes={"tool": "calculator"}):
        output = run_tool()

provider.shutdown()
```

### 3. Debugging (Time-Travel & Testing)

**Checkpointing** and **testing** allow you to debug agents retrospectively and validate behavior against historical data.

**Key Components:**
- **CheckpointManager**: Creates snapshots of agent state
- **ReplayEngine**: Restores agent state and re-executes from any point
- **PolicyTestHarness**: Tests policies against historical traces
- **Behavioral Assertions**: Declarative tests for agent behavior

**Example:**
```python
from clearstone.debugging import CheckpointManager, ReplayEngine

manager = CheckpointManager()
checkpoint = manager.create_checkpoint(agent, trace, span_id="span_abc")

engine = ReplayEngine(checkpoint)
engine.start_debugging_session("process_next_step", input_data)
```

## Core Abstractions

### PolicyContext

The `PolicyContext` is the data structure passed to every policy function. It provides information about the current execution:

```python
@dataclass
class PolicyContext:
    user_id: str
    agent_id: str
    timestamp: float
    metadata: Dict[str, Any]
```

**Metadata** is where you pass operation-specific data:
```python
context = create_context(
    user_id="user_123",
    agent_id="research_agent",
    metadata={
        "tool_name": "web_search",
        "session_cost": 12.50,
        "user_role": "admin"
    }
)
```

### Decision Actions

Policies return a **Decision** that tells the engine what to do:

| Action | Behavior | Use Case |
|--------|----------|----------|
| **ALLOW** | Continue execution normally | Default - no issues detected |
| **BLOCK** | Stop execution immediately, raise error | Prevent dangerous or unauthorized actions |
| **ALERT** | Continue but log a warning | Monitor suspicious behavior |
| **PAUSE** | Stop and wait for human approval | Require manual review for high-stakes operations |
| **REDACT** | Continue but remove sensitive fields | Protect PII in outputs |

**Example:**
```python
from clearstone import ALLOW, BLOCK, ALERT, PAUSE, REDACT

return ALLOW

return BLOCK("User not authorized")

return ALERT

return PAUSE("Manual approval required for $10k transaction")

return REDACT(reason="PII protection", fields=["ssn", "credit_card"])
```

### Traces and Spans

A **trace** represents a complete agent execution. A **span** represents a single operation within that trace.

**Span Hierarchy:**
```
Trace: research_workflow
├── Span: agent_execution
│   ├── Span: plan_generation
│   ├── Span: web_search (tool)
│   └── Span: synthesis
```

**Span Attributes:**
```python
with tracer.span("llm_call", attributes={
    "model": "gpt-4",
    "temperature": 0.7,
    "tokens": 1500,
    "cost": 0.045
}) as span:
    result = call_llm()
```

### Checkpoints

A **checkpoint** is a snapshot of agent state at a specific moment in time. It includes:
- Agent's complete internal state
- The trace context (all parent spans)
- Metadata about the execution point
- Timestamp and version information

**Creating a Checkpoint:**
```python
from clearstone.debugging import CheckpointManager

manager = CheckpointManager(checkpoint_dir=".checkpoints")

checkpoint = manager.create_checkpoint(
    agent=my_agent,
    trace=execution_trace,
    span_id="span_xyz"
)

checkpoint_path = manager.save_checkpoint(checkpoint)
```

**Loading a Checkpoint:**
```python
checkpoint = manager.load_checkpoint("t1_ckpt_abc123.ckpt")

restored_agent = checkpoint.agent
execution_context = checkpoint.trace
```

## How They Work Together

The three pillars integrate seamlessly:

1. **Tracing captures everything** your agent does
2. **Policies enforce rules** at runtime
3. **Testing validates behavior** against historical traces
4. **Checkpoints enable time-travel debugging**

**Complete Example:**
```python
from clearstone import Policy, BLOCK, ALLOW, PolicyEngine, create_context, context_scope
from clearstone.observability import TracerProvider
from clearstone.testing import PolicyTestHarness, assert_tool_was_called

@Policy(name="block_expensive_tools", priority=100)
def block_expensive_tools(context):
    tool_name = context.metadata.get("tool_name")
    if tool_name == "gpt4_turbo":
        return BLOCK("Expensive tool blocked")
    return ALLOW

provider = TracerProvider(db_path="traces.db")
tracer = provider.get_tracer("cost_conscious_agent")
engine = PolicyEngine()

with tracer.span("agent_run"):
    context = create_context(
        user_id="user_1",
        agent_id="agent_1",
        metadata={"tool_name": "gpt4_turbo"}
    )
    
    with context_scope(context):
        try:
            engine.evaluate(context)
        except Exception as e:
            print(f"Blocked: {e}")

provider.shutdown()

harness = PolicyTestHarness("traces.db")
traces = harness.load_traces()
result = harness.simulate_policy(
    assert_tool_was_called("gpt4_turbo", times=0),
    traces
)
```

## Key Design Principles

### 1. Declarative Over Imperative
Policies are written as simple functions, not complex state machines. You declare *what* should happen, not *how* to enforce it.

### 2. Zero Performance Impact
Tracing uses asynchronous batching and thread-safe operations to ensure zero impact on agent execution speed.

### 3. Composability
Policies can be combined using `compose_and` and `compose_or` to build complex rules from simple parts.

### 4. Fail-Safe Defaults
If a policy throws an error, the engine defaults to **ALLOW** and logs the error. The system never crashes due to a policy bug.

### 5. Testability First
Every feature is designed to be testable. Policies can be validated before deployment, and agent behavior can be tested against historical data.

## Next Steps

- **[Governance Guide](governance.md)**: Deep dive into writing and composing policies
- **[Observability Guide](observability.md)**: Master distributed tracing
- **[Testing Guide](testing.md)**: Learn behavioral testing and backtesting
- **[Time-Travel Debugging](time-travel-debugging.md)**: Debug agents by traveling back in time

