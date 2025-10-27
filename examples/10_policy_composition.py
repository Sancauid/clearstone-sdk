"""
Example: Policy Composition with compose_and and compose_or

This example demonstrates how to combine policies using logical operators
to create complex governance rules from simple building blocks.

Note: This example uses fresh policy registries for each demo to avoid
interference from previously registered policies.
"""

from clearstone import (
    create_context,
    compose_and,
    compose_or,
    ALLOW,
    BLOCK
)


def example_1_compose_and():
    """Example: Using compose_and to require ALL conditions."""
    print("\n=== Example 1: compose_and - ALL policies must pass ===")

    def requires_admin(context):
        if context.metadata.get("role") == "admin":
            return ALLOW
        return BLOCK("Admin role required")

    def requires_verified_email(context):
        if context.metadata.get("email_verified"):
            return ALLOW
        return BLOCK("Email verification required")

    strict_policy = compose_and(requires_admin, requires_verified_email)

    ctx_admin_verified = create_context(
        "user1", "agent1",
        role="admin",
        email_verified=True
    )

    ctx_admin_unverified = create_context(
        "user2", "agent1",
        role="admin",
        email_verified=False
    )

    decision1 = strict_policy(ctx_admin_verified)
    print(f"Admin + Verified: {decision1.action.value}")

    decision2 = strict_policy(ctx_admin_unverified)
    print(f"Admin + Unverified: {decision2.action.value} - {decision2.reason}")


def example_2_compose_or():
    """Example: Using compose_or to allow ANY condition."""
    print("\n=== Example 2: compose_or - ANY policy can pass ===")

    def is_admin(context):
        if context.metadata.get("role") == "admin":
            return ALLOW
        return BLOCK("Not admin")

    def is_emergency(context):
        if context.metadata.get("emergency_mode"):
            return ALLOW
        return BLOCK("Not emergency")

    flexible_policy = compose_or(is_admin, is_emergency)

    ctx_regular_user = create_context(
        "user1", "agent1",
        role="user"
    )

    ctx_emergency_user = create_context(
        "user2", "agent1",
        role="user",
        emergency_mode=True
    )

    ctx_admin = create_context(
        "user3", "agent1",
        role="admin"
    )

    decision1 = flexible_policy(ctx_regular_user)
    print(f"Regular User: {decision1.action.value}")

    decision2 = flexible_policy(ctx_emergency_user)
    print(f"Emergency User: {decision2.action.value}")

    decision3 = flexible_policy(ctx_admin)
    print(f"Admin User: {decision3.action.value}")


def example_3_nested_composition():
    """Example: Nesting compositions for complex logic."""
    print("\n=== Example 3: Nested composition - Complex logic ===")

    def requires_admin(context):
        if context.metadata.get("role") == "admin":
            return ALLOW
        return BLOCK("Admin required")

    def requires_business_hours(context):
        hour = context.metadata.get("hour", 12)
        if 9 <= hour < 17:
            return ALLOW
        return BLOCK("Outside business hours")

    def emergency_override(context):
        if context.metadata.get("emergency"):
            return ALLOW
        return BLOCK("Not emergency")

    normal_access = compose_and(requires_admin, requires_business_hours)
    flexible_access = compose_or(normal_access, emergency_override)

    scenarios = [
        ("Admin during business hours", {"role": "admin", "hour": 14}),
        ("Admin after hours", {"role": "admin", "hour": 22}),
        ("Emergency after hours", {"role": "user", "hour": 22, "emergency": True}),
        ("Regular user during hours", {"role": "user", "hour": 14}),
    ]

    for name, metadata in scenarios:
        ctx = create_context("user", "agent", **metadata)
        decision = flexible_access(ctx)
        print(f"{name}: {decision.action.value}")


def example_4_token_limit_composition():
    """Example: Combining token limits with custom logic."""
    print("\n=== Example 4: Token limit with custom permissions ===")

    def check_token_limit(context):
        limit = context.metadata.get("token_limit")
        tokens = context.metadata.get("tokens_used", 0)
        if limit and tokens > limit:
            return BLOCK(f"Token limit exceeded: {tokens} > {limit}")
        return ALLOW

    def requires_special_permission(context):
        if context.metadata.get("special_permission"):
            return ALLOW
        return BLOCK("Special permission required")

    combined = compose_and(check_token_limit, requires_special_permission)

    ctx_pass = create_context(
        "user1", "agent1",
        token_limit=5000,
        tokens_used=3000,
        special_permission=True
    )

    ctx_fail_tokens = create_context(
        "user2", "agent1",
        token_limit=5000,
        tokens_used=6000,
        special_permission=True
    )

    ctx_fail_permission = create_context(
        "user3", "agent1",
        token_limit=5000,
        tokens_used=3000,
        special_permission=False
    )

    scenarios = [
        ("Under token limit + has permission", ctx_pass),
        ("Over token limit + has permission", ctx_fail_tokens),
        ("Under token limit + no permission", ctx_fail_permission),
    ]

    for name, ctx in scenarios:
        decision = combined(ctx)
        result = f"{decision.action.value}"
        if decision.reason:
            result += f" - {decision.reason}"
        print(f"{name}: {result}")


def example_5_multiple_fallback_policies():
    """Example: Multiple fallback options with compose_or."""
    print("\n=== Example 5: Multiple fallback options ===")

    def primary_auth(context):
        if context.metadata.get("primary_auth"):
            return ALLOW
        return BLOCK("Primary auth failed")

    def secondary_auth(context):
        if context.metadata.get("secondary_auth"):
            return ALLOW
        return BLOCK("Secondary auth failed")

    def backup_auth(context):
        if context.metadata.get("backup_auth"):
            return ALLOW
        return BLOCK("Backup auth failed")

    multi_auth = compose_or(primary_auth, secondary_auth, backup_auth)

    test_cases = [
        ("Primary succeeds", {"primary_auth": True}),
        ("Primary fails, secondary succeeds", {"secondary_auth": True}),
        ("Primary & secondary fail, backup succeeds", {"backup_auth": True}),
        ("All fail", {}),
    ]

    for name, metadata in test_cases:
        ctx = create_context("user", "agent", **metadata)
        decision = multi_auth(ctx)
        print(f"{name}: {decision.action.value}")


if __name__ == "__main__":
    print("Clearstone Policy Composition Demo")
    print("=" * 60)

    example_1_compose_and()
    example_2_compose_or()
    example_3_nested_composition()
    example_4_token_limit_composition()
    example_5_multiple_fallback_policies()

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("\nKey Takeaways:")
    print("- compose_and: ALL policies must pass (fail-fast on BLOCK)")
    print("- compose_or: ANY policy can pass (first non-BLOCK wins)")
    print("- Compositions can be nested for complex logic")
    print("- Works seamlessly with pre-built library policies")

