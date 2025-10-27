# clearstone/integrations/langchain/callbacks.py

import dataclasses
from typing import Any, Dict, List, Optional

try:
    from langchain_core.callbacks.base import BaseCallbackHandler
except ImportError:
    from langchain.callbacks.base import BaseCallbackHandler

from clearstone.core.policy import PolicyEngine
from clearstone.core.context import PolicyContext, get_current_context, context_scope
from clearstone.core.actions import ActionType, Decision

class PolicyViolationError(Exception):
    """Custom exception raised when a policy returns a BLOCK decision."""
    def __init__(self, message: str, decision: Decision):
        super().__init__(message)
        self.decision = decision

class PolicyPauseError(Exception):
    """Custom exception raised when a policy returns a PAUSE decision."""
    def __init__(self, message: str, decision: Decision):
        super().__init__(message)
        self.decision = decision


class PolicyCallbackHandler(BaseCallbackHandler):
    """
    Integrates Clearstone policies into the LangChain execution lifecycle.
    """
    def __init__(self, policy_engine: PolicyEngine):
        self.policy_engine = policy_engine

    def _get_or_raise_context(self) -> PolicyContext:
        context = get_current_context()
        if context is None:
            raise RuntimeError(
                "PolicyCallbackHandler requires an active PolicyContext. "
                "Wrap your LangChain call in a `with context_scope(ctx):` block."
            )
        return context

    def _evaluate_at_decision_point(self, event_metadata: Dict[str, Any]):
        """Helper to enrich context, evaluate policies, and handle the outcome."""
        original_context = self._get_or_raise_context()
        
        enriched_context = dataclasses.replace(
            original_context,
            metadata={**original_context.metadata, **event_metadata}
        )
        
        with context_scope(enriched_context):
            decision = self.policy_engine.evaluate()
        
        self._handle_decision(decision, event_metadata.get("event_type", "unknown"))

    def _handle_decision(self, decision: Decision, decision_point: str):
        """Raises exceptions for terminal decisions like BLOCK and PAUSE."""
        if decision.action == ActionType.BLOCK:
            raise PolicyViolationError(
                f"Policy blocked execution at {decision_point}: {decision.reason}",
                decision
            )
        if decision.action == ActionType.PAUSE:
            raise PolicyPauseError(
                f"Policy paused execution at {decision_point}: {decision.reason}",
                decision
            )

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Decision Point 1: Before an LLM call."""
        event_metadata = {
            "event_type": "on_llm_start",
            "llm_prompts": prompts,
            "llm_serialized": serialized,
        }
        self._evaluate_at_decision_point(event_metadata)

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Decision Point 2: Before a tool is executed."""
        event_metadata = {
            "event_type": "on_tool_start",
            "tool_name": serialized.get("name"),
            "tool_input": input_str,
        }
        self._evaluate_at_decision_point(event_metadata)
