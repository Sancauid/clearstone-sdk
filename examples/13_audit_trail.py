"""
Example: Audit Trail for Policy Decisions

This example demonstrates how to use AuditTrail to capture, analyze,
and export policy evaluation history.
"""

from clearstone import (
    Policy,
    PolicyEngine,
    AuditTrail,
    create_context,
    context_scope,
    ALLOW,
    BLOCK
)
from clearstone.core.policy import reset_policies


def example_1_basic_audit():
    """Example: Basic audit trail usage."""
    print("\n=== Example 1: Basic audit trail ===")

    reset_policies()

    @Policy(name="token_check", priority=100)
    def token_check(context):
        tokens = context.metadata.get("tokens", 0)
        if tokens > 5000:
            return BLOCK(f"Token limit exceeded: {tokens}")
        return ALLOW

    @Policy(name="role_check", priority=90)
    def role_check(context):
        role = context.metadata.get("role", "guest")
        if role == "guest":
            return BLOCK("Guest access not allowed")
        return ALLOW

    audit = AuditTrail()
    engine = PolicyEngine(audit_trail=audit)

    contexts = [
        create_context("user1", "agent1", tokens=3000, role="user"),
        create_context("user2", "agent1", tokens=6000, role="user"),
        create_context("user3", "agent1", tokens=2000, role="guest"),
    ]

    for ctx in contexts:
        with context_scope(ctx):
            decision = engine.evaluate()
            print(f"User {ctx.user_id}: {decision.action.value}")

    print(f"\nTotal decisions recorded: {len(audit.get_entries())}")


def example_2_audit_summary():
    """Example: Analyzing audit trail with summary statistics."""
    print("\n=== Example 2: Audit summary statistics ===")

    reset_policies()

    @Policy(name="amount_check", priority=100)
    def amount_check(context):
        amount = context.metadata.get("amount", 0)
        if amount > 1000:
            return BLOCK(f"Amount {amount} exceeds limit")
        return ALLOW

    audit = AuditTrail()
    engine = PolicyEngine(audit_trail=audit)

    test_amounts = [500, 1500, 300, 2000, 800, 1200, 400]

    print("Processing transactions...")
    for i, amount in enumerate(test_amounts, 1):
        ctx = create_context(f"user{i}", "agent1", amount=amount)
        with context_scope(ctx):
            decision = engine.evaluate()
            status = "✓" if decision.action.value == "allow" else "✗"
            print(f"  {status} Transaction {i}: ${amount} - {decision.action.value}")

    summary = audit.summary()
    print(f"\nSummary:")
    print(f"  Total decisions: {summary['total_decisions']}")
    print(f"  Blocks: {summary['blocks']}")
    print(f"  Block rate: {summary['block_rate']:.1%}")


def example_3_export_to_json():
    """Example: Exporting audit trail to JSON."""
    print("\n=== Example 3: Export to JSON ===")

    reset_policies()

    @Policy(name="access_control", priority=100)
    def access_control(context):
        role = context.metadata.get("role", "guest")
        resource = context.metadata.get("resource", "")

        if role == "admin":
            return ALLOW

        if resource in ["admin_panel", "settings"]:
            return BLOCK(f"{role} cannot access {resource}")

        return ALLOW

    audit = AuditTrail()
    engine = PolicyEngine(audit_trail=audit)

    test_cases = [
        {"role": "user", "resource": "dashboard"},
        {"role": "user", "resource": "admin_panel"},
        {"role": "admin", "resource": "admin_panel"},
        {"role": "guest", "resource": "settings"},
    ]

    for i, metadata in enumerate(test_cases, 1):
        ctx = create_context(f"user{i}", "agent1", **metadata)
        with context_scope(ctx):
            engine.evaluate()

    audit.to_json("/tmp/audit_log.json")
    print("✓ Exported audit trail to /tmp/audit_log.json")
    print(f"  Recorded {len(audit.get_entries())} decisions")


