# clearstone/core/actions.py

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List

class ActionType(Enum):
    """
    Defines the set of possible outcomes from a policy evaluation.
    These are simple, stateless actions represented as singleton instances.
    """
    ALLOW = "allow"
    BLOCK = "block"
    PAUSE = "pause"
    ALERT = "alert"
    REDACT = "redact"
    SKIP = "skip"

@dataclass(frozen=True)
class Decision:
    """
    Represents a policy decision, including the action and any associated state
    (e.g., a reason for blocking, metadata). Frozen for immutability.
    """
    action: ActionType
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_block(self) -> bool:
        """Helper method to check if this is a blocking decision."""
        return self.action == ActionType.BLOCK

ALLOW = Decision(ActionType.ALLOW)
PAUSE = Decision(ActionType.PAUSE)
ALERT = Decision(ActionType.ALERT)
SKIP = Decision(ActionType.SKIP)

def BLOCK(reason: str, **metadata) -> Decision:
    """
    Factory function to create a BLOCK decision. A reason is mandatory.
    """
    if not reason or not isinstance(reason, str):
        raise ValueError("BLOCK decision requires a non-empty string reason.")
    return Decision(action=ActionType.BLOCK, reason=reason, metadata=metadata)

def REDACT(reason: str, fields: List[str], **metadata) -> Decision:
    """
    Factory function to create a REDACT decision. A list of fields is mandatory.
    """
    if not fields or not isinstance(fields, list):
        raise ValueError("REDACT decision requires a non-empty list of fields.")
    metadata['fields_to_redact'] = fields
    return Decision(action=ActionType.REDACT, reason=reason, metadata=metadata)
