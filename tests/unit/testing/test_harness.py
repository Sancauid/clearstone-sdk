import pytest
import sqlite3
import json
from clearstone.testing.harness import PolicyTestHarness
from clearstone.observability.models import Span, SpanKind, SpanStatus
from clearstone.core.actions import ALLOW, BLOCK, Decision, ActionType

def create_mock_db_with_traces(db_path, traces_data):
  """Helper function to create and populate a temporary SQLite DB."""
  conn = sqlite3.connect(db_path)
  SCHEMA = """
  CREATE TABLE spans (
    span_id TEXT, trace_id TEXT, parent_span_id TEXT, name TEXT, kind TEXT,
    start_time_ns INTEGER, end_time_ns INTEGER, status TEXT,
    attributes_json TEXT, input_snapshot_json TEXT, output_snapshot_json TEXT,
    error_message TEXT, instrumentation_name TEXT, instrumentation_version TEXT
  );
  """
  conn.executescript(SCHEMA)
  cursor = conn.cursor()

  for trace_id, spans in traces_data.items():
    for span in spans:
      cursor.execute("INSERT INTO spans VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
        span['span_id'], trace_id, span.get('parent_span_id'), span['name'],
        span['kind'], span['start_time_ns'], None, span['status'],
        json.dumps(span['attributes']), None, None, None, "test", "1.0"
      ))
  conn.commit()
  conn.close()

def high_cost_span_policy(span: Span) -> Decision:
  """A simple span-level policy that blocks if 'cost' attribute is over 1.0."""
  if span.attributes.get("cost", 0) > 1.0:
    return BLOCK("Cost exceeds $1.00")
  return ALLOW

@pytest.fixture
def mock_trace_db(tmp_path):
  """Pytest fixture to create a temporary database with two traces."""
  db_file = tmp_path / "harness_test.db"
  traces_data = {
    "trace_1": [
      {'span_id': 's1a', 'name': 'op1', 'kind': 'INTERNAL', 'status': 'OK', 'start_time_ns': 1, 'attributes': {'cost': 0.5}},
      {'span_id': 's1b', 'name': 'op2', 'kind': 'CLIENT', 'status': 'OK', 'start_time_ns': 2, 'attributes': {'cost': 0.8}},
    ],
    "trace_2": [
      {'span_id': 's2a', 'name': 'op3', 'kind': 'INTERNAL', 'status': 'OK', 'start_time_ns': 3, 'attributes': {'cost': 0.2}},
      {'span_id': 's2b', 'name': 'op4', 'kind': 'CLIENT', 'status': 'ERROR', 'start_time_ns': 4, 'attributes': {'cost': 1.5}},
    ]
  }
  create_mock_db_with_traces(db_file, traces_data)
  return str(db_file)

def test_harness_initialization(mock_trace_db):
  """Test that the harness can be initialized with a database path."""
  harness = PolicyTestHarness(mock_trace_db)
  assert harness.db_path == mock_trace_db
  assert harness._conn is not None

def test_harness_load_traces(mock_trace_db):
  """Test that historical traces can be loaded from the database."""
  harness = PolicyTestHarness(mock_trace_db)
  traces = harness.load_traces(limit=5)

  assert len(traces) == 2
  trace_ids = {t.trace_id for t in traces}
  assert "trace_1" in trace_ids
  assert "trace_2" in trace_ids

  trace1 = next(t for t in traces if t.trace_id == "trace_1")
  assert len(trace1.spans) == 2

def test_harness_simulate_span_policy_calculates_impact(mock_trace_db):
  """Test the core simulation for span-level policies."""
  harness = PolicyTestHarness(mock_trace_db)
  traces = harness.load_traces()

  result = harness.simulate_span_policy(high_cost_span_policy, traces)

  assert result.policy_name == "high_cost_span_policy"
  assert result.traces_analyzed == 2
  assert result.spans_analyzed == 4

  assert result.decisions[ALLOW.action] == 3
  assert result.decisions[ActionType.BLOCK] == 1

  assert len(result.blocked_trace_ids) == 1
  assert result.blocked_trace_ids[0] == "trace_2"

def test_policy_test_result_summary(mock_trace_db):
  """Test the summary dictionary generation."""
  harness = PolicyTestHarness(mock_trace_db)
  traces = harness.load_traces()
  result = harness.simulate_span_policy(high_cost_span_policy, traces)

  summary = result.summary()

  assert summary["policy_name"] == "high_cost_span_policy"
  assert summary["traces_analyzed"] == 2
  assert summary["runs_blocked"] == 1
  assert summary["block_rate_percent"] == "25.00%"

