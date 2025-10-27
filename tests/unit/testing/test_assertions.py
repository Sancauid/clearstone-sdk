from clearstone.core.actions import ActionType
from clearstone.observability.models import Span, SpanKind, SpanStatus, Trace
from clearstone.testing.assertions import (
    assert_llm_cost_is_less_than,
    assert_no_errors_in_trace,
    assert_span_order,
    assert_tool_was_called,
)


def mock_span(
    name,
    kind=SpanKind.INTERNAL,
    status=SpanStatus.OK,
    cost=0.0,
    tool_name=None,
    error_message=None,
):
    attributes = {}
    if cost > 0:
        attributes["llm.cost"] = cost
    if tool_name:
        attributes["tool.name"] = tool_name

    return Span(
        trace_id="t1",
        name=name,
        kind=kind,
        status=status,
        attributes=attributes,
        start_time_ns=0,
        instrumentation_name="test",
        instrumentation_version="1",
        error_message=error_message,
    )


def test_assert_tool_was_called_passes():
    """Test that the assertion passes when the tool is present."""
    trace = Trace(
        trace_id="t1",
        spans=[mock_span("s1", tool_name="search")],
        root_span_id="",
        agent_id="",
        agent_version="",
        environment="",
        start_time_ns=0,
    )
    policy = assert_tool_was_called("search")
    assert policy(trace).action == ActionType.ALLOW


def test_assert_tool_was_called_fails():
    """Test that the assertion fails when the tool is absent."""
    trace = Trace(
        trace_id="t1",
        spans=[mock_span("s1")],
        root_span_id="",
        agent_id="",
        agent_version="",
        environment="",
        start_time_ns=0,
    )
    policy = assert_tool_was_called("search")
    assert policy(trace).action == ActionType.BLOCK


def test_assert_tool_was_called_with_times():
    """Test the 'times' parameter for tool call assertions."""
    trace = Trace(
        trace_id="t1",
        spans=[
            mock_span("s1", tool_name="search"),
            mock_span("s2", tool_name="search"),
        ],
        root_span_id="",
        agent_id="",
        agent_version="",
        environment="",
        start_time_ns=0,
    )

    policy_pass = assert_tool_was_called("search", times=2)
    assert policy_pass(trace).action == ActionType.ALLOW

    policy_fail = assert_tool_was_called("search", times=1)
    assert policy_fail(trace).action == ActionType.BLOCK


def test_assert_llm_cost_is_less_than():
    """Test the cost assertion."""
    trace = Trace(
        trace_id="t1",
        spans=[mock_span("s1", cost=0.02), mock_span("s2", cost=0.02)],
        root_span_id="",
        agent_id="",
        agent_version="",
        environment="",
        start_time_ns=0,
    )

    policy_pass = assert_llm_cost_is_less_than(0.05)
    assert policy_pass(trace).action == ActionType.ALLOW

    policy_fail = assert_llm_cost_is_less_than(0.04)
    assert policy_fail(trace).action == ActionType.BLOCK


def test_assert_no_errors_in_trace():
    """Test the error assertion."""
    trace_ok = Trace(
        trace_id="t1",
        spans=[mock_span("s1", status=SpanStatus.OK)],
        root_span_id="",
        agent_id="",
        agent_version="",
        environment="",
        start_time_ns=0,
    )
    policy_pass = assert_no_errors_in_trace()
    assert policy_pass(trace_ok).action == ActionType.ALLOW

    trace_err = Trace(
        trace_id="t2",
        spans=[mock_span("s1", status=SpanStatus.ERROR, error_message="API failed")],
        root_span_id="",
        agent_id="",
        agent_version="",
        environment="",
        start_time_ns=0,
    )
    policy_fail = assert_no_errors_in_trace()
    assert policy_fail(trace_err).action == ActionType.BLOCK


def test_assert_span_order():
    """Test the span order assertion."""
    trace = Trace(
        trace_id="t1",
        spans=[mock_span("think"), mock_span("plan"), mock_span("act")],
        root_span_id="",
        agent_id="",
        agent_version="",
        environment="",
        start_time_ns=0,
    )

    policy_pass = assert_span_order(["think", "act"])
    assert policy_pass(trace).action == ActionType.ALLOW

    policy_fail = assert_span_order(["act", "think"])
    assert policy_fail(trace).action == ActionType.BLOCK
