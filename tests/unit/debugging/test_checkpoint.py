from typing import List

import pytest

from clearstone.debugging.checkpoint import (
    Checkpoint,
    CheckpointManager,
    CheckpointSerializer,
)
from clearstone.observability.models import Span, Trace


class MockAgent:
    def __init__(self, memory: List[str]):
        self.memory = memory

    def get_state(self):
        """A simple state extraction method for checkpointing."""
        return {"memory": self.memory}


@pytest.fixture
def mock_trace():
    """Creates a mock trace with a simple parent-child hierarchy."""
    span1 = Span(
        trace_id="t1",
        span_id="s1",
        name="parent",
        start_time_ns=1,
        instrumentation_name="t",
        instrumentation_version="1",
    )
    span2 = Span(
        trace_id="t1",
        span_id="s2",
        name="child",
        parent_span_id="s1",
        start_time_ns=2,
        instrumentation_name="t",
        instrumentation_version="1",
    )
    return Trace(
        trace_id="t1",
        spans=[span1, span2],
        root_span_id="s1",
        agent_id="a1",
        agent_version="v1",
        environment="test",
        start_time_ns=1,
    )


@pytest.fixture
def checkpoint_manager(tmp_path):
    """Provides a CheckpointManager using a temporary directory."""
    return CheckpointManager(checkpoint_dir=str(tmp_path / ".checkpoints"))


def test_checkpoint_serialization_roundtrip():
    """Test that a Checkpoint can be serialized and deserialized without data loss."""
    agent = MockAgent(memory=["msg1", "msg2"])
    span = Span(
        trace_id="t1",
        span_id="s1",
        name="test",
        start_time_ns=1,
        instrumentation_name="t",
        instrumentation_version="1",
    )

    original_checkpoint = Checkpoint(
        trace_id="t1",
        span_id="s1",
        agent_class_path="tests.unit.debugging.test_checkpoint.MockAgent",
        clearstone_version="0.1.0",
        agent_state=agent.get_state(),
        current_span=span,
    )

    serialized_data = CheckpointSerializer.serialize(original_checkpoint)
    deserialized_checkpoint = CheckpointSerializer.deserialize(serialized_data)

    assert isinstance(deserialized_checkpoint, Checkpoint)
    assert original_checkpoint.checkpoint_id == deserialized_checkpoint.checkpoint_id
    assert (
        original_checkpoint.agent_state["memory"]
        == deserialized_checkpoint.agent_state["memory"]
    )
    assert (
        original_checkpoint.current_span.span_id
        == deserialized_checkpoint.current_span.span_id
    )


def test_checkpoint_manager_create_and_save(checkpoint_manager, mock_trace):
    """Test that the manager can create a checkpoint and save it to a file."""
    agent = MockAgent(memory=["hello"])

    checkpoint = checkpoint_manager.create_checkpoint(agent, mock_trace, span_id="s2")

    assert checkpoint is not None
    checkpoint_file = (
        checkpoint_manager.checkpoint_dir
        / f"{checkpoint.trace_id}_{checkpoint.checkpoint_id}.ckpt"
    )
    assert checkpoint_file.exists()
    assert checkpoint_file.stat().st_size > 0


def test_checkpoint_manager_load(checkpoint_manager, mock_trace):
    """Test that a saved checkpoint can be loaded back correctly."""
    agent = MockAgent(memory=["original state"])

    created_checkpoint = checkpoint_manager.create_checkpoint(
        agent, mock_trace, span_id="s2"
    )
    filepath = (
        checkpoint_manager.checkpoint_dir
        / f"{created_checkpoint.trace_id}_{created_checkpoint.checkpoint_id}.ckpt"
    )

    loaded_checkpoint = checkpoint_manager.load_checkpoint(str(filepath))

    assert loaded_checkpoint.checkpoint_id == created_checkpoint.checkpoint_id
    assert loaded_checkpoint.trace_id == "t1"
    assert loaded_checkpoint.span_id == "s2"
    assert loaded_checkpoint.agent_state["memory"] == ["original state"]
    assert loaded_checkpoint.current_span.name == "child"


def test_checkpoint_manager_finds_upstream_spans(checkpoint_manager, mock_trace):
    """Test that the manager correctly identifies and includes parent spans."""
    agent = MockAgent(memory=[])

    checkpoint = checkpoint_manager.create_checkpoint(agent, mock_trace, span_id="s2")

    assert len(checkpoint.upstream_spans) == 1
    assert checkpoint.upstream_spans[0].span_id == "s1"
    assert checkpoint.current_span.span_id == "s2"
