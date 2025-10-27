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
    """Creates a mock Checkpoint object for testing."""
    agent = ReplayableAgent(initial_value=10)
    span = Span(
        trace_id="t1",
        span_id="s1",
        name="test_span",
        start_time_ns=0,
        instrumentation_name="test",
        instrumentation_version="1",
    )

    return Checkpoint(
        trace_id="t1",
        span_id="s1",
        agent_class_path="tests.unit.debugging.test_replay.ReplayableAgent",
        clearstone_version="0.1.0",
        agent_state=agent.get_state(),
        current_span=span,
    )


def test_replay_engine_rehydrates_agent_state(mock_checkpoint):
    """Test that the engine correctly loads the agent and its state."""
    engine = ReplayEngine(mock_checkpoint)

    assert isinstance(engine.agent, ReplayableAgent)
    assert engine.agent.counter == 10
    assert engine.agent.history == []


@patch("pdb.set_trace")
@patch("clearstone.debugging.replay.DeterministicExecutionContext")
def test_start_debugging_session_calls_pdb_and_context(
    mock_context, mock_pdb, mock_checkpoint
):
    """Test that the main debugging method correctly initiates pdb and the deterministic context."""
    engine = ReplayEngine(mock_checkpoint)

    mock_context_instance = MagicMock()
    mock_context.return_value.__enter__.return_value = mock_context_instance
    mock_context.return_value.__exit__.return_value = None

    engine.start_debugging_session("run_step", 5)

    mock_pdb.assert_called_once()

    mock_context.assert_called_once()
