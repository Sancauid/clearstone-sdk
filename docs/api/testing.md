# Testing API Reference

This page documents the complete API for Clearstone's AI-native testing framework.

## PolicyTestHarness

The core testing tool for backtesting and behavioral assertions.

```python
from clearstone.testing import PolicyTestHarness

harness = PolicyTestHarness("agent_traces.db")
traces = harness.load_traces(limit=100)
```

::: clearstone.testing.harness.PolicyTestHarness

## Behavioral Assertions

Pre-built assertion policies for validating agent behavior.

### assert_tool_was_called

Verify a tool was called the expected number of times.

```python
from clearstone.testing import assert_tool_was_called

policy = assert_tool_was_called("web_search", times=3)
result = harness.simulate_policy(policy, traces)
```

::: clearstone.testing.assertions.assert_tool_was_called

### assert_no_errors_in_trace

Validate that traces executed without errors.

```python
from clearstone.testing import assert_no_errors_in_trace

policy = assert_no_errors_in_trace()
result = harness.simulate_policy(policy, traces)
```

::: clearstone.testing.assertions.assert_no_errors_in_trace

### assert_llm_cost_is_less_than

Ensure agent stays within budget.

```python
from clearstone.testing import assert_llm_cost_is_less_than

policy = assert_llm_cost_is_less_than(0.50)
result = harness.simulate_policy(policy, traces)
```

::: clearstone.testing.assertions.assert_llm_cost_is_less_than

### assert_span_order

Validate workflow sequence is correct.

```python
from clearstone.testing import assert_span_order

policy = assert_span_order(["plan", "search", "synthesize"])
result = harness.simulate_policy(policy, traces)
```

::: clearstone.testing.assertions.assert_span_order

## Test Result Models

### TestResult

Contains the results of policy simulation.

```python
result = harness.simulate_policy(policy, traces)

summary = result.summary()
print(f"Blocked: {summary['runs_blocked']}")
print(f"Block Rate: {summary['block_rate_percent']}")
```

::: clearstone.testing.harness.PolicyTestResult

