# clearstone/core/policy.py

import inspect
import time
from dataclasses import dataclass
from typing import Callable, List, Optional

from clearstone.core.actions import ALLOW, BLOCK, ActionType, Decision
from clearstone.core.context import PolicyContext, get_current_context
from clearstone.utils.audit import AuditTrail
from clearstone.utils.metrics import PolicyMetrics
from clearstone.utils.telemetry import get_telemetry_manager

_policy_registry: List["PolicyInfo"] = []


@dataclass(frozen=True)
class PolicyInfo:
    """Metadata about a registered policy function."""

    name: str
    priority: int
    func: Callable


def Policy(name: str, priority: int = 0) -> Callable:
    """
    Decorator to register a function as a Clearstone policy.

    Args:
        name: A unique, human-readable identifier for the policy.
        priority: An integer determining execution order. Higher numbers run first.

    Example:
        @Policy(name="block_admin_tools_for_guests", priority=100)
        def my_policy(context: PolicyContext) -> Decision:
            if context.metadata.get("role") == "guest":
                return BLOCK("Guests cannot access admin tools.")
            return ALLOW
    """
    if not name or not isinstance(name, str):
        raise ValueError("Policy name must be a non-empty string.")

    def decorator(func: Callable) -> Callable:
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        if len(params) != 1 or params[0] != "context":
            raise TypeError(
                f"Policy function '{func.__name__}' must have the signature: "
                f"def {func.__name__}(context: PolicyContext) -> Decision. Got: {sig}"
            )

        info = PolicyInfo(name=name, priority=priority, func=func)

        func._policy_info = info

        _policy_registry.append(info)
        return func

    return decorator


def get_policies() -> List[PolicyInfo]:
    """Returns all registered policies, sorted by priority (descending)."""
    return sorted(_policy_registry, key=lambda p: p.priority, reverse=True)


def reset_policies() -> None:
    """Clears the global policy registry. Primarily for testing."""
    global _policy_registry
    _policy_registry = []


class PolicyEngine:
    """
    The central engine that evaluates registered policies against a given context.

    Args:
        policies: An optional list of decorated policy functions to use.
                  If provided, this exact list will be used, and auto-discovery
                  of other policies will be skipped. If None (default), the engine
                  will auto-discover all imported @Policy-decorated functions.
        audit_trail: Optional AuditTrail instance. If None, creates a new one.
        metrics: Optional PolicyMetrics instance. If None, creates a new one.
    """

    def __init__(
        self,
        policies: Optional[List[Callable]] = None,
        audit_trail: Optional[AuditTrail] = None,
        metrics: Optional[PolicyMetrics] = None,
    ):
        self._policies: List[PolicyInfo] = []
        self.audit_trail = audit_trail or AuditTrail()
        self.metrics = metrics or PolicyMetrics()

        if policies is not None:
            # --- Explicit Configuration Path ---
            # If a list is provided, register ONLY those policies.
            # We filter out any non-callable items for safety.
            valid_policies = [p for p in policies if callable(p)]
            self._register_policies(valid_policies)
        else:
            # --- Auto-Discovery Path (Backward-Compatible) ---
            # Otherwise, fall back to the original auto-discovery logic.
            self._discover_policies()

        if not self._policies:
            # This check is now universal for both paths.
            raise ValueError(
                "PolicyEngine initialized with no valid policies. "
                "Either provide a list of policy functions or ensure @Policy-decorated "
                "functions are imported."
            )

        # Record a telemetry event for initialization
        get_telemetry_manager().record_event(
            "component_initialized", {"name": "PolicyEngine"}
        )

    def _register_policies(self, policy_funcs: List[Callable]):
        """
        Processes a list of decorated functions and adds them to the engine's active set,
        sorted by priority.
        """
        # This logic re-uses the metadata attached by the @Policy decorator.
        # It ensures that even explicitly passed policies are handled correctly.
        policy_infos = []
        for func in policy_funcs:
            if hasattr(func, "_policy_info"):
                policy_infos.append(func._policy_info)
            else:
                # Handle the case where a non-decorated function is passed.
                # We can either raise an error or assign default metadata.
                # Assigning defaults is more user-friendly.
                name = getattr(func, "__name__", "anonymous_policy")
                policy_infos.append(PolicyInfo(name=name, priority=0, func=func))

        self._policies = sorted(policy_infos, key=lambda p: p.priority, reverse=True)

    def _discover_policies(self):
        """Auto-discovers all imported @Policy-decorated functions from the global registry."""
        self._policies = sorted(get_policies(), key=lambda p: p.priority, reverse=True)

    def evaluate(self, context: Optional[PolicyContext] = None) -> Decision:
        """
        Evaluates an action against all registered policies using a composable veto model.

        Args:
            context: The PolicyContext for the evaluation. If None, it's retrieved
                     from the active context variable scope.
        """
        if context is None:
            context = get_current_context()
        if context is None:
            raise RuntimeError(
                "Cannot evaluate policies: No PolicyContext is active. "
                "Use `with context_scope(ctx):` before calling evaluate."
            )

        final_decision = ALLOW

        for policy_info in self._policies:
            start_time = time.perf_counter()

            try:
                decision = policy_info.func(context)
                end_time = time.perf_counter()
                latency_ms = (end_time - start_time) * 1000

                self.metrics.record(policy_info.name, decision, latency_ms)
                self.audit_trail.record_decision(policy_info.name, context, decision)

                if decision.action == ActionType.BLOCK:
                    return decision

                if (
                    final_decision.action == ActionType.ALLOW
                    and decision.action not in [ActionType.ALLOW, ActionType.SKIP]
                ):
                    final_decision = decision

            except Exception as e:
                end_time = time.perf_counter()
                latency_ms = (end_time - start_time) * 1000

                err_reason = f"Policy '{policy_info.name}' raised an exception: {e}"
                err_decision = BLOCK(err_reason)

                self.metrics.record(policy_info.name, err_decision, latency_ms)
                self.audit_trail.record_decision(
                    policy_info.name, context, err_decision, error=str(e)
                )
                return err_decision

        return final_decision

    def get_audit_trail(self, limit: int = 100):
        """Returns the most recent audit trail entries."""
        return self.audit_trail.get_entries(limit=limit)
