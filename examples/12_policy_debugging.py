"""
Example: Policy Debugging with PolicyDebugger

This example demonstrates how to use PolicyDebugger to trace policy execution
and understand the decision-making process line by line.
"""

from clearstone import ALLOW, BLOCK, PolicyDebugger, create_context


def example_1_simple_trace():
    """Example: Basic policy trace."""
    print("\n=== Example 1: Simple policy trace ===")

    def simple_policy(context):
        """A simple policy for demonstration."""
        role = context.metadata.get("role", "guest")
        if role == "admin":
            return ALLOW
        return BLOCK("Non-admin access denied")

    debugger = PolicyDebugger()
    ctx = create_context("user1", "agent1", role="user")

    decision, trace = debugger.trace_evaluation(simple_policy, ctx)

    print(f"Decision: {decision.action.value}")
    print(f"Reason: {decision.reason}")
    print(f"\nTrace captured {len(trace)} execution steps:")
    for event in trace:
        print(f"  Line {event['line_no']}: {event['line_text']}")


def example_2_complex_branching():
    """Example: Tracing complex branching logic."""
    print("\n=== Example 2: Complex branching logic ===")

    def complex_policy(context):
        """Policy with multiple branches."""
        role = context.metadata.get("role", "guest")
        amount = context.metadata.get("amount", 0)
        verified = context.metadata.get("verified", False)

        if role == "admin":
            return ALLOW

        if not verified:
            return BLOCK("User not verified")

        if amount > 1000:
            return BLOCK(f"Amount {amount} exceeds limit for non-admin")

        return ALLOW

    debugger = PolicyDebugger()

    scenarios = [
        ("Admin user", {"role": "admin", "amount": 5000}),
        ("Unverified user", {"role": "user", "amount": 500, "verified": False}),
        (
            "Verified user over limit",
            {"role": "user", "amount": 2000, "verified": True},
        ),
        (
            "Verified user under limit",
            {"role": "user", "amount": 500, "verified": True},
        ),
    ]

    for name, metadata in scenarios:
        ctx = create_context("user", "agent", **metadata)
        decision, trace = debugger.trace_evaluation(complex_policy, ctx)
        print(f"\n{name}: {decision.action.value}")
        if decision.reason:
            print(f"  Reason: {decision.reason}")
        print(f"  Execution path: {len(trace)} lines")


def example_3_formatted_trace():
    """Example: Using formatted trace output."""
    print("\n=== Example 3: Formatted trace output ===")

    def rate_limit_policy(context):
        """Check rate limiting."""
        rate_count = context.metadata.get("rate_count", 0)
        rate_limit = context.metadata.get("rate_limit", 100)

        if rate_count > rate_limit:
            return BLOCK(f"Rate limit exceeded: {rate_count}/{rate_limit}")

        return ALLOW

    debugger = PolicyDebugger()
    ctx = create_context("user1", "agent1", rate_count=150, rate_limit=100)

    decision, trace = debugger.trace_evaluation(rate_limit_policy, ctx)
    formatted = debugger.format_trace(rate_limit_policy, decision, trace)

    print(formatted)


def example_4_debugging_workflow():
    """Example: Using debugger in a development workflow."""
    print("\n=== Example 4: Debugging workflow ===")

    def buggy_policy(context):
        """A policy that might have issues."""
        user_type = context.metadata.get("user_type", "standard")
        credits = context.metadata.get("credits", 0)

        if user_type == "premium":
            return ALLOW

        if credits < 10:
            return BLOCK("Insufficient credits")

        return ALLOW

    debugger = PolicyDebugger()

    print("Testing policy with different inputs...")

    test_cases = [
        {"user_type": "premium", "credits": 0},
        {"user_type": "standard", "credits": 5},
        {"user_type": "standard", "credits": 20},
    ]

    for i, metadata in enumerate(test_cases, 1):
        ctx = create_context("user", "agent", **metadata)
        decision, trace = debugger.trace_evaluation(buggy_policy, ctx)

        print(f"\nTest case {i}: {metadata}")
        print(f"  Result: {decision.action.value}")
        if decision.reason:
            print(f"  Reason: {decision.reason}")

        print("  Execution path:")
        for event in trace:
            locals_str = ", ".join([f"{k}={v}" for k, v in event["locals"].items()])
            print(f"    L{event['line_no']}: {event['line_text']}")
            if locals_str:
                print(f"        ({locals_str})")


def example_5_comparing_paths():
    """Example: Comparing execution paths for different decisions."""
    print("\n=== Example 5: Comparing execution paths ===")

    def access_control_policy(context):
        """Multi-factor access control."""
        role = context.metadata.get("role", "guest")
        mfa_enabled = context.metadata.get("mfa_enabled", False)
        ip_whitelisted = context.metadata.get("ip_whitelisted", False)

        if role == "guest":
            return BLOCK("Guest access not allowed")

        if role == "admin":
            if not mfa_enabled:
                return BLOCK("Admin requires MFA")
            return ALLOW

        if not ip_whitelisted:
            return BLOCK("IP not whitelisted for standard users")

        return ALLOW

    debugger = PolicyDebugger()

    ctx_guest = create_context("user", "agent", role="guest")
    ctx_admin_no_mfa = create_context("user", "agent", role="admin", mfa_enabled=False)
    ctx_admin_with_mfa = create_context("user", "agent", role="admin", mfa_enabled=True)

    print("\nGuest user:")
    decision1, trace1 = debugger.trace_evaluation(access_control_policy, ctx_guest)
    print(f"  Decision: {decision1.action.value} - {decision1.reason}")
    print(f"  Lines executed: {[e['line_no'] for e in trace1]}")

    print("\nAdmin without MFA:")
    decision2, trace2 = debugger.trace_evaluation(
        access_control_policy, ctx_admin_no_mfa
    )
    print(f"  Decision: {decision2.action.value} - {decision2.reason}")
    print(f"  Lines executed: {[e['line_no'] for e in trace2]}")

    print("\nAdmin with MFA:")
    decision3, trace3 = debugger.trace_evaluation(
        access_control_policy, ctx_admin_with_mfa
    )
    print(f"  Decision: {decision3.action.value}")
    print(f"  Lines executed: {[e['line_no'] for e in trace3]}")


if __name__ == "__main__":
    print("Clearstone Policy Debugging Demo")
    print("=" * 60)

    example_1_simple_trace()
    example_2_complex_branching()
    example_3_formatted_trace()
    example_4_debugging_workflow()
    example_5_comparing_paths()

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("\nKey Takeaways:")
    print("- PolicyDebugger traces line-by-line execution of policies")
    print("- Captures local variables at each step")
    print("- Helps understand decision-making logic")
    print("- Perfect for debugging complex branching policies")
    print("- Use format_trace() for human-readable output")
