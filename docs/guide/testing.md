# Testing

The Testing pillar provides AI-native testing capabilities for validating agent behavior. Unlike traditional unit tests that check outputs, Clearstone tests validate **how** agents behave at runtime.

## The PolicyTestHarness

The `PolicyTestHarness` is the core testing tool. It loads historical traces and simulates policy enforcement to predict impact before deployment.

### Basic Setup

```python
from clearstone.testing import PolicyTestHarness

harness = PolicyTestHarness("agent_traces.db")

traces = harness.load_traces(limit=100)
```

## Behavioral Assertions

Behavioral assertions are policies designed for testing. They validate specific agent behaviors.

### assert_tool_was_called

Verify a tool was called the expected number of times.

```python
from clearstone.testing import assert_tool_was_called

policy = assert_tool_was_called("web_search")

result = harness.simulate_policy(policy, traces)

summary = result.summary()
print(f"Passed: {summary['traces_analyzed'] - summary['runs_blocked']}")
print(f"Failed: {summary['runs_blocked']}")
```

**With Exact Count:**
```python
policy = assert_tool_was_called("web_search", times=3)
```

### assert_no_errors_in_trace

Validate that traces executed without errors.

```python
from clearstone.testing import assert_no_errors_in_trace

policy = assert_no_errors_in_trace()

result = harness.simulate_policy(policy, traces)

if result.summary()["runs_blocked"] > 0:
    print("❌ Found traces with errors:")
    print(f"   Blocked traces: {result.blocked_trace_ids}")
```

### assert_llm_cost_is_less_than

Ensure agent stays within budget.

```python
from clearstone.testing import assert_llm_cost_is_less_than

policy = assert_llm_cost_is_less_than(0.50)

result = harness.simulate_policy(policy, traces)

summary = result.summary()
print(f"Over Budget: {summary['runs_blocked']} / {summary['traces_analyzed']}")
```

### assert_span_order

Validate workflow sequence is correct.

```python
from clearstone.testing import assert_span_order

policy = assert_span_order(["plan", "search", "synthesize"])

result = harness.simulate_policy(policy, traces)

if result.summary()["runs_blocked"] > 0:
    print("❌ Workflow order violated")
```

## Historical Backtesting

Test new policies against production data before deployment.

### Basic Backtesting

```python
from clearstone import Policy, BLOCK, ALLOW

@Policy(name="new_cost_policy", priority=100)
def new_cost_policy(context):
    cost = sum(
        span.attributes.get("cost", 0)
        for span in context.metadata.get("spans", [])
    )
    
    if cost > 2.0:
        return BLOCK(f"Cost ${cost:.2f} exceeds new limit")
    
    return ALLOW

harness = PolicyTestHarness("production_traces.db")
traces = harness.load_traces(limit=1000)

result = harness.simulate_policy(new_cost_policy, traces)

summary = result.summary()
print(f"Impact Analysis:")
print(f"  Traces Analyzed: {summary['traces_analyzed']}")
print(f"  Would Block: {summary['runs_blocked']}")
print(f"  Block Rate: {summary['block_rate_percent']}")
print(f"  Blocked Trace IDs: {result.blocked_trace_ids[:10]}")
```

### Comparing Policies

```python
from clearstone.policies.common import token_limit_policy, cost_limit_policy

harness = PolicyTestHarness("traces.db")
traces = harness.load_traces()

token_result = harness.simulate_policy(token_limit_policy, traces)
cost_result = harness.simulate_policy(cost_limit_policy, traces)

print("Token Policy:")
print(f"  Block Rate: {token_result.summary()['block_rate_percent']}")

print("Cost Policy:")
print(f"  Block Rate: {cost_result.summary()['block_rate_percent']}")
```

### Analyzing Impact

```python
result = harness.simulate_policy(new_policy, traces)

print(f"Total Traces: {len(traces)}")
print(f"Blocked: {len(result.blocked_trace_ids)}")
print(f"Allowed: {len(result.allowed_trace_ids)}")

print("\nBlocked Trace Details:")
for trace_id in result.blocked_trace_ids[:5]:
    trace = next(t for t in traces if t.trace_id == trace_id)
    print(f"  {trace_id}: {trace.root_span.name}")
    print(f"    Duration: {trace.root_span.duration_ms:.2f}ms")
    print(f"    Status: {trace.root_span.status}")
```

## pytest Integration

Integrate behavioral tests into your test suite.

### Basic Test

```python
import pytest
from clearstone.observability import TracerProvider
from clearstone.testing import PolicyTestHarness, assert_tool_was_called

def test_research_agent_uses_search(tmp_path):
    db_path = tmp_path / "test_traces.db"
    
    provider = TracerProvider(db_path=str(db_path))
    tracer = provider.get_tracer("test_agent")
    
    with tracer.span("research_workflow"):
        with tracer.span("search", attributes={"tool.name": "web_search"}):
            pass
    
    provider.shutdown()
    
    harness = PolicyTestHarness(str(db_path))
    traces = harness.load_traces()
    
    policy = assert_tool_was_called("web_search", times=1)
    result = harness.simulate_policy(policy, traces)
    
    assert result.summary()["runs_blocked"] == 0, \
        "Agent should use web_search exactly once"
```