def example_4_export_to_csv():
    """Example: Exporting audit trail to CSV."""
    print("\n=== Example 4: Export to CSV ===")

    reset_policies()

    @Policy(name="rate_limit", priority=100)
    def rate_limit(context):
        rate_count = context.metadata.get("rate_count", 0)
        if rate_count > 100:
            return BLOCK(f"Rate limit exceeded: {rate_count}/100")
        return ALLOW

    audit = AuditTrail()
    engine = PolicyEngine(audit_trail=audit)

    rate_counts = [50, 120, 80, 150, 30, 110]

    for i, count in enumerate(rate_counts, 1):
        ctx = create_context(f"user{i}", "agent1", rate_count=count)
        with context_scope(ctx):
            engine.evaluate()

    audit.to_csv("/tmp/audit_log.csv")
    print("✓ Exported audit trail to /tmp/audit_log.csv")
    print(f"  Recorded {len(audit.get_entries())} decisions")


def example_5_shared_audit_trail():
    """Example: Sharing audit trail across multiple engines."""
    print("\n=== Example 5: Shared audit trail ===")

    reset_policies()

    @Policy(name="auth_policy", priority=100)
    def auth_policy(context):
        authenticated = context.metadata.get("authenticated", False)
        if not authenticated:
            return BLOCK("Not authenticated")
        return ALLOW

    @Policy(name="permission_policy", priority=90)
    def permission_policy(context):
        has_permission = context.metadata.get("has_permission", False)
        if not has_permission:
            return BLOCK("No permission")
        return ALLOW

    shared_audit = AuditTrail()

    auth_engine = PolicyEngine(audit_trail=shared_audit)

    print("Testing authentication & permissions...")
    test_cases = [
        {"authenticated": True, "has_permission": True},
        {"authenticated": False, "has_permission": True},
        {"authenticated": True, "has_permission": False},
    ]

    for i, metadata in enumerate(test_cases, 1):
        ctx = create_context(f"user{i}", "agent1", **metadata)
        with context_scope(ctx):
            decision = auth_engine.evaluate()
            print(f"  User {i}: {decision.action.value}")

    print(f"\nShared audit trail captured: {len(shared_audit.get_entries())} entries")
    summary = shared_audit.summary()
    print(f"Block rate: {summary['block_rate']:.1%}")


def example_6_audit_analysis():
    """Example: Analyzing audit trail entries."""
    print("\n=== Example 6: Audit trail analysis ===")

    reset_policies()

    @Policy(name="multi_check", priority=100)
    def multi_check(context):
        role = context.metadata.get("role", "guest")
        amount = context.metadata.get("amount", 0)

        if role == "guest":
            return BLOCK("Guest access denied")

        if amount > 1000:
            return BLOCK(f"Amount {amount} exceeds limit")

        return ALLOW

    audit = AuditTrail()
    engine = PolicyEngine(audit_trail=audit)

    test_data = [
        {"role": "user", "amount": 500},
        {"role": "guest", "amount": 200},
        {"role": "user", "amount": 1500},
        {"role": "admin", "amount": 5000},
    ]

    for i, metadata in enumerate(test_data, 1):
        ctx = create_context(f"user{i}", "agent1", **metadata)
        with context_scope(ctx):
            engine.evaluate()

    entries = audit.get_entries()
    print("Analyzing audit entries...")

    blocked_by_role = sum(1 for e in entries if "Guest access" in (e["reason"] or ""))
    blocked_by_amount = sum(1 for e in entries if "exceeds limit" in (e["reason"] or ""))

    print(f"  Total decisions: {len(entries)}")
    print(f"  Blocked by role: {blocked_by_role}")
    print(f"  Blocked by amount: {blocked_by_amount}")

    print("\nLast 3 decisions:")
    for entry in audit.get_entries(limit=3):
        print(f"  - {entry['policy_name']}: {entry['decision']} ({entry['reason'] or 'N/A'})")


if __name__ == "__main__":
    print("Clearstone Audit Trail Demo")
    print("=" * 60)

    example_1_basic_audit()
    example_2_audit_summary()
    example_3_export_to_json()
    example_4_export_to_csv()
    example_5_shared_audit_trail()
    example_6_audit_analysis()

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("\nKey Takeaways:")
    print("- AuditTrail captures all policy decisions automatically")
    print("- Use summary() for quick statistics (block rate, alerts, etc)")
    print("- Export to JSON or CSV for analysis and compliance")
    print("- Share audit trails across multiple engines")
    print("- Analyze entries to understand policy behavior")

