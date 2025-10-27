import pdb
import time
import random
from unittest.mock import patch
from typing import Any, List

from .checkpoint import Checkpoint

class DeterministicExecutionContext:
  """
  A context manager that mocks non-deterministic functions (like time and random)
  to ensure a replay is deterministic. It can also mock external calls.
  """
  def __init__(self, checkpoint: Checkpoint):
    self.checkpoint = checkpoint
    self._patches = []
    self._mocked_llm_responses = self._extract_mocked_responses("llm")
    self._mocked_tool_responses = self._extract_mocked_responses("tool")

  def _extract_mocked_responses(self, span_type: str) -> List[Any]:
    """Extracts outputs from spans of a specific type to be used as mocks."""
    responses = []
    from clearstone.serialization.hybrid import HybridSerializer
    serializer = HybridSerializer()
    
    all_spans = self.checkpoint.upstream_spans + [self.checkpoint.current_span]
    for span in sorted(all_spans, key=lambda s: s.start_time_ns):
      if span.span_type == span_type and span.output_snapshot:
        if span.output_snapshot.get("captured"):
          responses.append(serializer.deserialize(span.output_snapshot["data"]))
    return responses

  def __enter__(self):
    """Applies all the patches."""
    patcher_time = patch('time.time', return_value=self.checkpoint.timestamp_ns / 1e9)
    
    patcher_random = patch('random.random', return_value=0.5)
    
    patcher_llm = patch('your_agent_module.llm.invoke', side_effect=self._mocked_llm_responses)
    patcher_tool = patch('your_agent_module.tools.run', side_effect=self._mocked_tool_responses)

    self._patches = [patcher_time, patcher_random, patcher_llm, patcher_tool]
    for p in self._patches:
      p.start()
    
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    """Stops all patches."""
    for p in self._patches:
      p.stop()

class ReplayEngine:
  """
  Loads a checkpoint and rehydrates an agent to allow for interactive,
  time-travel debugging.
  """
  def __init__(self, checkpoint: Checkpoint):
    self.checkpoint = checkpoint
    self.agent = self._rehydrate_agent()

  def _rehydrate_agent(self) -> Any:
    """
    Dynamically imports the agent's class and restores its state
    from the checkpoint.
    """
    module_name, class_name = self.checkpoint.agent_class_path.rsplit('.', 1)
    try:
      module = __import__(module_name, fromlist=[class_name])
      agent_class = getattr(module, class_name)
    except (ImportError, AttributeError) as e:
      raise ImportError(f"Could not import agent class '{self.checkpoint.agent_class_path}'. Ensure it's in your PYTHONPATH.") from e

    agent_instance = agent_class.__new__(agent_class)
    
    if hasattr(agent_instance, 'load_state'):
      agent_instance.load_state(self.checkpoint.agent_state)
    else:
      agent_instance.__dict__.update(self.checkpoint.agent_state)
      
    return agent_instance

  def start_debugging_session(self, function_to_replay: str, *args, **kwargs):
    """
    Starts an interactive debugging session using pdb.
    
    Args:
      function_to_replay: The name of the method on the agent to call.
      *args, **kwargs: The arguments to pass to that method.
    """
    print("\n--- 🕰️ Welcome to the Clearstone Time-Travel Debugger ---")
    print(f"  Trace ID: {self.checkpoint.trace_id}")
    print(f"  Checkpoint: {self.checkpoint.checkpoint_id} (at span: '{self.checkpoint.current_span.name}')")
    print(f"  Agent State: Rehydrated for '{self.checkpoint.agent_class_path}'")
    print("\nDropping into interactive debugger (pdb). Type 'c' to continue execution from the checkpoint.")
    print("-" * 60)
    
    replay_method = getattr(self.agent, function_to_replay)

    pdb.set_trace()
    
    with DeterministicExecutionContext(self.checkpoint):
      result = replay_method(*args, **kwargs)
      print("-" * 60)
      print(f"--- ✅ Replay finished. Final result: {result} ---")
      return result

