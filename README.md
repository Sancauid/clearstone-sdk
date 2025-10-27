# Clearstone SDK

[![PyPI Version](https://img.shields.io/pypi/v/clearstone-sdk.svg)](https://pypi.org/project/clearstone-sdk/)
[![Build Status](https://img.shields.io/github/actions/workflow/status/your-repo/your-workflow.yml?branch=main)](https://github.com/your-repo/clearstone-sdk/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/pypi/pyversions/clearstone-sdk.svg)](https://pypi.org/project/clearstone-sdk)

**Production-Grade Governance and Observability for AI Agent Systems.**

Clearstone is a comprehensive Python SDK that provides safety, governance, and observability for multi-agent AI workflows. It combines declarative Policy-as-Code with OpenTelemetry-aligned distributed tracing to help you build reliable, debuggable, and compliant AI systems.

---

## The Problem

Autonomous AI agents are powerful but operate in a high-stakes environment. Without robust guardrails and observability, they can be:
*   **Unsafe:** Accidentally executing destructive actions (e.g., deleting files).
*   **Costly:** Over-using expensive tools or LLM tokens.
*   **Non-compliant:** Mishandling sensitive data (PII).
*   **Unpredictable:** Difficult to debug when they fail.
*   **Opaque:** No visibility into what they're actually doing at runtime.

Clearstone provides the tools to manage these risks with declarative Policy-as-Code governance and production-ready distributed tracing.

## Key Features

### Policy Governance
*   ✅ **Declarative Policy-as-Code:** Write policies as simple Python functions using the `@Policy` decorator. No YAML or complex DSLs.
*   ✅ **Seamless LangChain Integration:** Drop the `PolicyCallbackHandler` into any LangChain agent to enforce policies at runtime.
*   ✅ **Rich Pre-Built Policy Library:** Get started in minutes with 17+ production-ready policies for cost control, RBAC, PII redaction, security alerts, and more.
*   ✅ **Local LLM Protection:** Built-in policies for system load monitoring and model server health checks—specifically designed for local-first AI workflows.
*   ✅ **Human-in-the-Loop Controls:** Pause agent execution for manual approval with the `PAUSE` action and `InterventionClient` for high-stakes decisions.
*   ✅ **Pre-Deploy Validation:** Catch buggy, slow, or non-deterministic policies *before* they reach production with the `PolicyValidator`.
*   ✅ **Line-by-Line Debugging:** Understand exactly why a policy made a decision with the `PolicyDebugger`'s execution trace.
*   ✅ **Performance Metrics:** Track policy execution times, identify bottlenecks, and analyze decision patterns with `PolicyMetrics`.
*   ✅ **Composable Logic:** Build complex rules from simple, reusable policies with `compose_and` and `compose_or` helpers.
*   ✅ **Exportable Audit Trails:** Generate JSON or CSV audit logs for every policy decision, perfect for compliance and analysis.
*   ✅ **Developer CLI:** Accelerate development by scaffolding new, well-structured policy files with the `clearstone new-policy` command.

### Observability & Tracing
*   ✅ **Production-Ready Tracing:** OpenTelemetry-aligned distributed tracing for complete agent execution visibility.
*   ✅ **Automatic Hierarchy Tracking:** Nested spans automatically establish parent-child relationships without manual configuration.
*   ✅ **High-Fidelity Capture:** Nanosecond-precision timing, input/output snapshots, and full error stack traces.
*   ✅ **Thread-Safe Persistence:** SQLite storage with Write-Ahead Logging (WAL) for concurrent-safe trace storage.
*   ✅ **Asynchronous Batching:** Non-blocking span capture with automatic batch writes for zero performance impact.
*   ✅ **Hybrid Serialization:** Smart JSON-first serialization with automatic pickle fallback for complex objects.
*   ✅ **Single-Line Setup:** Initialize the entire tracing system with one `TracerProvider` instantiation.

## Installation

The SDK requires Python 3.10+.

```bash
pip install clearstone-sdk
```

## 5-Minute Quickstart

See how easy it is to protect an agent from performing unauthorized actions.

#### 1. Define Your Policies

Create a file `my_app/policies.py`. Our policies will check a user's role before allowing access to a tool.

```python
# my_app/policies.py
from clearstone import Policy, ALLOW, BLOCK

@Policy(name="block_admin_tools_for_guests", priority=100)
def block_admin_tools_policy(context):
    """A high-priority policy to enforce Role-Based Access Control (RBAC)."""
    
    # Policies read data from the context's metadata
    role = context.metadata.get("role")
    tool_name = context.metadata.get("tool_name")

    if role == "guest" and tool_name == "admin_panel":
        return BLOCK(f"Role '{role}' is not authorized to access '{tool_name}'.")
    
    return ALLOW
```

#### 2. Integrate with Your Agent

In your main application file, initialize the engine and add the `PolicyCallbackHandler` to your agent call.

```python
# my_app/main.py
from clearstone import (
    create_context,
    context_scope,
    PolicyEngine,
    PolicyViolationError
)
from clearstone.integrations.langchain import PolicyCallbackHandler

# This import discovers and registers the policies we just wrote
import my_app.policies

# --- Setup Clearstone (do this once) ---
engine = PolicyEngine()
handler = PolicyCallbackHandler(engine)

def run_agent_with_tool(user_role: str):
    """Simulates running an agent for a user with a specific role."""
    print(f"\n--- Running agent for user with role: '{user_role}' ---")

    # 1. Create a context for this specific run
    context = create_context(
        user_id=f"user_{user_role}",
        agent_id="admin_agent_v1",
        metadata={"role": user_role}
    )

    try:
        # 2. Run the agent within the context scope and with the handler
        with context_scope(context):
            # In a real app, this would be: agent.invoke(..., callbacks=[handler])
            # We simulate the tool call for this example:
            print("Agent is attempting to access 'admin_panel' tool...")
            handler.on_tool_start(serialized={"name": "admin_panel"}, input_str="")
        
        print("✅ SUCCESS: Agent action was approved by all policies.")

    except PolicyViolationError as e:
        # 3. Handle policy violations gracefully
        print(f"❌ BLOCKED: The action was stopped by a policy.")
        print(f"   Reason: {e.decision.reason}")

# --- Run Scenarios ---
run_agent_with_tool("admin")
run_agent_with_tool("guest")
```

#### 3. Run and See the Result
```
--- Running agent for user with role: 'admin' ---
Agent is attempting to access 'admin_panel' tool...
✅ SUCCESS: Agent action was approved by all policies.

--- Running agent for user with role: 'guest' ---
Agent is attempting to access 'admin_panel' tool...
❌ BLOCKED: The action was stopped by a policy.
   Reason: Role 'guest' is not authorized to access 'admin_panel'.
```

## The Developer Toolkit

Clearstone is more than just an engine; it's a complete toolkit for policy governance.

#### 1. Composing Policies
Build complex logic from simple, reusable parts.
```python
from clearstone import compose_and
from clearstone.policies.common import token_limit_policy, cost_limit_policy

# This new policy only passes if BOTH underlying policies pass.
safe_and_cheap_policy = compose_and(token_limit_policy, cost_limit_policy)
```

#### 2. Validating Policies Before Deployment
Catch bugs before they reach production. The validator checks for slowness, non-determinism, and fragility.
```python
from clearstone import PolicyValidator

validator = PolicyValidator()
failures = validator.run_all_checks(my_buggy_policy)

if failures:
    print("Policy failed validation:", failures)
else:
    print("Policy is ready for production!")
```

#### 3. Debugging Policy Decisions
Understand *why* a policy made a specific decision with a line-by-line execution trace.
```python
from clearstone import PolicyDebugger

debugger = PolicyDebugger()
decision, trace = debugger.trace_evaluation(my_complex_policy, context)

# Print a human-readable report
print(debugger.format_trace(my_complex_policy, decision, trace))
```

#### 4. Performance Monitoring
Track policy performance and identify bottlenecks with real-time metrics.
```python
from clearstone import PolicyMetrics

metrics = PolicyMetrics()
engine = PolicyEngine(metrics=metrics)

# ... run agent ...

# Get performance summary
summary = metrics.summary()
print(f"Policy 'token_limit' avg latency: {summary['token_limit']['avg_latency_ms']:.4f}ms")

# Find slowest policies
slowest = metrics.get_slowest_policies(top_n=5)
for policy_name, stats in slowest:
    print(f"{policy_name}: {stats['avg_latency_ms']:.4f}ms")

# Find policies that block most often
top_blockers = metrics.get_top_blocking_policies(top_n=5)
```

#### 5. Human-in-the-Loop Interventions
Pause agent execution for manual approval on high-stakes operations like financial transactions or destructive actions.
```python
import dataclasses
from clearstone import (
  Policy, PolicyEngine, create_context, context_scope,
  ALLOW, PAUSE, InterventionClient
)
from clearstone.integrations.langchain import PolicyCallbackHandler, PolicyPauseError

@Policy(name="require_approval_for_large_spend", priority=100)
def approval_policy(context):
  amount = context.metadata.get("amount", 0)
  is_approved = context.metadata.get("is_approved", False)
  
  if amount > 1000 and not is_approved:
    return PAUSE(f"Transaction of ${amount} requires manual approval.")
  
  return ALLOW

def run_transaction(engine, context):
  handler = PolicyCallbackHandler(engine)
  
  try:
    with context_scope(context):
      handler.on_tool_start(serialized={"name": "execute_payment"}, input_str="")
    print("✅ Transaction successful")
    return True
  
  except PolicyPauseError as e:
    print(f"⏸️ Transaction paused: {e.decision.reason}")
    
    intervention_client = InterventionClient()
    intervention_client.request_intervention(e.decision)
    intervention_id = e.decision.metadata.get("intervention_id")
    
    if intervention_client.wait_for_approval(intervention_id):
      # User approved - retry with approval flag
      approved_context = dataclasses.replace(
        context, 
        metadata={**context.metadata, "is_approved": True}
      )
      return run_transaction(engine, approved_context)
    else:
      print("❌ Transaction rejected by user")
      return False

engine = PolicyEngine()
ctx = create_context("user-1", "finance-agent", amount=2500)
run_transaction(engine, ctx)
```

#### 6. Auditing and Exporting
The `PolicyEngine` automatically captures a detailed audit trail. You can analyze it or export it for compliance.
```python
from clearstone import AuditTrail

audit = AuditTrail()
engine = PolicyEngine(audit_trail=audit)

# ... run agent ...

# Get a quick summary
print(audit.summary())
# {'total_decisions': 50, 'blocks': 5, 'alerts': 12, 'block_rate': 0.1}

# Export for external analysis
audit.to_json("audit_log.json")
audit.to_csv("audit_log.csv")
```

## Distributed Tracing & Observability

Clearstone provides production-grade distributed tracing to understand exactly what your AI agents are doing at runtime.

#### Quick Start: Trace Your Agent
```python
from clearstone.observability import TracerProvider, SpanKind

# Initialize once at application startup
provider = TracerProvider(db_path="traces.db")
tracer = provider.get_tracer("my_agent", version="1.0")

# Trace operations with automatic hierarchy
with tracer.span("agent_execution", kind=SpanKind.INTERNAL) as root_span:
    # Nested spans automatically link to parents
    with tracer.span("llm_call", kind=SpanKind.CLIENT, attributes={"model": "gpt-4"}) as llm_span:
        result = call_llm()
    
    with tracer.span("tool_execution", attributes={"tool": "calculator"}):
        output = run_tool()

# Spans are automatically persisted to SQLite
# Retrieve traces for analysis
trace = provider.trace_store.get_trace(root_span.trace_id)
```

#### Key Capabilities

**Automatic Parent-Child Linking**
```python
# No manual span IDs needed - hierarchy is automatic
with tracer.span("parent_operation"):
    with tracer.span("child_operation"):
        with tracer.span("grandchild_operation"):
            pass  # Three-level hierarchy created automatically
```

**Rich Span Attributes**
```python
with tracer.span("llm_call", attributes={
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 1000
}) as span:
    # Attributes are searchable in storage
    result = call_llm()
```

**Exception Tracking**
```python
with tracer.span("risky_operation") as span:
    raise ValueError("Something went wrong")
# Span automatically captures:
# - status: ERROR
# - error_message: "Something went wrong"
# - error_stacktrace: full traceback
```

**Performance Characteristics**
- ⚡ **Non-blocking:** Span capture takes < 1μs
- 🔄 **Batched writes:** Groups 100 spans per transaction
- 🔒 **Thread-safe:** Multiple threads can trace concurrently
- 💾 **Efficient storage:** SQLite with WAL mode for concurrent reads

## Command-Line Interface (CLI)

Accelerate development with the `clearstone` CLI. The `new-policy` command scaffolds a boilerplate file with best practices.

```bash
# See all available commands
clearstone --help

# Create a new policy file
clearstone new-policy enforce_data_locality --priority=80 --dir=my_app/compliance

# Output: Creates my_app/compliance/enforce_data_locality_policy.py
```
```python
# my_app/compliance/enforce_data_locality_policy.py
from clearstone import Policy, ALLOW, BLOCK, Decision
# ... boilerplate ...

@Policy(name="enforce_data_locality", priority=80)
def enforce_data_locality_policy(context: PolicyContext) -> Decision:
    """
    [TODO: Describe what this policy does.]
    """
    # [TODO: Implement your policy logic here.]
    return ALLOW
```

## For Local LLM Users

Clearstone includes specialized policies designed specifically for local-first AI workflows. These address the unique challenges of running large language models on local hardware:

### System Load Protection

Prevents system freezes by monitoring CPU and memory usage before allowing intensive operations:

```python
from clearstone.policies.common import system_load_policy

# Automatically blocks operations when:
# - CPU usage > 90% (configurable)
# - Memory usage > 95% (configurable)

context = create_context(
    "user", "agent",
    cpu_threshold_percent=85.0,      # Custom threshold
    memory_threshold_percent=90.0
)
```

### Model Health Check

Provides instant feedback when your local model server is down, avoiding mysterious 60-second timeouts:

```python
from clearstone.policies.common import model_health_check_policy

# Quick health check (0.5s timeout) before LLM calls
# Supports Ollama, LM Studio, and custom endpoints

context = create_context(
    "user", "agent",
    local_model_health_url="http://localhost:11434/api/tags",  # Ollama default
    health_check_timeout=1.0
)
```

**Why This Matters:**
- ❌ No more system freezes from resource exhaustion
- ❌ No more waiting 60 seconds for timeout errors  
- ✅ Immediate, actionable error messages
- ✅ Prevents retry loops that make problems worse

See `examples/16_local_llm_protection.py` for a complete demonstration.

---

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to submit pull requests, set up a development environment, and run tests.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.