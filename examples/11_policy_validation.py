"""
Example: Policy Validation for Pre-Deployment Checks

This example demonstrates how to use PolicyValidator to ensure policies are
safe, performant, and deterministic before deploying them to production.
"""

import random
import time

from clearstone import (
    ALLOW,
    BLOCK,
    PolicyValidationError,
    PolicyValidator,
    create_context,
)


def example_1_good_policy():
    """Example: A well-behaved policy passes all checks."""
    print("\n=== Example 1: Validating a good policy ===")

    def good_policy(context):
        """A safe, fast, and deterministic policy."""
        if context.metadata.get("role") == "admin":
            return BLOCK("Admin access blocked")
        return ALLOW

    validator = PolicyValidator()
    failures = validator.run_all_checks(good_policy)

    if not failures:
        print("✓ All validation checks passed!")
    else:
        print("✗ Validation failures:")
        for failure in failures:
            print(f"  - {failure}")


def example_2_non_deterministic_policy():
    """Example: Catching non-deterministic policies."""
    print("\n=== Example 2: Non-deterministic policy (uses random) ===")

    def bad_policy(context):
        """This policy will fail determinism checks."""
        if random.random() > 0.5:
            return BLOCK("Randomly blocked")
        return ALLOW

    validator = PolicyValidator()

    try:
        validator.validate_determinism(bad_policy)
        print("✓ Determinism check passed")
    except PolicyValidationError as e:
        print(f"✗ Determinism check failed: {e}")


def example_3_slow_policy():
    """Example: Catching slow policies."""
    print("\n=== Example 3: Slow policy (network call simulation) ===")

    def slow_policy(context):
        """This policy will fail performance checks."""
        time.sleep(0.002)
        return ALLOW

    validator = PolicyValidator()

    try:
        validator.validate_performance(slow_policy, max_latency_ms=1.0)
        print("✓ Performance check passed")
    except PolicyValidationError as e:
        print(f"✗ Performance check failed: {e}")


def example_4_fragile_policy():
    """Example: Catching fragile policies that crash on missing metadata."""
    print("\n=== Example 4: Fragile policy (crashes on missing data) ===")

    def fragile_policy(context):
        """This policy will fail exception safety checks."""
        if context.metadata["role"] == "admin":
            return BLOCK("Admin blocked")
        return ALLOW

    validator = PolicyValidator()

    try:
        validator.validate_exception_safety(fragile_policy)
        print("✓ Exception safety check passed")
    except PolicyValidationError as e:
        print(f"✗ Exception safety check failed: {e}")


def example_5_run_all_checks():
    """Example: Running all checks at once."""
    print("\n=== Example 5: Running all checks on multiple policies ===")

    def good_policy(context):
        return ALLOW

    def bad_policy_1(context):
        if random.random() > 0.5:
            return BLOCK("Random")
        return ALLOW

    def bad_policy_2(context):
        time.sleep(0.003)
        return ALLOW

    policies = [
        ("good_policy", good_policy),
        ("non_deterministic_policy", bad_policy_1),
        ("slow_policy", bad_policy_2),
    ]

    validator = PolicyValidator()

    for name, policy in policies:
        failures = validator.run_all_checks(policy)
        if not failures:
            print(f"✓ {name}: All checks passed")
        else:
            print(f"✗ {name}: {len(failures)} failure(s)")
            for failure in failures:
                print(f"    - {failure}")


def example_6_custom_validation_context():
    """Example: Using a custom context for validation."""
    print("\n=== Example 6: Custom validation context ===")

    def role_based_policy(context):
        """Policy that requires specific metadata."""
        role = context.metadata.get("role", "guest")
        if role == "admin":
            return BLOCK("Admin blocked")
        return ALLOW

    custom_context = create_context("test_user", "test_agent", role="admin")

    validator = PolicyValidator(default_context=custom_context)
    failures = validator.run_all_checks(role_based_policy)

    if not failures:
        print("✓ Policy validated with custom context")
    else:
        print(f"✗ {len(failures)} failure(s) with custom context")


def example_7_production_deployment_workflow():
    """Example: Production deployment workflow."""
    print("\n=== Example 7: Production deployment workflow ===")

    def deploy_policy(policy_func):
        """Simulate deploying a policy after validation."""
        validator = PolicyValidator()
        failures = validator.run_all_checks(policy_func)

        if not failures:
            print(f"✓ Deploying {policy_func.__name__} to production...")
            return True
        else:
            print(f"✗ Deployment blocked for {policy_func.__name__}:")
            for failure in failures:
                print(f"    - {failure}")
            return False

    def safe_policy(context):
        return ALLOW

    def unsafe_policy(context):
        if random.random() > 0.5:
            return BLOCK("Random")
        return ALLOW

    deploy_policy(safe_policy)
    deploy_policy(unsafe_policy)


if __name__ == "__main__":
    print("Clearstone Policy Validation Demo")
    print("=" * 60)

    example_1_good_policy()
    example_2_non_deterministic_policy()
    example_3_slow_policy()
    example_4_fragile_policy()
    example_5_run_all_checks()
    example_6_custom_validation_context()
    example_7_production_deployment_workflow()

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("\nKey Takeaways:")
    print("- Validate determinism: Policies should return same output for same input")
    print("- Validate performance: Policies should execute within time budgets")
    print(
        "- Validate exception safety: Policies should handle missing metadata gracefully"
    )
    print("- Use run_all_checks() for comprehensive pre-deployment validation")
