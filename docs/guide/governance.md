# Governance

The Governance pillar provides declarative Policy-as-Code to control agent behavior at runtime. This guide covers everything you need to write, compose, debug, and deploy production-ready policies.

## The PolicyEngine

The `PolicyEngine` is the heart of the governance system. It discovers, evaluates, and enforces policies.

### Basic Setup

```python
from clearstone import PolicyEngine

engine = PolicyEngine()
```

The engine automatically discovers all policies decorated with `@Policy` that have been imported into your application.

### Evaluating Policies

```python
from clearstone import create_context

context = create_context(
    user_id="user_123",
    agent_id="research_agent",
    metadata={"tool_name": "web_search", "cost": 0.05}
)

decision = engine.evaluate(context)

if decision.action == "BLOCK":
    raise Exception(f"Action blocked: {decision.reason}")
```

## Writing Policies

### The @Policy Decorator

Every policy is a simple Python function decorated with `@Policy`:

```python
from clearstone import Policy, ALLOW, BLOCK

@Policy(name="my_policy", priority=100)
def my_policy(context):
    """Description of what this policy does."""
    
    if context.metadata.get("some_condition"):
        return BLOCK("Reason for blocking")
    
    return ALLOW
```

**Parameters:**
- `name`: Unique identifier for the policy (required)
- `priority`: Higher priority policies are evaluated first (default: 50)
- `enabled`: Whether the policy is active (default: True)

### Policy Priority

Policies are evaluated in **descending priority order** (highest first):

```python
@Policy(name="security_check", priority=100)
def security_policy(context):
    pass

@Policy(name="cost_check", priority=80)
def cost_policy(context):
    pass

@Policy(name="logging", priority=10)
def logging_policy(context):
    pass
```

Evaluation order: `security_policy` → `cost_policy` → `logging_policy`

### Short-Circuit Evaluation

The engine stops evaluating as soon as a policy returns **BLOCK** or **PAUSE**:

```python
@Policy(name="auth", priority=100)
def auth_policy(context):
    if not context.metadata.get("authenticated"):
        return BLOCK("Not authenticated")
    return ALLOW

@Policy(name="expensive_check", priority=50)
def expensive_check(context):
    pass
```

If `auth_policy` blocks, `expensive_check` is never evaluated.

## Decision Types

### ALLOW

Continue execution normally.

```python
from clearstone import ALLOW

return ALLOW
```

### BLOCK

Stop execution immediately and raise a `PolicyViolationError`.

```python
from clearstone import BLOCK

return BLOCK("User does not have permission")
```

**In LangChain:**
```python
from clearstone.integrations.langchain import PolicyCallbackHandler

handler = PolicyCallbackHandler(engine)

try:
    with context_scope(context):
        handler.on_tool_start(serialized={"name": "admin_tool"}, input_str="")
except PolicyViolationError as e:
    print(f"Blocked: {e.decision.reason}")
```

### ALERT

Continue execution but log a warning for monitoring.

```python
from clearstone import ALERT

return ALERT
```

**Best Practice:** Use `ALERT` for suspicious but not dangerous behavior:
```python
@Policy(name="suspicious_activity_monitor", priority=70)
def monitor_suspicious(context):
    failed_attempts = context.metadata.get("failed_auth_attempts", 0)
    
    if failed_attempts > 3:
        return Decision(
            ActionType.ALERT,
            reason=f"User has {failed_attempts} failed login attempts"
        )
    
    return ALLOW
```

### PAUSE

Stop execution and wait for human approval.

```python
from clearstone import PAUSE

return PAUSE("High-risk transaction requires manual approval")
```