### Testing Agent Behavior

```python
def test_agent_stays_within_budget(tmp_path):
    db_path = tmp_path / "test_traces.db"
    
    provider = TracerProvider(db_path=str(db_path))
    tracer = provider.get_tracer("test_agent")
    
    with tracer.span("task", attributes={"cost": 0.45}):
        pass
    
    provider.shutdown()
    
    harness = PolicyTestHarness(str(db_path))
    traces = harness.load_traces()
    
    policy = assert_llm_cost_is_less_than(0.50)
    result = harness.simulate_policy(policy, traces)
    
    assert result.summary()["runs_blocked"] == 0
```

### Testing Error Handling

```python
def test_agent_handles_errors_gracefully(tmp_path):
    db_path = tmp_path / "test_traces.db"
    
    provider = TracerProvider(db_path=str(db_path))
    tracer = provider.get_tracer("test_agent")
    
    with tracer.span("workflow") as span:
        with tracer.span("risky_operation") as child:
            child.set_status("ERROR")
    
    provider.shutdown()
    
    harness = PolicyTestHarness(str(db_path))
    traces = harness.load_traces()
    
    policy = assert_no_errors_in_trace()
    result = harness.simulate_policy(policy, traces)
    
    assert result.summary()["runs_blocked"] > 0, \
        "Should detect error in trace"
```

### Parametrized Tests

```python
@pytest.mark.parametrize("tool_name,expected_count", [
    ("web_search", 2),
    ("calculator", 1),
    ("summarizer", 1),
])
def test_tool_usage_counts(tmp_path, tool_name, expected_count):
    db_path = tmp_path / "test_traces.db"
    
    provider = TracerProvider(db_path=str(db_path))
    tracer = provider.get_tracer("test_agent")
    
    with tracer.span("workflow"):
        for _ in range(expected_count):
            with tracer.span("tool", attributes={"tool.name": tool_name}):
                pass
    
    provider.shutdown()
    
    harness = PolicyTestHarness(str(db_path))
    traces = harness.load_traces()
    
    policy = assert_tool_was_called(tool_name, times=expected_count)
    result = harness.simulate_policy(policy, traces)
    
    assert result.summary()["runs_blocked"] == 0
```

## Custom Behavioral Assertions

Create your own assertions for specific needs.

### Isolated Policy Testing

Use explicit configuration to test policies in isolation without interference from other policies:

```python
import pytest
from clearstone import PolicyEngine, Policy, BLOCK, ALLOW, create_context
from clearstone.core.actions import ActionType

@Policy(name="value_check_policy", priority=100)
def value_check_policy(context):
    """Ensure value doesn't exceed threshold."""
    value = context.metadata.get("value", 0)
    threshold = context.metadata.get("threshold", 10)
    
    if value > threshold:
        return BLOCK(f"Value {value} exceeds threshold {threshold}")
    
    return ALLOW

def test_value_check_policy_blocks_high_values():
    """Test that the policy blocks values above threshold."""
    # Test this policy in isolation, ignoring all other registered policies
    engine = PolicyEngine(policies=[value_check_policy])
    
    context = create_context(
        "user", "agent",
        metadata={"value": 15, "threshold": 10}
    )
    
    decision = engine.evaluate(context)
    
    assert decision.action == ActionType.BLOCK
    assert "exceeds threshold" in decision.reason

def test_value_check_policy_allows_low_values():
    """Test that the policy allows values below threshold."""
    engine = PolicyEngine(policies=[value_check_policy])
    
    context = create_context(
        "user", "agent",
        metadata={"value": 5, "threshold": 10}
    )
    
    decision = engine.evaluate(context)
    
    assert decision.action == ActionType.ALLOW

def test_multiple_policies_together():
    """Test how multiple policies interact."""
    @Policy(name="auth_check", priority=100)
    def auth_check(context):
        if not context.metadata.get("authenticated"):
            return BLOCK("Not authenticated")
        return ALLOW
    
    # Test specific combination of policies
    engine = PolicyEngine(policies=[auth_check, value_check_policy])
    
    context = create_context(
        "user", "agent",
        metadata={"authenticated": False, "value": 5}
    )
    
    decision = engine.evaluate(context)
    
    # Auth should block first (higher priority when both are 100)
    assert decision.action == ActionType.BLOCK
    assert "Not authenticated" in decision.reason
```

**Benefits of Isolated Testing:**

- **No Side Effects:** Other policies don't interfere with your test
- **Deterministic:** Test outcome depends only on the policy being tested
- **Fast:** Only evaluates the policies you need
- **Clear Failures:** Easy to identify which policy caused a test failure
- **Flexible:** Mix and match policies to test specific combinations

