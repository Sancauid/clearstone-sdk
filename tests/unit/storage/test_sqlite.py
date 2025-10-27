# tests/unit/storage/test_sqlite.py

import sqlite3
import threading
import time
from unittest.mock import patch

import pytest

from clearstone.observability.models import Span
from clearstone.storage.sqlite import SpanBuffer, TraceStore


@pytest.fixture
def db_path(tmp_path):
    """Provides a temporary path for the SQLite database."""
    return tmp_path / "test_traces.db"


@pytest.fixture
def trace_store(db_path):
    """Fixture for a TraceStore instance with a temporary database."""
    return TraceStore(db_path=str(db_path))


def create_mock_span(trace_id, name):
    return Span(
        trace_id=trace_id,
        name=name,
        start_time_ns=time.time_ns(),
        instrumentation_name="test",
        instrumentation_version="1.0",
    )


def test_trace_store_initialization(trace_store, db_path):
    """Test that the database file and tables are created on initialization."""
    assert db_path.exists()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='spans';"
    )
    assert cursor.fetchone() is not None
    conn.close()


def test_write_and_read_spans(trace_store):
    """Test a simple write and read roundtrip."""
    span1 = create_mock_span("t1", "op1")
    trace_store.write_spans([span1])

    trace = trace_store.get_trace("t1")
    assert trace is not None
    assert len(trace.spans) == 1
    assert trace.spans[0].span_id == span1.span_id
    assert trace.spans[0].name == "op1"


def test_span_buffer_flushes_on_batch_size(trace_store):
    """Test that the buffer flushes automatically when the batch size is reached."""
    with patch.object(trace_store, "write_spans") as mock_write:
        buffer = SpanBuffer(writer=trace_store, batch_size=2, flush_interval_s=10)

        buffer.add_span(create_mock_span("t1", "s1"))
        assert mock_write.call_count == 0

        buffer.add_span(create_mock_span("t1", "s2"))
        time.sleep(0.1)

        assert mock_write.call_count == 1
        assert len(mock_write.call_args[0][0]) == 2
        buffer.shutdown()


def test_span_buffer_flushes_on_interval(trace_store):
    """Test that the buffer flushes automatically based on the time interval."""
    with patch.object(trace_store, "write_spans") as mock_write:
        buffer = SpanBuffer(writer=trace_store, batch_size=10, flush_interval_s=0.1)

        buffer.add_span(create_mock_span("t2", "s1"))
        assert mock_write.call_count == 0

        time.sleep(0.2)

        assert mock_write.call_count == 1
        assert len(mock_write.call_args[0][0]) == 1
        buffer.shutdown()


def test_span_buffer_is_thread_safe(trace_store):
    """Test that the buffer handles concurrent adds from multiple threads."""
    with patch.object(trace_store, "write_spans", wraps=trace_store.write_spans):
        buffer = SpanBuffer(writer=trace_store, batch_size=50, flush_interval_s=0.2)

        num_threads = 10
        spans_per_thread = 10
        total_spans = num_threads * spans_per_thread

        def worker(thread_id):
            for i in range(spans_per_thread):
                buffer.add_span(create_mock_span(f"trace_{thread_id}", f"span_{i}"))

        threads = [
            threading.Thread(target=worker, args=(i,)) for i in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        buffer.shutdown()

        conn = sqlite3.connect(trace_store.db_path)
        count = conn.execute("SELECT COUNT(*) FROM spans").fetchone()[0]
        conn.close()
        assert count == total_spans
