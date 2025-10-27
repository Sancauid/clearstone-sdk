# Developer Toolkit

Clearstone is more than just a policy engine; it's a complete toolkit for policy governance.

## 1. Composing Policies

Build complex logic from simple, reusable parts.

```python
from clearstone import compose_and
from clearstone.policies.common import token_limit_policy, cost_limit_policy

# This new policy only passes if BOTH underlying policies pass.
safe_and_cheap_policy = compose_and(token_limit_policy, cost_limit_policy)
```

## 2. Validating Policies Before Deployment

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

## 3. Debugging Policy Decisions

Understand *why* a policy made a specific decision with a line-by-line execution trace.

```python
from clearstone import PolicyDebugger

debugger = PolicyDebugger()
decision, trace = debugger.trace_evaluation(my_complex_policy, context)

# Print a human-readable report
print(debugger.format_trace(my_complex_policy, decision, trace))
```

## 4. Performance Monitoring

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

## 5. Human-in-the-Loop Interventions

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

## 6. Auditing and Exporting

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

## Command-Line Interface (CLI)

Accelerate development with the `clearstone` CLI. The `new-policy` command scaffolds a boilerplate file with best practices.

```bash
# See all available commands
clearstone --help

# Create a new policy file
clearstone new-policy enforce_data_locality --priority=80 --dir=my_app/compliance

# Output: Creates my_app/compliance/enforce_data_locality_policy.py
```

The generated file includes:

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

## Next Steps

- Check out [Writing Policies](writing-policies.md) for more details
- Explore the [API Reference](../api/index.md)
- See the [Examples](https://github.com/your-repo/clearstone-sdk/tree/main/examples)