**Human-in-the-Loop Example:**
```python
import dataclasses
from clearstone import InterventionClient
from clearstone.integrations.langchain import PolicyPauseError

@Policy(name="require_approval", priority=100)
def approval_policy(context):
    amount = context.metadata.get("transaction_amount", 0)
    is_approved = context.metadata.get("is_approved", False)
    
    if amount > 1000 and not is_approved:
        return PAUSE(f"Transaction of ${amount} requires approval")
    
    return ALLOW

def run_with_approval(engine, context):
    handler = PolicyCallbackHandler(engine)
    
    try:
        with context_scope(context):
            handler.on_tool_start(serialized={"name": "execute_payment"}, input_str="")
        return True
    
    except PolicyPauseError as e:
        print(f"⏸️ Paused: {e.decision.reason}")
        
        client = InterventionClient()
        client.request_intervention(e.decision)
        intervention_id = e.decision.metadata.get("intervention_id")
        
        if client.wait_for_approval(intervention_id):
            approved_context = dataclasses.replace(
                context,
                metadata={**context.metadata, "is_approved": True}
            )
            return run_with_approval(engine, approved_context)
        else:
            print("❌ Transaction rejected")
            return False
```

### REDACT

Continue execution but remove sensitive fields from outputs.

```python
from clearstone import REDACT

return REDACT(
    reason="PII protection",
    fields=["ssn", "credit_card", "email"]
)
```

**Usage Example:**
```python
@Policy(name="redact_pii", priority=85)
def redact_pii_policy(context):
    tool_name = context.metadata.get("tool_name")
    
    pii_tools = {
        "fetch_user": ["ssn", "credit_card"],
        "get_medical": ["diagnosis", "prescription"]
    }
    
    if tool_name in pii_tools:
        return REDACT(
            reason=f"PII redaction for {tool_name}",
            fields=pii_tools[tool_name]
        )
    
    return ALLOW
```

## Composing Policies

Build complex policies from simple, reusable parts.

### compose_and

Create a policy that only passes if **all** sub-policies pass.

```python
from clearstone import compose_and
from clearstone.policies.common import token_limit_policy, cost_limit_policy

combined_policy = compose_and(token_limit_policy, cost_limit_policy)
```

### compose_or

Create a policy that passes if **any** sub-policy passes.

```python
from clearstone import compose_or

admin_or_superuser = compose_or(admin_check_policy, superuser_check_policy)
```

### Custom Composition

For complex logic, write a new policy that delegates to others:

```python
@Policy(name="multi_stage_check", priority=100)
def multi_stage_policy(context):
    auth_result = auth_policy(context)
    if auth_result.action != "ALLOW":
        return auth_result
    
    cost_result = cost_policy(context)
    if cost_result.action != "ALLOW":
        return cost_result
    
    return ALLOW
```

## LangChain Integration

### PolicyCallbackHandler

The `PolicyCallbackHandler` is a LangChain callback that enforces policies automatically:

```python
from clearstone import PolicyEngine, create_context, context_scope
from clearstone.integrations.langchain import PolicyCallbackHandler
from langchain.agents import AgentExecutor

engine = PolicyEngine()
handler = PolicyCallbackHandler(engine)

context = create_context(
    user_id="user_123",
    agent_id="my_agent",
    metadata={"role": "user", "session_cost": 0.0}
)

with context_scope(context):
    result = agent.invoke(
        {"input": "Search for AI safety papers"},
        callbacks=[handler]
    )
```

### Intercepted Events

The handler intercepts these LangChain events:
- `on_tool_start`: Before a tool is called
- `on_llm_start`: Before an LLM call
- `on_chain_start`: Before a chain executes

### Error Handling

```python
from clearstone.integrations.langchain import PolicyViolationError, PolicyPauseError

try:
    with context_scope(context):
        result = agent.invoke(input, callbacks=[handler])

except PolicyViolationError as e:
    print(f"❌ Blocked: {e.decision.reason}")

except PolicyPauseError as e:
    print(f"⏸️ Paused: {e.decision.reason}")
```

## Developer Tools

### PolicyValidator

Validate policies before deployment to catch bugs, slowness, and non-determinism.

```python
from clearstone import PolicyValidator

validator = PolicyValidator()

failures = validator.run_all_checks(my_policy)

if failures:
    print("❌ Policy failed validation:")
    for failure in failures:
        print(f"  - {failure}")
else:
    print("✅ Policy is production-ready")
```

**Validation Checks:**
- **Performance**: Ensures policy executes in < 100ms
- **Determinism**: Ensures policy returns same result for same input
- **Error Handling**: Ensures policy doesn't crash on edge cases

### PolicyDebugger

