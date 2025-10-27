import uuid
import time
import pickle
import json
import base64
import sys
import os
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from clearstone.observability.models import Span, Trace

class Checkpoint(BaseModel):
  """
  A snapshot of an agent's state at a specific point in a trace,
  designed to be rehydrated by the ReplayEngine.
  """
  checkpoint_id: str = Field(default_factory=lambda: f"ckpt_{uuid.uuid4().hex}")
  trace_id: str
  span_id: str
  
  timestamp_ns: int = Field(default_factory=time.time_ns)
  
  agent_state: Dict[str, Any]
  agent_class_path: str
  
  current_span: Span
  upstream_spans: List[Span] = Field(default_factory=list)
  
  python_version: str = Field(default=f"{sys.version_info.major}.{sys.version_info.minor}")
  clearstone_version: str

class CheckpointSerializer:
  """Handles the serialization and deserialization of Checkpoint objects."""
  
  @staticmethod
  def serialize(checkpoint: Checkpoint) -> bytes:
    """
    Serializes a checkpoint using a hybrid JSON/pickle approach.
    Metadata is JSON for readability, while the agent state is pickled for fidelity.
    """
    agent_state_pickled = pickle.dumps(checkpoint.agent_state, protocol=pickle.HIGHEST_PROTOCOL)
    
    payload = {
      "metadata": {
        "checkpoint_id": checkpoint.checkpoint_id,
        "trace_id": checkpoint.trace_id,
        "span_id": checkpoint.span_id,
        "timestamp_ns": checkpoint.timestamp_ns,
        "agent_class_path": checkpoint.agent_class_path,
        "python_version": checkpoint.python_version,
        "clearstone_version": checkpoint.clearstone_version,
      },
      "current_span": checkpoint.current_span.model_dump(mode='json'),
      "upstream_spans": [s.model_dump(mode='json') for s in checkpoint.upstream_spans],
      "agent_state_pickle_b64": base64.b64encode(agent_state_pickled).decode('utf-8'),
    }
    return json.dumps(payload).encode('utf-8')

  @staticmethod
  def deserialize(data: bytes) -> Checkpoint:
    """Deserializes bytes back into a Checkpoint object."""
    payload = json.loads(data.decode('utf-8'))
    metadata = payload['metadata']
    
    agent_state_pickled = base64.b64decode(payload['agent_state_pickle_b64'].encode('utf-8'))
    agent_state = pickle.loads(agent_state_pickled)
    
    current_span = Span.model_validate(payload['current_span'])
    upstream_spans = [Span.model_validate(s) for s in payload['upstream_spans']]
    
    return Checkpoint(
      checkpoint_id=metadata['checkpoint_id'],
      trace_id=metadata['trace_id'],
      span_id=metadata['span_id'],
      timestamp_ns=metadata['timestamp_ns'],
      agent_class_path=metadata['agent_class_path'],
      python_version=metadata['python_version'],
      clearstone_version=metadata['clearstone_version'],
      agent_state=agent_state,
      current_span=current_span,
      upstream_spans=upstream_spans
    )

class CheckpointManager:
  """Manages the creation, storage, and retrieval of checkpoints."""
  
  def __init__(self, checkpoint_dir: str = ".clearstone_checkpoints"):
    self.checkpoint_dir = Path(checkpoint_dir)
    self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    self.sdk_version = "0.1.0"

  def _get_upstream_spans(self, target_span: Span, trace: Trace) -> List[Span]:
    """Helper to find all ancestors of a given span in a trace."""
    upstream_map = {s.span_id: s for s in trace.spans}
    ancestors = []
    current_id = target_span.parent_span_id
    while current_id and current_id in upstream_map:
      parent_span = upstream_map[current_id]
      ancestors.insert(0, parent_span)
      current_id = parent_span.parent_span_id
    return ancestors

  def create_checkpoint(self, agent: Any, trace: Trace, span_id: str) -> Checkpoint:
    """
    Creates a checkpoint for a given agent at a specific span within a trace.
    """
    target_span = next((s for s in trace.spans if s.span_id == span_id), None)
    if not target_span:
      raise ValueError(f"Span ID '{span_id}' not found in the provided trace.")

    if not hasattr(agent, 'get_state'):
      raise TypeError("Agent must have a 'get_state()' method to be checkpointable.")
    
    agent_state = agent.get_state()
    
    checkpoint = Checkpoint(
      trace_id=trace.trace_id,
      span_id=span_id,
      agent_class_path=f"{agent.__class__.__module__}.{agent.__class__.__name__}",
      clearstone_version=self.sdk_version,
      agent_state=agent_state,
      current_span=target_span,
      upstream_spans=self._get_upstream_spans(target_span, trace)
    )
    
    self._save_checkpoint(checkpoint)
    return checkpoint

  def _save_checkpoint(self, checkpoint: Checkpoint):
    """Serializes and saves a checkpoint to a file."""
    filename = f"{checkpoint.trace_id}_{checkpoint.checkpoint_id}.ckpt"
    filepath = self.checkpoint_dir / filename
    
    serialized_data = CheckpointSerializer.serialize(checkpoint)
    filepath.write_bytes(serialized_data)

  def load_checkpoint(self, path: str) -> Checkpoint:
    """Loads and deserializes a checkpoint from a file."""
    filepath = Path(path)
    if not filepath.exists():
      raise FileNotFoundError(f"Checkpoint file not found: {path}")
      
    serialized_data = filepath.read_bytes()
    return CheckpointSerializer.deserialize(serialized_data)

