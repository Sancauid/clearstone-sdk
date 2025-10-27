"""
Policy composition utilities for combining multiple policies with logical operators.
"""

from typing import Callable
from clearstone.core.policy import Policy
from clearstone.core.actions import ALLOW, BLOCK, ActionType, Decision
from clearstone.core.context import PolicyContext


def compose_and(*policies: Callable[[PolicyContext], Decision]) -> Callable[[PolicyContext], Decision]:
    """
    Creates a new composite policy where ALL underlying policies must ALLOW an action.
    
    This is a fail-safe composition. The moment any policy returns a BLOCK, the
    entire composition immediately returns that BLOCK decision and stops further evaluation.

    Args:
        *policies: A sequence of policy functions to compose.

    Returns:
        A new policy function that can be used by the PolicyEngine.

    Example:
        combined = compose_and(token_limit_policy, rbac_policy, business_hours_policy)
        
        @Policy(name="combined_policy", priority=100)
        def my_policy(context):
            return combined(context)
    """
    policy_names = "_and_".join(p.__name__ for p in policies)

    def composed_and_policy(context: PolicyContext) -> Decision:
        for policy in policies:
            decision = policy(context)
            if decision.action == ActionType.BLOCK:
                return decision
        return ALLOW
    
    composed_and_policy.__name__ = f"composed_and({policy_names})"
    return composed_and_policy


def compose_or(*policies: Callable[[PolicyContext], Decision]) -> Callable[[PolicyContext], Decision]:
    """
    Creates a new composite policy where ANY of the underlying policies can ALLOW an action.
    
    This composition returns the decision of the first policy that does not BLOCK.
    If all policies return BLOCK, it returns the decision of the first policy.

    Args:
        *policies: A sequence of policy functions to compose.

    Returns:
        A new policy function.

    Example:
        either = compose_or(admin_access_policy, emergency_override_policy)
        
        @Policy(name="flexible_access", priority=90)
        def my_policy(context):
            return either(context)
    """
    policy_names = "_or_".join(p.__name__ for p in policies)

    def composed_or_policy(context: PolicyContext) -> Decision:
        if not policies:
            return BLOCK("compose_or evaluated with no policies, blocking by default.")

        block_decisions = []
        for policy in policies:
            decision = policy(context)
            if decision.action != ActionType.BLOCK:
                return decision
            block_decisions.append(decision)
        
        return block_decisions[0]
    
    composed_or_policy.__name__ = f"composed_or({policy_names})"
    return composed_or_policy

