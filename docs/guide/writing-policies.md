# Writing Policies

This guide covers how to write effective policies for your AI agent systems.

## Policy Basics

A policy in Clearstone is a simple Python function decorated with `@Policy`. It receives a context object and returns a decision.

```python
from clearstone import Policy, ALLOW, BLOCK

@Policy(name="my_policy", priority=100)
def my_policy(context):
    """
    A simple policy that checks something.
    """
    # Read from context
    user_role = context.metadata.get("role")
    
    # Make a decision
    if user_role == "guest":
        return BLOCK("Guests are not allowed.")
    
    return ALLOW
```

## Decision Types

Clearstone provides several decision types:

- **ALLOW**: Allow the action to proceed
- **BLOCK(reason)**: Block the action with a reason
- **PAUSE(reason)**: Pause for human approval
- **ALERT**: Allow but trigger an alert
- **REDACT(reason, fields)**: Redact specific fields
- **SKIP**: Skip this policy (neutral)

## Priority System

Policies are evaluated in priority order (highest to lowest). A policy with priority 100 runs before a policy with priority 50.

```python
@Policy(name="high_priority_check", priority=100)
def high_priority_check(context):
    # Runs first
    pass

@Policy(name="low_priority_check", priority=10)
def low_priority_check(context):
    # Runs later
    pass
```

## Composing Policies

You can combine policies using composition helpers:

```python
from clearstone import compose_and, compose_or
from clearstone.policies.common import token_limit_policy, cost_limit_policy

# Both must pass
safe_and_cheap = compose_and(token_limit_policy, cost_limit_policy)

# At least one must pass
lenient_check = compose_or(policy_a, policy_b)
```

## Pre-Built Policy Library

Clearstone includes 15+ production-ready policies:

- **Token & Cost Control**: `token_limit_policy`, `session_cost_limit_policy`, `daily_cost_limit_policy`
- **RBAC**: `rbac_tool_access_policy`, `admin_only_action_policy`
- **PII Protection**: `redact_pii_policy`, `block_pii_tools_policy`
- **Security**: `block_dangerous_tools_policy`, `alert_on_privileged_access_policy`
- **Time-Based**: `business_hours_only_policy`

Import them from `clearstone.policies.common`:

```python
from clearstone.policies.common import (
    token_limit_policy,
    rbac_tool_access_policy,
    block_dangerous_tools_policy
)
```

## Best Practices

### 1. Keep Policies Simple

Each policy should check one thing. Use composition to combine multiple checks.

```python
# Good: Single responsibility
@Policy(name="check_role", priority=100)
def check_role(context):
    role = context.metadata.get("role")
    if role not in ["admin", "user"]:
        return BLOCK(f"Invalid role: {role}")
    return ALLOW

# Bad: Too many responsibilities
@Policy(name="check_everything", priority=100)
def check_everything(context):
    # Checks role, cost, time, PII, etc...
    pass
```

### 2. Provide Clear Reasons

When blocking or pausing, always provide a clear, actionable reason:

```python
# Good: Clear reason
return BLOCK("Daily budget of $100 exceeded. Current spend: $125")

# Bad: Vague reason
return BLOCK("Budget exceeded")
```

### 3. Test Your Policies

Use the `PolicyValidator` to catch bugs before deployment:

```python
from clearstone import PolicyValidator

validator = PolicyValidator()
failures = validator.run_all_checks(my_policy)

if failures:
    print("Policy failed validation:", failures)
```

### 4. Use Appropriate Priorities

- **100+**: Critical security checks (auth, dangerous tools)
- **80-99**: Important business rules (cost limits, RBAC)
- **50-79**: Nice-to-have checks (alerts, logging)
- **0-49**: Low-priority policies

## Debugging Policies

Use the `PolicyDebugger` to understand policy decisions:

```python
from clearstone import PolicyDebugger

debugger = PolicyDebugger()
decision, trace = debugger.trace_evaluation(my_policy, context)

# Print detailed execution trace
print(debugger.format_trace(my_policy, decision, trace))
```

## Next Steps

- Explore the [Developer Toolkit](developer-toolkit.md)
- See the [API Reference](../api/index.md)
- Check out the [Examples](https://github.com/your-repo/clearstone-sdk/tree/main/examples)

