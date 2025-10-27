# clearstone/core/context.py

import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from contextlib import contextmanager

@dataclass(frozen=True)
class PolicyContext:
    """
    Immutable execution context for a policy evaluation. It is propagated via
    contextvars, making it safe for threaded and asynchronous environments.
    """
    user_id: str
    agent_id: str
    session_id: str
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def current(cls) -> Optional['PolicyContext']:
        """Retrieves the current context from the context variable."""
        return _policy_context.get()

_policy_context: ContextVar[Optional[PolicyContext]] = ContextVar('policy_context', default=None)

def get_current_context() -> Optional[PolicyContext]:
    """
    Retrieves the current policy context from the active scope.
    Returns None if no context has been set.
    """
    return _policy_context.get()

def set_current_context(context: PolicyContext) -> None:
    """
    Manually sets the current policy context for the active scope.
    It is often safer to use the `context_scope` context manager.
    """
    _policy_context.set(context)

@contextmanager
def context_scope(context: PolicyContext):
    """
    A context manager for safely setting and automatically resetting the policy context.

    Usage:
        ctx = create_context(...)
        with context_scope(ctx):
            decision = policy_engine.evaluate()
    """
    token = _policy_context.set(context)
    try:
        yield context
    finally:
        _policy_context.reset(token)

def create_context(
    user_id: str,
    agent_id: str,
    session_id: Optional[str] = None,
    **metadata
) -> PolicyContext:
    """
    Factory function for conveniently creating a new PolicyContext instance.
    """
    if not user_id or not agent_id:
        raise ValueError("user_id and agent_id must be provided.")
    return PolicyContext(
        user_id=user_id,
        agent_id=agent_id,
        session_id=session_id or str(uuid.uuid4()),
        metadata=metadata
    )
