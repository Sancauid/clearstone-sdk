# Time-Travel Debugging

The Time-Travel Debugging pillar allows you to capture complete agent state snapshots and replay execution from any point in history. This enables debugging agents in ways that weren't possible before.

## The Checkpoint System

A **checkpoint** is a complete snapshot of your agent's state at a specific moment in execution. It includes:
- Agent's internal state (memory, configuration, variables)
- Full trace context (all parent spans up to that point)
- Execution metadata (timestamp, version, span ID)
- Serialized state (JSON metadata + pickle state)

## CheckpointManager

The `CheckpointManager` creates, saves, and loads checkpoints.

### Initialization

```python
from clearstone.debugging import CheckpointManager

manager = CheckpointManager(checkpoint_dir=".checkpoints")
```

### Creating a Checkpoint

```python
from clearstone.observability import TracerProvider

provider = TracerProvider(db_path="traces.db")
tracer = provider.get_tracer("my_agent", version="1.0")

with tracer.span("agent_workflow") as root_span:
    trace_id = root_span.trace_id
    
    with tracer.span("step_1") as span1:
        agent.process_step_1()
    
    with tracer.span("step_2") as span2:
        span_id = span2.span_id
        agent.process_step_2()

provider.shutdown()

trace = provider.trace_store.get_trace(trace_id)

checkpoint = manager.create_checkpoint(
    agent=agent,
    trace=trace,
    span_id=span_id
)

checkpoint_path = manager.save_checkpoint(checkpoint)
print(f"Checkpoint saved: {checkpoint_path}")
```

### Loading a Checkpoint

```python
checkpoint = manager.load_checkpoint("t1_ckpt_abc123.ckpt")

print(f"Agent Type: {checkpoint.agent_class_name}")
print(f"Trace ID: {checkpoint.trace.trace_id}")
print(f"Span ID: {checkpoint.span_id}")
print(f"Timestamp: {checkpoint.timestamp}")
```

## ReplayEngine

The `ReplayEngine` restores agent state from a checkpoint and enables interactive debugging.

### Basic Replay

```python
from clearstone.debugging import ReplayEngine

checkpoint = manager.load_checkpoint("t1_ckpt_abc123.ckpt")

engine = ReplayEngine(checkpoint)

result = engine.replay_from_checkpoint(
    function_name="process_next_step",
    *args,
    **kwargs
)
```

### Interactive Debugging Session

The `start_debugging_session` method drops you into an interactive `pdb` session with the restored agent state:

```python
engine = ReplayEngine(checkpoint)

engine.start_debugging_session(
    function_to_replay="process_next_step",
    input_data={"query": "test"}
)
```

**When you run this:**
```
> /path/to/agent.py(42)process_next_step()
-> result = self.process(input_data)
(Pdb) print(self.memory)
[{'role': 'user', 'content': 'previous message'}]
(Pdb) next
> /path/to/agent.py(43)process_next_step()
-> return result
(Pdb) continue
```

## Agent Requirements

For agents to be checkpointable, they must implement two methods:

### get_state()

Returns a dictionary of all state to preserve:

```python
class MyAgent:
    def get_state(self):
        """Return complete agent state."""
        return {
            "memory": self.memory,
            "config": self.config,
            "tool_history": self.tool_history,
            "session_cost": self.session_cost
        }
```

### load_state()

Restores agent from a state dictionary:

```python
class MyAgent:
    def load_state(self, state):
        """Restore agent from state dictionary."""
        self.memory = state["memory"]
        self.config = state["config"]
        self.tool_history = state["tool_history"]
        self.session_cost = state["session_cost"]
```

### Automatic State Capture

If your agent doesn't implement these methods, Clearstone automatically captures `__dict__`:

```python
class SimpleAgent:
    def __init__(self):
        self.memory = []
        self.count = 0
```

## Deterministic Replay

The `DeterministicExecutionContext` mocks non-deterministic functions to ensure reproducible debugging.

### Automatically Mocked Functions

When replaying from a checkpoint, these are automatically mocked:

**Time Functions:**
```python
import time

time.time()
time.time_ns()
datetime.datetime.now()
```

**Random Functions:**
```python
import random

random.random()
random.randint(1, 10)
random.choice([1, 2, 3])
```

**LLM Responses:**
```python
response = call_llm("prompt")
```

### Custom Deterministic Values

Override mocked values:

```python
from clearstone.debugging import DeterministicExecutionContext

context = DeterministicExecutionContext(
    checkpoint=checkpoint,
    fixed_time=1609459200.0,
    fixed_random_seed=42,
    replayed_llm_responses={
        "prompt_1": "mocked_response_1",
        "prompt_2": "mocked_response_2"
    }
)

with context:
    result = agent.run()
```

## Complete Example

### 1. Create Agent with Checkpointing

```python
from clearstone.observability import TracerProvider
from clearstone.debugging import CheckpointManager

class ResearchAgent:
    def __init__(self):
        self.memory = []
        self.total_cost = 0.0
    
    def get_state(self):
        return {
            "memory": self.memory,
            "total_cost": self.total_cost
        }
    
    def load_state(self, state):
        self.memory = state["memory"]
        self.total_cost = state["total_cost"]
    
    def research(self, query):
        self.memory.append({"query": query})
        result = self.call_llm(query)
        self.memory.append({"result": result})
        return result
    
    def call_llm(self, prompt):
        return f"Answer to: {prompt}"

agent = ResearchAgent()

provider = TracerProvider(db_path="research_traces.db")
tracer = provider.get_tracer("research_agent")

with tracer.span("research_workflow") as root_span:
    trace_id = root_span.trace_id
    
    with tracer.span("query_1"):
        agent.research("What is AI safety?")
    
    with tracer.span("query_2") as span:
        checkpoint_span_id = span.span_id
        agent.research("What are the risks?")

provider.shutdown()

manager = CheckpointManager()
trace = provider.trace_store.get_trace(trace_id)
checkpoint = manager.create_checkpoint(agent, trace, checkpoint_span_id)
checkpoint_path = manager.save_checkpoint(checkpoint)

print(f"Checkpoint saved: {checkpoint_path}")
```