Understand exactly why a policy made a specific decision.

```python
from clearstone import PolicyDebugger

debugger = PolicyDebugger()

decision, trace = debugger.trace_evaluation(my_complex_policy, context)

print(debugger.format_trace(my_complex_policy, decision, trace))
```

**Output:**
```
Policy: my_complex_policy
Decision: BLOCK (Line 15)
Reason: Cost limit exceeded

Execution Trace:
  Line 10: cost = context.metadata.get("cost")  # cost = 25.5
  Line 12: limit = context.metadata.get("limit")  # limit = 10.0
  Line 15: if cost > limit:  # True
  Line 16:     return BLOCK("Cost limit exceeded")  # RETURNED
```

### PolicyMetrics

Track policy performance and identify bottlenecks.

```python
from clearstone import PolicyMetrics

metrics = PolicyMetrics()
engine = PolicyEngine(metrics=metrics)

summary = metrics.summary()

for policy_name, stats in summary.items():
    print(f"{policy_name}:")
    print(f"  Avg Latency: {stats['avg_latency_ms']:.4f}ms")
    print(f"  Calls: {stats['call_count']}")
    print(f"  Block Rate: {stats['block_rate']:.2%}")

slowest = metrics.get_slowest_policies(top_n=5)
top_blockers = metrics.get_top_blocking_policies(top_n=5)
```

### AuditTrail

Generate exportable audit logs for compliance.

```python
from clearstone import AuditTrail

audit = AuditTrail()
engine = PolicyEngine(audit_trail=audit)

summary = audit.summary()
print(f"Total Decisions: {summary['total_decisions']}")
print(f"Blocks: {summary['blocks']}")
print(f"Block Rate: {summary['block_rate']:.2%}")

audit.to_json("audit_log.json")
audit.to_csv("audit_log.csv")
```

## CLI Tools

### Scaffolding New Policies

```bash
clearstone new-policy enforce_data_locality --priority=80 --dir=my_app/policies
```

**Generated File:**
```python
from clearstone import Policy, ALLOW, BLOCK, Decision
from clearstone.core.context import PolicyContext

@Policy(name="enforce_data_locality", priority=80)
def enforce_data_locality_policy(context: PolicyContext) -> Decision:
    """
    [TODO: Describe what this policy does.]
    """
    return ALLOW
```

## Best Practices

### 1. Keep Policies Simple

Each policy should check **one thing**. Use composition for complex logic.

**Bad:**
```python
@Policy(name="mega_policy", priority=100)
def mega_policy(context):
    if not check_auth(context):
        return BLOCK("Auth failed")
    if not check_cost(context):
        return BLOCK("Cost exceeded")
    if not check_rate_limit(context):
        return BLOCK("Rate limit exceeded")
    return ALLOW
```

**Good:**
```python
@Policy(name="auth_check", priority=100)
def auth_policy(context):
    if not check_auth(context):
        return BLOCK("Auth failed")
    return ALLOW

@Policy(name="cost_check", priority=90)
def cost_policy(context):
    if not check_cost(context):
        return BLOCK("Cost exceeded")
    return ALLOW

combined = compose_and(auth_policy, cost_policy)
```

### 2. Use Priorities Strategically

Security policies should have highest priority, monitoring policies lowest:
- **Security**: 100-150
- **Access Control**: 80-100
- **Cost/Rate Limits**: 60-80
- **Monitoring/Alerts**: 10-50

### 3. Provide Clear Reasons

Always include a descriptive reason when blocking:

```python
return BLOCK(f"User '{user_id}' does not have role '{required_role}'")
```

### 4. Test Before Deploying

Always run `PolicyValidator` before deploying a new policy:

```bash
python -m clearstone.utils.validator my_policy
```

### 5. Monitor in Production

Use `PolicyMetrics` and `AuditTrail` to monitor policy behavior in production.

## Next Steps

- **[Pre-Built Policies](../policies.md)**: Explore 17+ production-ready policies
- **[Observability Guide](observability.md)**: Add distributed tracing
- **[Testing Guide](testing.md)**: Validate policies with backtesting
- **[API Reference](../api/governance.md)**: Complete API documentation

