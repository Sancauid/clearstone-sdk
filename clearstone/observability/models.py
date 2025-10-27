# clearstone/observability/models.py

import uuid
from enum import Enum
from typing import Any, Optional, Dict, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

# --- OTel-Aligned Enumerations ---

class SpanKind(str, Enum):
    """OTel-aligned span kind categorization."""
    INTERNAL = "INTERNAL"        # Default for internal operations
    CLIENT = "CLIENT"            # Represents a client-side call (e.g., LLM API)
    SERVER = "SERVER"            # Represents a server-side handling of a call
    PRODUCER = "PRODUCER"        # For message queue producers
    CONSUMER = "CONSUMER"        # For message queue consumers

class SpanStatus(str, Enum):
    """Execution status of a span."""
    UNSET = "UNSET"              # Default status
    OK = "OK"                    # Operation completed successfully
    ERROR = "ERROR"              # Operation failed

# --- Core Data Models ---

class SpanEvent(BaseModel):
    """Represents a point-in-time event within a span's lifecycle."""
    name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attributes: Dict[str, Any] = Field(default_factory=dict)

class SpanLink(BaseModel):
    """Represents a causal link to another span, possibly in a different trace."""
    trace_id: str
    span_id: str
    attributes: Dict[str, Any] = Field(default_factory=dict)

class Span(BaseModel):
    """
    The core data structure for a single traced operation, designed for
    high-fidelity capture and replay.
    """
    # === Identity & Hierarchy ===
    trace_id: str
    span_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    parent_span_id: Optional[str] = None
    
    # === Execution Context ===
    name: str  # e.g., "agent.think" or "tool.calculator"
    kind: SpanKind = SpanKind.INTERNAL
    
    # === Timing (nanosecond precision) ===
    start_time_ns: int
    end_time_ns: Optional[int] = None
    
    # === Execution Metadata ===
    attributes: Dict[str, Any] = Field(default_factory=dict)
    events: List[SpanEvent] = Field(default_factory=list)
    links: List[SpanLink] = Field(default_factory=list)
    
    # === Status and Errors ===
    status: SpanStatus = SpanStatus.UNSET
    error_message: Optional[str] = None
    error_stacktrace: Optional[str] = None
    
    # === Replay-Critical Snapshots ===
    input_snapshot: Optional[Dict[str, Any]] = None
    output_snapshot: Optional[Dict[str, Any]] = None
    
    # === Governance Integration ===
    policy_decisions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # === Instrumentation Metadata ===
    instrumentation_name: str
    instrumentation_version: str
    
    model_config = ConfigDict(use_enum_values=False)  # Keep enums as objects for type safety

    @property
    def duration_ns(self) -> Optional[int]:
        """Calculates the span duration in nanoseconds if the span is complete."""
        if self.end_time_ns is None:
            return None
        return self.end_time_ns - self.start_time_ns

class Trace(BaseModel):
    """A collection of spans for a complete agent execution."""
    trace_id: str
    root_span_id: str
    spans: List[Span]
    
    # Trace-level metadata
    agent_id: str
    agent_version: str
    environment: str
    start_time_ns: int
    end_time_ns: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

