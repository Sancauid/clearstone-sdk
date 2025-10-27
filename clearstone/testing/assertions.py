from typing import Callable, List
from clearstone.observability.models import Span, Trace, SpanStatus
from clearstone.core.actions import Decision, BLOCK, ALLOW

PolicyFunc = Callable[[Trace], Decision]

def assert_tool_was_called(tool_name: str, times: int = None, reason: str = None) -> PolicyFunc:
  """
  Creates a policy that asserts a specific tool was called.

  Args:
    tool_name: The name of the tool to check for.
    times: If provided, asserts the tool was called exactly this many times.
    reason: Custom failure message.
  """
  def policy(trace: Trace) -> Decision:
    tool_spans = [span for span in trace.spans if span.attributes.get("tool.name") == tool_name]

    if times is not None:
      if len(tool_spans) != times:
        failure_reason = reason or f"Expected tool '{tool_name}' to be called {times} time(s), but it was called {len(tool_spans)} time(s)."
        return BLOCK(failure_reason)
    else:
      if not tool_spans:
        failure_reason = reason or f"Expected tool '{tool_name}' to be called at least once, but it was not."
        return BLOCK(failure_reason)

    return ALLOW
  return policy

def assert_llm_cost_is_less_than(max_cost: float, reason: str = None) -> PolicyFunc:
  """
  Creates a policy that asserts the total LLM cost of a trace is below a threshold.
  """
  def policy(trace: Trace) -> Decision:
    total_cost = sum(span.attributes.get("llm.cost", 0) for span in trace.spans if "llm.cost" in span.attributes)

    if total_cost >= max_cost:
      failure_reason = reason or f"Total LLM cost ${total_cost:.4f} exceeded the limit of ${max_cost:.4f}."
      return BLOCK(failure_reason)

    return ALLOW
  return policy

def assert_no_errors_in_trace(reason: str = None) -> PolicyFunc:
  """
  Creates a policy that asserts no spans in the trace have an ERROR status.
  """
  def policy(trace: Trace) -> Decision:
    error_spans = [span for span in trace.spans if span.status == SpanStatus.ERROR]

    if error_spans:
      first_error = error_spans[0]
      failure_reason = reason or f"Trace failed. At least one error was found, starting with span '{first_error.name}': {first_error.error_message}"
      return BLOCK(failure_reason)

    return ALLOW
  return policy

def assert_span_order(span_names: List[str], reason: str = None) -> PolicyFunc:
  """
  Creates a policy that asserts a specific sequence of spans occurred in order.
  Note: This is a simple subsequence check, not a strict adjacency check.
  """
  def policy(trace: Trace) -> Decision:
    span_name_sequence = [span.name for span in trace.spans]

    it = iter(span_name_sequence)
    if all(name in it for name in span_names):
      return ALLOW
    else:
      failure_reason = reason or f"Expected span sequence {span_names} was not found in the correct order."
      return BLOCK(failure_reason)
  return policy

