# tests/unit/observability/test_tracer.py

import threading
import time

import pytest

from clearstone.observability.models import SpanStatus
from clearstone.observability.tracer import get_tracer, reset_tracer_registry


@pytest.fixture(autouse=True)
def clean_tracer_registry():
    reset_tracer_registry()


def test_span_context_manager_creates_and_finalizes_span():
    """Test the basic lifecycle of a span using the context manager."""
    tracer = get_tracer("test_agent")

    with tracer.span("test_operation") as span:
        assert span.name == "test_operation"
        assert span.status == SpanStatus.UNSET
        assert span.end_time_ns is None
        time.sleep(0.01)

    assert span.status == SpanStatus.OK
    assert span.end_time_ns is not None
    assert span.duration_ns is not None and span.duration_ns > 0

    buffered_spans = tracer.get_buffered_spans()
    assert len(buffered_spans) == 1
    assert buffered_spans[0] is span


def test_span_context_manager_captures_exceptions():
    """Test that exceptions within a span are correctly captured."""
    tracer = get_tracer("test_agent")

    with pytest.raises(ValueError, match="Something went wrong"):
        with tracer.span("failing_operation"):
            raise ValueError("Something went wrong")

    buffered_spans = tracer.get_buffered_spans()
    assert len(buffered_spans) == 1
    failed_span = buffered_spans[0]

    assert failed_span.name == "failing_operation"
    assert failed_span.status == SpanStatus.ERROR
    assert failed_span.error_message == "Something went wrong"
    assert "Traceback" in failed_span.error_stacktrace


def test_nested_spans_have_correct_parent_child_relationship():
    """Test that nested spans correctly establish a parent-child hierarchy."""
    tracer = get_tracer("test_agent")

    with tracer.span("parent_op") as parent_span:
        with tracer.span("child_op") as child_span:
            assert child_span.parent_span_id == parent_span.span_id
            assert child_span.trace_id == parent_span.trace_id
            with tracer.span("grandchild_op") as grandchild_span:
                assert grandchild_span.parent_span_id == child_span.span_id

    spans = tracer.get_buffered_spans()
    assert len(spans) == 3

    grandchild, child, parent = spans
    assert parent.parent_span_id is None
    assert child.parent_span_id == parent.span_id
    assert grandchild.parent_span_id == child.span_id


def test_get_tracer_is_a_singleton_for_a_given_name():
    """Test that get_tracer returns the same instance for the same name."""
    tracer1 = get_tracer("shared_agent")
    tracer2 = get_tracer("shared_agent")
    assert tracer1 is tracer2

    tracer3 = get_tracer("other_agent")
    assert tracer1 is not tracer3


def test_tracer_is_thread_safe():
    """Test that spans from multiple threads are buffered correctly without conflicts."""
    tracer = get_tracer("multi_thread_agent")
    num_threads = 5
    spans_per_thread = 10

    def worker(thread_id):
        with tracer.span(f"thread_{thread_id}_root"):
            for i in range(spans_per_thread - 1):
                with tracer.span(f"op_{i}"):
                    time.sleep(0.001)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    buffered_spans = tracer.get_buffered_spans()
    assert len(buffered_spans) == num_threads * spans_per_thread

    thread_root_spans = [s for s in buffered_spans if "root" in s.name]
    assert len(thread_root_spans) == num_threads
    for root_span in thread_root_spans:
        assert root_span.parent_span_id is None
