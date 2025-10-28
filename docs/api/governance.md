# Governance API Reference

This page documents the complete API for Clearstone's governance system.

## Core Module

::: clearstone.core.policy

::: clearstone.core.actions

::: clearstone.core.context

::: clearstone.core.exceptions

## Policy Engine

The PolicyEngine discovers, evaluates, and enforces policies at runtime.

```python
from clearstone import PolicyEngine

engine = PolicyEngine()
```

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