### 2. Debug from Checkpoint

```python
from clearstone.debugging import CheckpointManager, ReplayEngine

manager = CheckpointManager()
checkpoint = manager.load_checkpoint(checkpoint_path)

print(f"Agent Memory at Checkpoint:")
for item in checkpoint.agent_state["memory"]:
    print(f"  {item}")

engine = ReplayEngine(checkpoint)

engine.start_debugging_session(
    function_to_replay="research",
    query="What are AI alignment solutions?"
)
```

## Advanced Features

### Checkpoint Metadata

Checkpoints include rich metadata:

```python
checkpoint = manager.load_checkpoint("checkpoint.ckpt")

print(f"Created: {checkpoint.timestamp}")
print(f"Agent: {checkpoint.agent_class_name}")
print(f"Module: {checkpoint.agent_module}")
print(f"Trace ID: {checkpoint.trace.trace_id}")
print(f"Span: {checkpoint.span_id}")
```

### Upstream Span Tracking

Checkpoints capture the complete parent span hierarchy:

```python
checkpoint = manager.load_checkpoint("checkpoint.ckpt")

print("Execution History:")
for span in checkpoint.trace.spans:
    print(f"  {span.name} ({span.duration_ms:.2f}ms)")
    print(f"    Attributes: {span.attributes}")
```

### Checkpoint Comparison

Compare agent state at different points:

```python
checkpoint_1 = manager.load_checkpoint("ckpt_step1.ckpt")
checkpoint_2 = manager.load_checkpoint("ckpt_step2.ckpt")

state_1 = checkpoint_1.agent_state
state_2 = checkpoint_2.agent_state

print("Memory Growth:")
print(f"  Step 1: {len(state_1['memory'])} items")
print(f"  Step 2: {len(state_2['memory'])} items")

print("Cost Delta:")
print(f"  Step 1: ${state_1['total_cost']:.2f}")
print(f"  Step 2: ${state_2['total_cost']:.2f}")
print(f"  Delta: ${state_2['total_cost'] - state_1['total_cost']:.2f}")
```

### Conditional Checkpointing

Create checkpoints only when specific conditions are met:

```python
with tracer.span("risky_operation") as span:
    try:
        result = agent.risky_operation()
    except Exception as e:
        span.set_status("ERROR")
        
        provider.shutdown()
        trace = provider.trace_store.get_trace(span.trace_id)
        
        checkpoint = manager.create_checkpoint(agent, trace, span.span_id)
        checkpoint_path = manager.save_checkpoint(checkpoint)
        
        print(f"Error checkpoint saved: {checkpoint_path}")
        raise
```

## Debugging Workflows

### Debugging a Bug

1. **Reproduce the bug with tracing enabled**
```python
provider = TracerProvider(db_path="bug_trace.db")
tracer = provider.get_tracer("agent")

with tracer.span("workflow") as root:
    try:
        agent.run_workflow()
    except BuggyBehaviorError as e:
        checkpoint_span_id = root.span_id
```

2. **Create checkpoint at failure point**
```python
provider.shutdown()
trace = provider.trace_store.get_trace(root.trace_id)
checkpoint = manager.create_checkpoint(agent, trace, checkpoint_span_id)
manager.save_checkpoint(checkpoint)
```

3. **Load checkpoint and debug**
```python
checkpoint = manager.load_checkpoint("checkpoint.ckpt")
engine = ReplayEngine(checkpoint)
engine.start_debugging_session("run_workflow")
```

### Performance Debugging

Find slow operations:

```python
trace = trace_store.get_trace(trace_id)

slow_spans = [
    span for span in trace.spans
    if span.duration_ms > 1000
]

for span in slow_spans:
    checkpoint = manager.create_checkpoint(agent, trace, span.span_id)
    
    print(f"Created checkpoint before slow operation: {span.name}")
    print(f"  Duration: {span.duration_ms:.2f}ms")
```

## Best Practices

### 1. Checkpoint Before Critical Operations

```python
with tracer.span("critical_operation") as span:
    checkpoint = manager.create_checkpoint(agent, trace, span.span_id)
    agent.critical_operation()
```

### 2. Name Checkpoints Descriptively

```python
checkpoint_path = manager.save_checkpoint(
    checkpoint,
    filename=f"before_payment_{transaction_id}.ckpt"
)
```

### 3. Clean Up Old Checkpoints

```python
import os
import time

checkpoint_dir = ".checkpoints"
max_age_days = 30

for filename in os.listdir(checkpoint_dir):
    path = os.path.join(checkpoint_dir, filename)
    age_days = (time.time() - os.path.getmtime(path)) / 86400
    
    if age_days > max_age_days:
        os.remove(path)
```

### 4. Use Version Control for Checkpoints

```bash
# .gitignore
.checkpoints/*.ckpt

# Keep only representative checkpoints in version control
git add .checkpoints/baseline_v1.ckpt
```

### 5. Document Checkpoint Purpose

```python
checkpoint.metadata["purpose"] = "Before prod deployment 2024-01-15"
checkpoint.metadata["ticket"] = "JIRA-123"
checkpoint.metadata["notes"] = "Agent was experiencing high costs"
```

## Next Steps

- **[Observability Guide](observability.md)**: Learn about distributed tracing
- **[Testing Guide](testing.md)**: Test policies with backtesting
- **[API Reference](../api/debugging.md)**: Complete debugging API documentation

