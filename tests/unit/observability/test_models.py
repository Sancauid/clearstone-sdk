# tests/unit/observability/test_models.py

import pytest
import time
from datetime import datetime, timezone
from clearstone.observability.models import (
    Span, Trace, SpanKind, SpanStatus, SpanEvent, SpanLink
)

def test_span_creation_with_required_fields():
    """Test creating a Span with the minimum required fields."""
    start_time = time.time_ns()
    span = Span(
        trace_id="trace_01",
        name="test_operation",
        start_time_ns=start_time,
        instrumentation_name="test_suite",
        instrumentation_version="1.0"
    )

    assert span.trace_id == "trace_01"
    assert span.name == "test_operation"
    assert len(span.span_id) == 32  # UUID hex length
    assert span.parent_span_id is None
    assert span.kind == SpanKind.INTERNAL
    assert span.status == SpanStatus.UNSET
    assert span.start_time_ns == start_time
    assert span.end_time_ns is None
    assert span.duration_ns is None

def test_span_full_initialization():
    """Test creating a Span with all fields populated."""
    event = SpanEvent(name="started_processing")
    link = SpanLink(trace_id="trace_02", span_id="span_linked")
    
    span = Span(
        trace_id="trace_03",
        span_id="span_01",
        parent_span_id="span_parent",
        name="complex_op",
        kind=SpanKind.CLIENT,
        start_time_ns=1000,
        end_time_ns=2500,
        status=SpanStatus.OK,
        attributes={"model": "gpt-4"},
        events=[event],
        links=[link],
        input_snapshot={"data": "input"},
        output_snapshot={"data": "output"},
        policy_decisions=[{"policy": "test_policy", "decision": "ALLOW"}],
        instrumentation_name="test_suite",
        instrumentation_version="1.0"
    )

    assert span.parent_span_id == "span_parent"
    assert span.kind == SpanKind.CLIENT
    assert span.status == SpanStatus.OK
    assert span.attributes["model"] == "gpt-4"
    assert len(span.events) == 1
    assert span.events[0].name == "started_processing"
    assert span.links[0].trace_id == "trace_02"
    assert span.duration_ns == 1500

def test_span_event_timestamp():
    """Test that SpanEvent has a default timestamp."""
    now = datetime.now(timezone.utc)
    event = SpanEvent(name="test_event")
    assert (event.timestamp - now).total_seconds() < 1

def test_trace_model_holds_spans():
    """Test the Trace model."""
    span1 = Span(trace_id="t1", name="s1", start_time_ns=1, instrumentation_name="t", instrumentation_version="1")
    span2 = Span(trace_id="t1", name="s2", start_time_ns=2, instrumentation_name="t", instrumentation_version="1")
    
    trace = Trace(
        trace_id="t1",
        root_span_id=span1.span_id,
        spans=[span1, span2],
        agent_id="test_agent",
        agent_version="v2",
        environment="testing",
        start_time_ns=1
    )

    assert trace.trace_id == "t1"
    assert len(trace.spans) == 2
    assert trace.agent_id == "test_agent"

