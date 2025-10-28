# clearstone/storage/sqlite.py

import json
import queue
import sqlite3
import threading
import time
from pathlib import Path
from typing import List, Optional

from clearstone.observability.models import Span, Trace

from .types import BaseSpanBuffer, BaseTraceStore

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS spans (
    span_id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    parent_span_id TEXT,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    start_time_ns INTEGER NOT NULL,
    end_time_ns INTEGER,
    status TEXT NOT NULL,
    attributes_json TEXT,
    input_snapshot_json TEXT,
    output_snapshot_json TEXT,
    error_message TEXT,
    instrumentation_name TEXT NOT NULL,
    instrumentation_version TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_spans_trace_id ON spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_spans_start_time ON spans(start_time_ns);
"""


class SpanBuffer(BaseSpanBuffer):
    """
    An in-memory, thread-safe buffer for spans that flushes them to a writer
    periodically or when the buffer is full. This decouples span creation
    from the I/O of writing to disk.
    """

    def __init__(
        self, writer: "TraceStore", batch_size: int = 100, flush_interval_s: int = 5
    ):
        self._queue = queue.Queue()
        self._writer = writer
        self._batch_size = batch_size
        self._flush_interval_s = flush_interval_s
        self._shutdown = threading.Event()

        self._flusher_thread = threading.Thread(
            target=self._periodic_flush, daemon=True
        )
        self._flusher_thread.start()

    def add_span(self, span: Span):
        """Add a span to the buffer. This is a non-blocking operation."""
        if not self._shutdown.is_set():
            self._queue.put(span)
            if self._queue.qsize() >= self._batch_size:
                self._flush_queue()

    def _periodic_flush(self):
        """The background worker thread that periodically flushes the queue."""
        while not self._shutdown.is_set():
            time.sleep(self._flush_interval_s)
            self._flush_queue()

    def _flush_queue(self):
        """Drains the queue and writes spans in batches."""
        spans_to_write = []
        while len(spans_to_write) < self._batch_size:
            try:
                span = self._queue.get_nowait()
                spans_to_write.append(span)
            except queue.Empty:
                break

        if spans_to_write:
            self._writer.write_spans(spans_to_write)

    def flush(self):
        """Manually trigger a flush of all buffered spans."""
        self._flush_queue()

    def shutdown(self):
        """Flush any remaining spans and stop the background thread."""
        self._shutdown.set()
        self.flush()
        self._flusher_thread.join()


class TraceStore(BaseTraceStore):
    """
    Manages the persistence of traces to a local SQLite database.
    This class handles database connections, schema creation, and writing data.
    """

    def __init__(self, db_path: str = "clearstone_traces.db"):
        self.db_path = Path(db_path)
        self._conn = None
        self._init_db()

    def _get_connection(self):
        """Establishes a thread-safe database connection."""
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        """Initializes the database and creates the necessary tables."""
        conn = self._get_connection()
        try:
            conn.executescript(SCHEMA_SQL)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.commit()
        finally:
            conn.close()

    def write_spans(self, spans: List[Span]):
        """
        Writes a batch of spans to the database in a single transaction.
        This is designed to be called by the SpanBuffer.
        """
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                values = []
                for span in spans:
                    values.append(
                        (
                            span.span_id,
                            span.trace_id,
                            span.parent_span_id,
                            span.name,
                            span.kind.value,
                            span.start_time_ns,
                            span.end_time_ns,
                            span.status.value,
                            json.dumps(span.attributes),
                            json.dumps(span.input_snapshot),
                            json.dumps(span.output_snapshot),
                            span.error_message,
                            span.instrumentation_name,
                            span.instrumentation_version,
                        )
                    )

                cursor.executemany(
                    "INSERT OR REPLACE INTO spans VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    values,
                )
        finally:
            conn.close()

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Retrieves all spans for a given trace_id and reconstructs the Trace."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM spans WHERE trace_id = ?", (trace_id,))
            rows = cursor.fetchall()

            if not rows:
                return None

            spans = []
            for row in rows:
                spans.append(
                    Span(
                        span_id=row[0],
                        trace_id=row[1],
                        parent_span_id=row[2],
                        name=row[3],
                        kind=row[4],
                        start_time_ns=row[5],
                        end_time_ns=row[6],
                        status=row[7],
                        attributes=json.loads(row[8] or "{}"),
                        input_snapshot=json.loads(row[9] or "null"),
                        output_snapshot=json.loads(row[10] or "null"),
                        error_message=row[11],
                        instrumentation_name=row[12],
                        instrumentation_version=row[13],
                    )
                )

            return Trace(
                trace_id=trace_id,
                spans=spans,
                root_span_id="",
                agent_id="",
                agent_version="",
                environment="",
                start_time_ns=0,
            )
        finally:
            conn.close()
