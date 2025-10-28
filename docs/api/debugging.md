# Debugging API Reference

This page documents the complete API for Clearstone's time-travel debugging system.

## CheckpointManager

Creates, saves, and loads agent state checkpoints.

```python
from clearstone.debugging import CheckpointManager

manager = CheckpointManager(checkpoint_dir=".checkpoints")
```

::: clearstone.debugging.checkpoint.CheckpointManager

## ReplayEngine

Restores agent state from checkpoints and enables interactive debugging.

```python
from clearstone.debugging import ReplayEngine

checkpoint = manager.load_checkpoint("checkpoint.ckpt")
# Pass trace_store to access all spans in the trace
engine = ReplayEngine(checkpoint, trace_store=provider.trace_store)
```

::: clearstone.debugging.replay.ReplayEngine

## Checkpoint Models

### Checkpoint

Complete snapshot of agent state at a specific execution point.

```python
checkpoint = manager.create_checkpoint(agent, trace, span_id)

print(f"Agent: {checkpoint.agent_class_path}")
print(f"Timestamp: {checkpoint.timestamp_ns}")
print(f"State: {checkpoint.agent_state}")
```

::: clearstone.debugging.checkpoint.Checkpoint

### CheckpointSerializer

Handles serialization and deserialization of checkpoints.

::: clearstone.debugging.checkpoint.CheckpointSerializer

## Replay Utilities

### DeterministicExecutionContext

Provides deterministic execution context for reproducible debugging.

::: clearstone.debugging.replay.DeterministicExecutionContext