### Basic Custom Assertion

```python
from clearstone import Policy, BLOCK, ALLOW

@Policy(name="assert_no_external_apis", priority=100)
def assert_no_external_apis(context):
    """Ensure agent doesn't call external APIs."""
    spans = context.metadata.get("spans", [])
    
    for span in spans:
        if span.attributes.get("external_api", False):
            return BLOCK(
                f"Unexpected external API call: {span.name}"
            )
    
    return ALLOW
```

### Advanced Custom Assertion

```python
@Policy(name="assert_optimal_workflow", priority=100)
def assert_optimal_workflow(context):
    """Ensure agent uses optimal workflow pattern."""
    spans = context.metadata.get("spans", [])
    
    span_names = [s.name for s in spans]
    
    if "plan" not in span_names:
        return BLOCK("Workflow missing 'plan' step")
    
    if "validate" not in span_names:
        return BLOCK("Workflow missing 'validate' step")
    
    plan_idx = span_names.index("plan")
    execute_idx = next(
        (i for i, name in enumerate(span_names) if "execute" in name),
        None
    )
    
    if execute_idx and execute_idx < plan_idx:
        return BLOCK("Workflow executed before planning")
    
    return ALLOW
```

## Regression Testing

Prevent behavioral regressions by testing against baseline traces.

### Creating a Baseline

```python
provider = TracerProvider(db_path="baseline_traces.db")
tracer = provider.get_tracer("production_agent")

with tracer.span("baseline_workflow"):
    run_agent()

provider.shutdown()
```

### Testing Against Baseline

```python
def test_no_regression():
    baseline_harness = PolicyTestHarness("baseline_traces.db")
    current_harness = PolicyTestHarness("current_traces.db")
    
    baseline_traces = baseline_harness.load_traces()
    current_traces = current_harness.load_traces()
    
    policy = assert_tool_was_called("expensive_api", times=0)
    
    baseline_result = baseline_harness.simulate_policy(policy, baseline_traces)
    current_result = current_harness.simulate_policy(policy, current_traces)
    
    assert baseline_result.summary()["runs_blocked"] == \
           current_result.summary()["runs_blocked"], \
           "Behavioral regression detected"
```

## Test Result Analysis

### Result Object

```python
result = harness.simulate_policy(policy, traces)

print(f"Policy Name: {result.policy_name}")
print(f"Traces Analyzed: {len(result.allowed_trace_ids) + len(result.blocked_trace_ids)}")
print(f"Allowed: {len(result.allowed_trace_ids)}")
print(f"Blocked: {len(result.blocked_trace_ids)}")
```

### Summary Statistics

```python
summary = result.summary()

print(f"Traces Analyzed: {summary['traces_analyzed']}")
print(f"Runs Blocked: {summary['runs_blocked']}")
print(f"Block Rate: {summary['block_rate_percent']}")
```

### Detailed Analysis

```python
for trace_id in result.blocked_trace_ids[:10]:
    trace = next(t for t in traces if t.trace_id == trace_id)
    
    print(f"Blocked Trace: {trace_id}")
    print(f"  Root: {trace.root_span.name}")
    print(f"  Duration: {trace.root_span.duration_ms:.2f}ms")
    
    for span in trace.spans:
        print(f"    - {span.name}")
        for key, value in span.attributes.items():
            print(f"        {key}: {value}")
```

## Best Practices

### 1. Test Early and Often

Run behavioral tests in CI/CD:

```yaml
# .github/workflows/test.yml
- name: Run Behavioral Tests
  run: pytest tests/behavioral/
```

### 2. Maintain Representative Test Data

Keep a dataset of representative traces:

```python
BASELINE_TRACES = "tests/fixtures/baseline_traces.db"

harness = PolicyTestHarness(BASELINE_TRACES)
```

### 3. Test Multiple Scenarios

```python
@pytest.mark.parametrize("scenario", [
    "happy_path",
    "error_recovery",
    "high_load",
    "edge_case"
])
def test_agent_behavior(scenario):
    harness = PolicyTestHarness(f"traces/{scenario}.db")
    pass
```

### 4. Document Test Intent

```python
def test_agent_respects_cost_limits():
    """
    Verify that the agent never exceeds a $1.00 cost per session.
    
    This is a critical business requirement to prevent unexpected bills.
    If this test fails, DO NOT deploy to production.
    """
    policy = assert_llm_cost_is_less_than(1.00)
    pass
```

### 5. Use Fixtures for Common Setup

```python
@pytest.fixture
def test_harness(tmp_path):
    db_path = tmp_path / "test_traces.db"
    return PolicyTestHarness(str(db_path))

def test_something(test_harness):
    traces = test_harness.load_traces()
    pass
```

## Next Steps

- **[Time-Travel Debugging](time-travel-debugging.md)**: Debug agents with checkpoints
- **[Pre-Built Policies](../policies.md)**: Explore behavioral assertions
- **[API Reference](../api/testing.md)**: Complete testing API documentation

