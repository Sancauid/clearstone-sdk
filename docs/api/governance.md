# Governance API Reference

This page documents the complete API for Clearstone's governance system.

## Core Module

::: clearstone.core.policy

::: clearstone.core.actions

::: clearstone.core.context

::: clearstone.core.exceptions

## Policy Engine

The PolicyEngine discovers, evaluates, and enforces policies at runtime.

### Initialization

```python
from clearstone import PolicyEngine

# Auto-discovery mode (default)
engine = PolicyEngine()

# Explicit configuration mode
engine = PolicyEngine(policies=[policy1, policy2])

# With audit trail and metrics
from clearstone import AuditTrail, PolicyMetrics

audit = AuditTrail()
metrics = PolicyMetrics()
engine = PolicyEngine(
    policies=[policy1, policy2],  # Optional
    audit_trail=audit,
    metrics=metrics
)
```

**Parameters:**

- `policies` (Optional[List[Callable]]): List of policy functions to use. If provided, only these policies will be evaluated (no auto-discovery). If None (default), all imported `@Policy`-decorated functions are discovered automatically.
- `audit_trail` (Optional[AuditTrail]): Custom audit trail instance for logging decisions. If None, creates a new instance.
- `metrics` (Optional[PolicyMetrics]): Custom metrics instance for tracking performance. If None, creates a new instance.

**Raises:**

- `ValueError`: If no valid policies are found (either through auto-discovery or explicit list)

## Pre-Built Policies

::: clearstone.policies.common

## Utility Functions

### compose_and

Compose multiple policies with AND logic.

```python
from clearstone import compose_and
from clearstone.policies.common import token_limit_policy, cost_limit_policy

combined = compose_and(token_limit_policy, cost_limit_policy)
```

::: clearstone.utils.composition.compose_and

### compose_or

Compose multiple policies with OR logic.

```python
from clearstone import compose_or

combined = compose_or(admin_check_policy, superuser_check_policy)
```

::: clearstone.utils.composition.compose_or

## Developer Tools

### PolicyValidator

Validate policies before deployment.

```python
from clearstone import PolicyValidator

validator = PolicyValidator()
failures = validator.run_all_checks(my_policy)
```

::: clearstone.utils.validator.PolicyValidator

### PolicyDebugger

Debug policy decision-making.

```python
from clearstone import PolicyDebugger

debugger = PolicyDebugger()
decision, trace = debugger.trace_evaluation(my_policy, context)
```

::: clearstone.utils.debugging.PolicyDebugger

### PolicyMetrics

Track policy performance metrics.

```python
from clearstone import PolicyMetrics

metrics = PolicyMetrics()
engine = PolicyEngine(metrics=metrics)
```

::: clearstone.utils.metrics.PolicyMetrics

### AuditTrail

Generate exportable audit logs.

```python
from clearstone import AuditTrail

audit = AuditTrail()
engine = PolicyEngine(audit_trail=audit)
```

::: clearstone.utils.audit.AuditTrail

## LangChain Integration

::: clearstone.integrations.langchain.callbacks

::: clearstone.integrations.langchain.decorators

::: clearstone.integrations.langchain.tools

