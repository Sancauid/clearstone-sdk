import pytest

from clearstone.observability import (
    SpanKind,
    TracerProvider,
)
from clearstone.testing import (
    PolicyTestHarness,
    assert_no_errors_in_trace,
    assert_span_order,
    assert_tool_was_called,
)


def simple_research_agent(query: str, tracer):
    """A mock agent that 'researches' a topic."""
    with tracer.span("research_workflow"):
        with tracer.span("plan"):
            pass

        with tracer.span(
            "search_tool", kind=SpanKind.CLIENT, attributes={"tool.name": "web_search"}
        ):
            pass

        with tracer.span("synthesize"):
            pass


def faulty_research_agent(query: str, tracer):
    """A mock agent that has an error during execution."""
    with tracer.span("faulty_workflow"):
        with tracer.span("plan"):
            pass
        with tracer.span(
            "search_tool", kind=SpanKind.CLIENT, attributes={"tool.name": "web_search"}
        ):
            raise ValueError("API connection failed")


def test_agent_behavior_with_harness(tmp_path):
    """
    This test demonstrates the full loop:
    1. Run an agent to generate a trace.
    2. Use the PolicyTestHarness to run behavioral assertions against that trace.
    """
    db_path = tmp_path / "testing_pillar_traces.db"

    provider = TracerProvider(db_path=str(db_path))
    tracer = provider.get_tracer("research_agent")

    simple_research_agent("What is Clearstone?", tracer)
    provider.shutdown()

    harness = PolicyTestHarness(trace_db_path=str(db_path))
    traces = harness.load_traces()

    assert len(traces) == 1, "Should have captured one trace"

    tool_policy = assert_tool_was_called("web_search", times=1)
    result1 = harness.simulate_policy(tool_policy, traces)
    assert (
        result1.summary()["runs_blocked"] == 0
    ), f"Tool assertion failed: {result1.blocked_trace_ids}"

    order_policy = assert_span_order(["plan", "search_tool", "synthesize"])
    result2 = harness.simulate_policy(order_policy, traces)
    assert (
        result2.summary()["runs_blocked"] == 0
    ), f"Order assertion failed: {result2.blocked_trace_ids}"

    error_policy = assert_no_errors_in_trace()
    result3 = harness.simulate_policy(error_policy, traces)
    assert (
        result3.summary()["runs_blocked"] == 0
    ), f"Error assertion failed: {result3.blocked_trace_ids}"


def test_faulty_agent_fails_behavioral_test(tmp_path):
    """
    This test demonstrates that our harness can catch behavioral failures,
    like errors in the trace.
    """
    db_path = tmp_path / "faulty_traces.db"

    provider = TracerProvider(db_path=str(db_path))
    tracer = provider.get_tracer("faulty_agent")

    with pytest.raises(ValueError):
        faulty_research_agent("This will fail", tracer)
    provider.shutdown()

    harness = PolicyTestHarness(trace_db_path=str(db_path))
    traces = harness.load_traces()

    result = harness.simulate_policy(assert_no_errors_in_trace(), traces)

    summary = result.summary()
    assert (
        summary["runs_blocked"] == 1
    ), "The 'assert_no_errors' policy should have blocked this faulty trace."
    assert summary["block_rate_percent"] == "100.00%", "Should have a 100% block rate"


def test_multiple_tool_calls(tmp_path):
    """Test that we can assert on the number of times a tool is called."""
    db_path = tmp_path / "multi_tool_traces.db"

    provider = TracerProvider(db_path=str(db_path))
    tracer = provider.get_tracer("multi_tool_agent")

    with tracer.span("workflow"):
        with tracer.span(
            "search1", kind=SpanKind.CLIENT, attributes={"tool.name": "web_search"}
        ):
            pass
        with tracer.span(
            "search2", kind=SpanKind.CLIENT, attributes={"tool.name": "web_search"}
        ):
            pass
        with tracer.span(
            "calculator", kind=SpanKind.CLIENT, attributes={"tool.name": "calculator"}
        ):
            pass

    provider.shutdown()

    harness = PolicyTestHarness(trace_db_path=str(db_path))
    traces = harness.load_traces()

    policy_exact = assert_tool_was_called("web_search", times=2)
    result = harness.simulate_policy(policy_exact, traces)
    assert (
        result.summary()["runs_blocked"] == 0
    ), "Should have found exactly 2 web_search calls"

    policy_wrong_count = assert_tool_was_called("web_search", times=3)
    result = harness.simulate_policy(policy_wrong_count, traces)
    assert (
        result.summary()["runs_blocked"] == 1
    ), "Should have blocked due to wrong count"


def test_agent_workflow_with_backtesting(tmp_path):
    """
    Comprehensive test showing how to backtest agent behavior changes.
    Simulates testing a new version of an agent against historical traces.
    """
    db_path = tmp_path / "backtest_traces.db"

    provider = TracerProvider(db_path=str(db_path))

    for i in range(5):
        tracer = provider.get_tracer(f"agent_v1_run_{i}")
        with tracer.span("workflow"):
            with tracer.span("analyze"):
                pass
            with tracer.span(
                "search", kind=SpanKind.CLIENT, attributes={"tool.name": "search"}
            ):
                pass
            with tracer.span("respond"):
                pass

    provider.shutdown()

    harness = PolicyTestHarness(trace_db_path=str(db_path))
    traces = harness.load_traces()

    assert len(traces) == 5, "Should have 5 historical traces"

    required_order = assert_span_order(["analyze", "search", "respond"])
    result = harness.simulate_policy(required_order, traces)

    summary = result.summary()
    assert summary["traces_analyzed"] == 5
    assert (
        summary["runs_blocked"] == 0
    ), "All historical runs should pass the behavior test"
