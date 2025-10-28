# Getting Started

Welcome to Clearstone! This 5-minute quickstart will guide you through the basics of protecting your AI agents with policy governance and distributed tracing.

## Installation

Clearstone requires Python 3.10 or higher.

```bash
pip install clearstone-sdk
```

## Your First Policy-Protected Agent

Let's build a simple agent that's protected by a policy. This example will show you how policies can prevent unauthorized actions before they happen.

### Step 1: Define Your Policies

Create a new file called `policies.py`:

```python
from clearstone import Policy, ALLOW, BLOCK

@Policy(name="block_dangerous_operations", priority=100)
def block_dangerous_operations(context):
    """Prevent the agent from executing dangerous file operations."""
    tool_name = context.metadata.get("tool_name", "")
    
    dangerous_operations = ["delete_file", "format_drive", "drop_table"]
    
    if any(op in tool_name.lower() for op in dangerous_operations):
        return BLOCK(f"Dangerous operation '{tool_name}' is not allowed.")
    
    return ALLOW
```

### Step 2: Set Up the Policy Engine

Create your main application file `main.py`:

```python
from clearstone import (
    PolicyEngine,
    create_context,
    context_scope,
    PolicyViolationError
)
from clearstone.integrations.langchain import PolicyCallbackHandler

import policies

engine = PolicyEngine()
handler = PolicyCallbackHandler(engine)

def run_agent_task(tool_name: str):
    """Simulate running an agent task with a specific tool."""
    print(f"\n--- Attempting to use tool: '{tool_name}' ---")
    
    context = create_context(
        user_id="user_123",
        agent_id="file_management_agent",
        metadata={"tool_name": tool_name}
    )
    
    try:
        with context_scope(context):
            handler.on_tool_start(
                serialized={"name": tool_name},
                input_str="process_task"
            )
        
        print("✅ SUCCESS: Operation approved by policies.")
        
    except PolicyViolationError as e:
        print(f"❌ BLOCKED: {e.decision.reason}")

run_agent_task("read_file")
run_agent_task("delete_file")
```

### Step 3: Run It

```bash
python main.py
```

**Output:**
```
--- Attempting to use tool: 'read_file' ---
✅ SUCCESS: Operation approved by policies.

--- Attempting to use tool: 'delete_file' ---
❌ BLOCKED: Dangerous operation 'delete_file' is not allowed.
```

That's it! Your agent is now protected by a policy that prevents dangerous operations.

## Adding Distributed Tracing

Now let's add observability to see exactly what your agent is doing.

### Step 4: Instrument with Tracing

Update your `main.py` to include tracing:

```python
from clearstone.observability import TracerProvider, SpanKind

provider = TracerProvider(db_path="agent_traces.db")
tracer = provider.get_tracer("file_management_agent", version="1.0")

def run_agent_task_with_tracing(tool_name: str):
    """Run an agent task with both policies and tracing."""
    
    with tracer.span("agent_task", kind=SpanKind.INTERNAL) as root_span:
        print(f"\n--- Task: {tool_name} (Trace ID: {root_span.trace_id}) ---")
        
        context = create_context(
            user_id="user_123",
            agent_id="file_management_agent",
            metadata={"tool_name": tool_name}
        )
        
        try:
            with context_scope(context):
                with tracer.span("policy_check", attributes={"tool": tool_name}):
                    handler.on_tool_start(
                        serialized={"name": tool_name},
                        input_str="process_task"
                    )
                
                with tracer.span("tool_execution", attributes={"tool": tool_name}):
                    print(f"Executing {tool_name}...")
            
            print("✅ SUCCESS: Task completed.")
            
        except PolicyViolationError as e:
            root_span.set_status("ERROR")
            print(f"❌ BLOCKED: {e.decision.reason}")

run_agent_task_with_tracing("read_file")
run_agent_task_with_tracing("delete_file")

provider.shutdown()
```

### Step 5: Query Your Traces

After running your agent, you can query the traces from the SQLite database:

```python
from clearstone.observability import TracerProvider

provider = TracerProvider(db_path="agent_traces.db")
traces = provider.trace_store.list_traces(limit=10)

for trace in traces:
    print(f"Trace ID: {trace.trace_id}")
    print(f"Root Span: {trace.root_span.name}")
    print(f"Duration: {trace.root_span.duration_ms:.2f}ms")
    print(f"Status: {trace.root_span.status}")
    print("---")
```

## Testing Your Policies

Use the testing framework to validate your agent's behavior:

```python
from clearstone.testing import PolicyTestHarness, assert_tool_was_called, assert_no_errors_in_trace

harness = PolicyTestHarness("agent_traces.db")
traces = harness.load_traces()

read_file_check = assert_tool_was_called("read_file", times=1)
no_errors_check = assert_no_errors_in_trace()

result = harness.simulate_policy(read_file_check, traces)
summary = result.summary()

if summary["runs_blocked"] == 0:
    print("✅ Test passed: Agent used read_file correctly")
else:
    print(f"❌ Test failed: {summary['runs_blocked']} traces blocked")
```

## What's Next?

You've now created a policy-protected agent with full observability and testing! Here are some next steps:

- **[Core Concepts](guide/core-concepts.md)**: Understand the three pillars of Clearstone
- **[Pre-Built Policies](policies.md)**: Explore 17+ production-ready policies
- **[Governance Guide](guide/governance.md)**: Learn about all policy decision types (BLOCK, ALERT, PAUSE, REDACT)
- **[Observability Guide](guide/observability.md)**: Deep dive into distributed tracing
- **[Testing Guide](guide/testing.md)**: Master behavioral assertions and backtesting
- **[Time-Travel Debugging](guide/time-travel-debugging.md)**: Debug agents by traveling back in time

## Getting Help

- **Documentation**: You're reading it! Browse the sections in the navigation.
- **GitHub Issues**: Report bugs or request features at [github.com/your-repo/clearstone-sdk](https://github.com/your-repo/clearstone-sdk)
- **Examples**: Check out the `examples/` directory in the repository for more complete demonstrations.

