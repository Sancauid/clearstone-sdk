# API Reference

Complete API documentation for Clearstone SDK.

## Core Modules

### Policy Decorator

```python
from clearstone import Policy

@Policy(name: str, priority: int = 0)
def my_policy(context: PolicyContext) -> Decision:
    pass
```

**Parameters:**
- `name` (str): Unique identifier for the policy
- `priority` (int): Evaluation priority (higher runs first, default: 0)

### Decision Types

#### ALLOW
```python
from clearstone import ALLOW

# Simple allow decision
return ALLOW
```

#### BLOCK
```python
from clearstone import BLOCK

# Block with reason
return BLOCK("Insufficient permissions")

# Block with metadata
return BLOCK("Token limit exceeded", tokens_used=1500, limit=1000)
```

#### PAUSE
```python
from clearstone import PAUSE

# Pause for human intervention
return PAUSE("Manual approval required for deployment")

# Pause with custom intervention ID
return PAUSE("High-value transaction", intervention_id="txn-123")
```

#### ALERT
```python
from clearstone import ALERT

# Allow but trigger alert
return ALERT
```

#### REDACT
```python
from clearstone import REDACT

# Redact specific fields
return REDACT("PII detected", fields=["ssn", "email", "credit_card"])
```

### PolicyContext

```python
@dataclass
class PolicyContext:
    user_id: str
    agent_id: str
    metadata: Dict[str, Any]
    timestamp: datetime
```

**Usage:**
```python
def my_policy(context):
    user_role = context.metadata.get("role")
    tool_name = context.metadata.get("tool_name")
    # ...
```

### PolicyEngine

```python
from clearstone import PolicyEngine

engine = PolicyEngine(
    audit_trail: AuditTrail = None,
    metrics: PolicyMetrics = None
)
```

**Methods:**
- `evaluate() -> Decision`: Evaluate all registered policies
- `get_registered_policies() -> List[PolicyInfo]`: Get list of registered policies

### Context Management

```python
from clearstone import create_context, context_scope

# Create a context
context = create_context(
    user_id: str,
    agent_id: str,
    **metadata
)

# Use within a scope
with context_scope(context):
    # Policies can access this context
    decision = engine.evaluate()
```

## LangChain Integration

### PolicyCallbackHandler

```python
from clearstone.integrations.langchain import PolicyCallbackHandler

handler = PolicyCallbackHandler(engine: PolicyEngine)

# Use with LangChain agent
agent.invoke(input, callbacks=[handler])
```

### Exceptions

```python
from clearstone.integrations.langchain import (
    PolicyViolationError,
    PolicyPauseError
)

try:
    with context_scope(context):
        handler.on_tool_start(...)
except PolicyViolationError as e:
    print(f"Blocked: {e.decision.reason}")
except PolicyPauseError as e:
    print(f"Paused: {e.decision.reason}")
```

## Developer Tools

### PolicyValidator

```python
from clearstone import PolicyValidator

validator = PolicyValidator()

# Run all validation checks
failures = validator.run_all_checks(policy_func)

# Individual checks
validator.check_determinism(policy_func, context)
validator.check_performance(policy_func, context, max_ms=100)
validator.check_signature(policy_func)
```

### PolicyDebugger

```python
from clearstone import PolicyDebugger

debugger = PolicyDebugger()

# Trace policy execution
decision, trace = debugger.trace_evaluation(policy_func, context)

# Format trace for display
report = debugger.format_trace(policy_func, decision, trace)
print(report)
```

### PolicyMetrics

```python
from clearstone import PolicyMetrics

metrics = PolicyMetrics()
engine = PolicyEngine(metrics=metrics)

# Get summary
summary = metrics.summary()

# Get slowest policies
slowest = metrics.get_slowest_policies(top_n=5)

# Get policies that block most
blockers = metrics.get_top_blocking_policies(top_n=5)

# Export metrics
metrics.to_json("metrics.json")
```

### AuditTrail

```python
from clearstone import AuditTrail

audit = AuditTrail()
engine = PolicyEngine(audit_trail=audit)

# Get summary
stats = audit.summary()

# Get entries
entries = audit.get_entries(limit=100)

# Export
audit.to_json("audit.json")
audit.to_csv("audit.csv")
```

### InterventionClient

```python
from clearstone import InterventionClient

client = InterventionClient()

# Log intervention request
client.request_intervention(pause_decision)

# Wait for approval (blocking)
approved = client.wait_for_approval(
    intervention_id: str,
    prompt: str = None
)
```

## Composition Helpers

```python
from clearstone import compose_and, compose_or

# AND composition (all must pass)
strict_policy = compose_and(policy_a, policy_b, policy_c)

# OR composition (at least one must pass)
lenient_policy = compose_or(policy_a, policy_b)
```

## Pre-Built Policies

```python
from clearstone.policies.common import (
    # Token & Cost
    token_limit_policy,
    session_cost_limit_policy,
    daily_cost_limit_policy,
    
    # RBAC
    rbac_tool_access_policy,
    admin_only_action_policy,
    
    # PII Protection
    redact_pii_policy,
    block_pii_tools_policy,
    
    # Security
    block_dangerous_tools_policy,
    pause_before_write_policy,
    alert_on_privileged_access_policy,
    alert_on_failed_auth_policy,
    
    # Time-Based
    business_hours_only_policy,
    
    # Additional
    rate_limit_policy,
    block_external_apis_policy,
    require_approval_for_high_cost_policy,
)

# Policy factory functions
from clearstone.policies.common import (
    create_safe_mode_policies,
    create_audit_mode_policies,
    create_cost_control_policies,
    create_security_policies,
    create_data_protection_policies,
)
```

## Command-Line Interface

```bash
# Create new policy
clearstone new-policy <name> [options]

# Options:
#   --priority=<int>    Policy priority (default: 0)
#   --dir=<path>        Output directory (default: policies)
#   --force             Overwrite existing file
```

## Next Steps

- See [Writing Policies](../guide/writing-policies.md) for usage examples
- Check out the [Developer Toolkit](../guide/developer-toolkit.md)
- Explore the [Examples](https://github.com/your-repo/clearstone-sdk/tree/main/examples)

