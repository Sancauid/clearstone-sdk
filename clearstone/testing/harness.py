import sqlite3
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable, Optional

from clearstone.observability.models import Span, Trace, SpanStatus
from clearstone.core.actions import Decision, ActionType

@dataclass
class PolicyTestResult:
  """Holds the results of a single policy backtest simulation."""
  policy_name: str
  traces_analyzed: int
  spans_analyzed: int
  decisions: Dict[ActionType, int] = field(default_factory=lambda: {action: 0 for action in ActionType})
  blocked_trace_ids: List[str] = field(default_factory=list)

  def summary(self) -> Dict[str, Any]:
    """Returns a dictionary summarizing the test results."""
    total_decisions = sum(self.decisions.values())
    block_rate = (self.decisions.get(ActionType.BLOCK, 0) / total_decisions) if total_decisions > 0 else 0
    return {
      "policy_name": self.policy_name,
      "traces_analyzed": self.traces_analyzed,
      "spans_analyzed": self.spans_analyzed,
      "decisions": {k.value: v for k, v in self.decisions.items()},
      "runs_blocked": len(self.blocked_trace_ids),
      "block_rate_percent": f"{block_rate:.2%}",
    }

class PolicyTestHarness:
  """
  A tool for backtesting new governance policies against a database of
  historical execution traces.
  """
  def __init__(self, trace_db_path: str):
    """Initializes the harness with a path to a Clearstone trace database."""
    self.db_path = trace_db_path
    self._conn = sqlite3.connect(self.db_path)

  def _row_to_span(self, row: sqlite3.Row) -> Span:
    """Converts a database row into a Span object."""
    return Span(
      span_id=row['span_id'],
      trace_id=row['trace_id'],
      parent_span_id=row['parent_span_id'],
      name=row['name'],
      kind=row['kind'],
      start_time_ns=row['start_time_ns'],
      end_time_ns=row['end_time_ns'],
      status=row['status'],
      attributes=json.loads(row['attributes_json'] or '{}'),
      input_snapshot=json.loads(row['input_snapshot_json'] or 'null'),
      output_snapshot=json.loads(row['output_snapshot_json'] or 'null'),
      error_message=row['error_message'],
      instrumentation_name=row['instrumentation_name'],
      instrumentation_version=row['instrumentation_version']
    )

  def load_traces(self, limit: int = 100) -> List[Trace]:
    """
    Loads a set of historical traces from the database.

    Args:
      limit: The maximum number of recent traces to load.
    """
    self._conn.row_factory = sqlite3.Row
    cursor = self._conn.cursor()

    cursor.execute("SELECT DISTINCT trace_id FROM spans ORDER BY start_time_ns DESC LIMIT ?", (limit,))
    trace_ids = [row['trace_id'] for row in cursor.fetchall()]

    traces = []
    for trace_id in trace_ids:
      cursor.execute("SELECT * FROM spans WHERE trace_id = ? ORDER BY start_time_ns ASC", (trace_id,))
      spans = [self._row_to_span(row) for row in cursor.fetchall()]
      if spans:
        traces.append(Trace(trace_id=trace_id, spans=spans, root_span_id=spans[0].span_id, agent_id="", agent_version="", environment="", start_time_ns=spans[0].start_time_ns))
    return traces

  def simulate_policy(self, policy: Callable[[Trace], Decision], traces: List[Trace]) -> PolicyTestResult:
    """
    Simulates the impact of a trace-level policy against a set of historical traces.

    Args:
      policy: A policy function that takes a Trace and returns a Decision.
      traces: A list of Trace objects to test against.

    Returns:
      A PolicyTestResult object with a full report of the simulation.
    """
    policy_name = getattr(policy, '__name__', 'anonymous_policy')
    result = PolicyTestResult(
      policy_name=policy_name,
      traces_analyzed=len(traces),
      spans_analyzed=sum(len(t.spans) for t in traces)
    )

    for trace in traces:
      decision = policy(trace)
      result.decisions[decision.action] += 1

      if decision.is_block():
        result.blocked_trace_ids.append(trace.trace_id)

    return result

  def simulate_span_policy(self, policy: Callable[[Span], Decision], traces: List[Trace]) -> PolicyTestResult:
    """
    Simulates the impact of a span-level policy against a set of historical traces.

    Args:
      policy: A policy function that takes a Span and returns a Decision.
      traces: A list of Trace objects to test against.

    Returns:
      A PolicyTestResult object with a full report of the simulation.
    """
    policy_name = getattr(policy, '__name__', 'anonymous_policy')
    result = PolicyTestResult(
      policy_name=policy_name,
      traces_analyzed=len(traces),
      spans_analyzed=sum(len(t.spans) for t in traces)
    )

    for trace in traces:
      trace_was_blocked = False
      for span in trace.spans:
        decision = policy(span)

        result.decisions[decision.action] += 1

        if decision.is_block() and not trace_was_blocked:
          result.blocked_trace_ids.append(trace.trace_id)
          trace_was_blocked = True

    return result

  def __del__(self):
    """Ensure the database connection is closed when the object is destroyed."""
    if self._conn:
      self._conn.close()

