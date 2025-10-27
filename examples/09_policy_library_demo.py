"""
Example: Using the Pre-built Policy Library

This example demonstrates how to use Clearstone's pre-built policy library
for common governance scenarios without writing custom policies.
"""

from clearstone import PolicyEngine, context_scope, create_context
from clearstone.policies import (
    create_cost_control_policies,
    create_security_policies,
)


def example_1_token_limits():
    """Example: Using token limit policy."""
    print("\n=== Example 1: Token Limits ===")

    engine = PolicyEngine()

    ctx = create_context(
        user_id="user_123",
        agent_id="research_agent",
        token_limit=5000,
        tokens_used=6000,
    )

    with context_scope(ctx):
        decision = engine.evaluate()
        print(f"Decision: {decision.action.value}")
        print(f"Reason: {decision.reason}")


def example_2_rbac():
    """Example: Role-based access control."""
    print("\n=== Example 2: RBAC ===")

    engine = PolicyEngine()

    ctx = create_context(
        user_id="guest_user",
        agent_id="admin_agent",
        user_role="guest",
        tool_name="delete_database",
        restricted_tools={
            "guest": ["delete_database", "export_data"],
            "user": ["delete_database"],
            "admin": [],
        },
    )

    with context_scope(ctx):
        decision = engine.evaluate()
        print(f"Decision: {decision.action.value}")
        print(f"Reason: {decision.reason}")


def example_3_dangerous_tools():
    """Example: Blocking dangerous operations."""
    print("\n=== Example 3: Dangerous Tools ===")

    engine = PolicyEngine()

    ctx = create_context(
        user_id="user_123", agent_id="data_agent", tool_name="drop_table"
    )

    with context_scope(ctx):
        decision = engine.evaluate()
        print(f"Decision: {decision.action.value}")
        print(f"Reason: {decision.reason}")


def example_4_pii_redaction():
    """Example: Automatic PII redaction."""
    print("\n=== Example 4: PII Redaction ===")

    engine = PolicyEngine()

    ctx = create_context(
        user_id="analyst_user",
        agent_id="data_agent",
        tool_name="fetch_user_data",
        pii_fields={"fetch_user_data": ["ssn", "credit_card", "email"]},
    )

    with context_scope(ctx):
        decision = engine.evaluate()
        print(f"Decision: {decision.action.value}")
        if decision.metadata.get("fields_to_redact"):
            print(f"Fields to redact: {decision.metadata['fields_to_redact']}")


def example_5_policy_factories():
    """Example: Using policy factories for common scenarios."""
    print("\n=== Example 5: Policy Factories (Cost Control) ===")

    policies = create_cost_control_policies()
    print(f"Created {len(policies)} cost control policies:")
    for policy in policies:
        print(f"  - {policy.__name__}")

    print("\n=== Example 5b: Policy Factories (Security) ===")
    policies = create_security_policies()
    print(f"Created {len(policies)} security policies:")
    for policy in policies:
        print(f"  - {policy.__name__}")


def example_6_combined_policies():
    """Example: Multiple policies working together."""
    print("\n=== Example 6: Combined Policies ===")

    engine = PolicyEngine()

    ctx = create_context(
        user_id="regular_user",
        agent_id="financial_agent",
        user_role="user",
        tool_name="export_sensitive_data",
        token_limit=5000,
        tokens_used=3000,
        daily_cost_limit=1000.0,
        daily_cost=500.0,
        pii_fields={"export_sensitive_data": ["ssn", "account_number"]},
    )

    with context_scope(ctx):
        decision = engine.evaluate()
        print(f"Decision: {decision.action.value}")
        if decision.action.value == "redact":
            print(f"Fields to redact: {decision.metadata.get('fields_to_redact')}")


if __name__ == "__main__":
    print("Clearstone Policy Library Demo")
    print("=" * 60)

    example_1_token_limits()
    example_2_rbac()
    example_3_dangerous_tools()
    example_4_pii_redaction()
    example_5_policy_factories()
    example_6_combined_policies()

    print("\n" + "=" * 60)
    print("Demo complete!")
