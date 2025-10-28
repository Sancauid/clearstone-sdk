from unittest.mock import MagicMock, patch

import pytest

from clearstone.debugging.checkpoint import Checkpoint
from clearstone.debugging.replay import ReplayEngine
from clearstone.observability.models import Span


class ReplayableAgent:
    def __init__(self, initial_value=0):
        self.counter = initial_value
        self.history = []

    def get_state(self):
        return {"counter": self.counter, "history": self.history}

    def load_state(self, state):
        self.counter = state.get("counter", 0)
        self.history = state.get("history", [])

    def run_step(self, increment):
        import random

        self.counter += increment + random.random()
        self.history.append(f"Incremented by {increment}")
        return self.counter


@pytest.fixture
def mock_checkpoint():
    """Creates a mock Checkpoint with a recorded tool call output."""
    agent = ReplayableAgent(initial_value=10)

    from clearstone.serialization.hybrid import SelectiveSnapshotCapture

    # Simulate a trace where a tool was called and returned 'mocked_tool_output'
    tool_span = Span(
        trace_id="t1",
        span_id="s_tool",
        name="tool_call",  # Name starts with "tool" for matching
        output_snapshot=SelectiveSnapshotCapture.capture("mocked_tool_output"),
        start_time_ns=1,
        instrumentation_name="test",
        instrumentation_version="1",
    )

    current_span = Span(
        trace_id="t1",
        span_id="s_current",
        parent_span_id="s_tool",
        name="current_op",
        start_time_ns=2,
        instrumentation_name="test",
        instrumentation_version="1",
    )

    return Checkpoint(
        trace_id="t1",
        span_id="s_current",
        agent_class_path="tests.unit.debugging.test_replay.ReplayableAgent",
        clearstone_version="0.1.0",
        agent_state=agent.get_state(),
        current_span=current_span,
        upstream_spans=[tool_span],
    )


def test_replay_engine_rehydrates_agent_state(mock_checkpoint):
    """Test that the engine correctly loads the agent and its state."""
    engine = ReplayEngine(mock_checkpoint)

    assert isinstance(engine.agent, ReplayableAgent)
    assert engine.agent.counter == 10
    assert engine.agent.history == []


@patch("pdb.set_trace")
def test_start_debugging_session_with_mock_config(mock_pdb, mock_checkpoint):
    """Test that the engine correctly configures mocks and runs."""
    # Create a mock trace store with the full trace
    mock_trace_store = MagicMock()
    mock_trace = MagicMock()
    mock_trace.spans = mock_checkpoint.upstream_spans + [mock_checkpoint.current_span]
    mock_trace_store.get_trace.return_value = mock_trace

    engine = ReplayEngine(mock_checkpoint, trace_store=mock_trace_store)

    # This is the user's configuration
    mock_config = {"tool": "tests.unit.debugging.test_replay.ReplayableAgent.run_step"}

    # We are replaying a function that will internally call the mocked function.
    # We will mock the 'run_step' method itself to test the flow.

    # We need to simulate the execution environment of start_debugging_session
    with patch(
        "clearstone.debugging.replay.DeterministicExecutionContext"
    ) as mock_exec_context:
        engine.start_debugging_session(
            "run_step",  # The function we are replaying
            mock_config=mock_config,
            increment=5,  # Argument for run_step
        )

        # Assert that our execution context was initialized with the correct mock data
        mock_exec_context.assert_called_once()
        args, kwargs = mock_exec_context.call_args
        # The second argument should be the mock_targets dictionary
        mock_targets = args[1]

        assert (
            "tests.unit.debugging.test_replay.ReplayableAgent.run_step" in mock_targets
        )
        # It should have found the one recorded "tool" response from our mock checkpoint
        assert (
            len(
                mock_targets[
                    "tests.unit.debugging.test_replay.ReplayableAgent.run_step"
                ]
            )
            == 1
        )
        assert (
            mock_targets["tests.unit.debugging.test_replay.ReplayableAgent.run_step"][0]
            == "mocked_tool_output"
        )

        # Verify trace store was used
        mock_trace_store.get_trace.assert_called_once_with(mock_checkpoint.trace_id)
