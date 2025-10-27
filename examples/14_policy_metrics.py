"""
Example 14: Policy Metrics and Performance Analysis

This example demonstrates how to use PolicyMetrics to track and analyze
policy performance, identify bottlenecks, and understand decision patterns.
"""

import time

from clearstone import (
    ALERT,
    ALLOW,
    BLOCK,
    Policy,
    PolicyEngine,
    PolicyMetrics,
    context_scope,
    create_context,
)
from clearstone.core.policy import reset_policies


def example_1_basic_metrics():
    """Example: Basic metrics collection."""
    print("\n=== Example 1: Basic metrics collection ===")
    reset_policies()

    @Policy(name="fast_check", priority=100)
    def fast_policy(context):
        return ALLOW

    @Policy(name="slow_check", priority=90)
    def slow_policy(context):
        time.sleep(0.001)  # Simulate slow operation
        if context.metadata.get("amount", 0) > 1000:
            return BLOCK("Amount too high")
        return ALLOW

    @Policy(name="alert_check", priority=80)
    def alert_policy(context):
        if context.metadata.get("amount", 0) > 500:
            return ALERT
        return ALLOW

    metrics = PolicyMetrics()
    engine = PolicyEngine(metrics=metrics)

    # Run several evaluations
    for amount in [100, 600, 1500]:
        ctx = create_context("user1", "agent1", metadata={"amount": amount})
        with context_scope(ctx):
            engine.evaluate()

    # Get summary
    summary = metrics.summary()
    print("\nMetrics Summary:")
    for policy_name, stats in summary.items():
        print(f"  {policy_name}:")
        print(f"    Evaluations: {stats['eval_count']}")
        print(f"    Blocks: {stats['block_count']}")
        print(f"    Alerts: {stats['alert_count']}")
        print(f"    Avg Latency: {stats['avg_latency_ms']:.4f}ms")


def example_2_identify_slow_policies():
    """Example: Finding performance bottlenecks."""
    print("\n=== Example 2: Identify slow policies ===")
    reset_policies()

    @Policy(name="instant_policy", priority=100)
    def instant_policy(context):
        return ALLOW

    @Policy(name="fast_policy", priority=90)
    def fast_policy(context):
        time.sleep(0.0005)
        return ALLOW

    @Policy(name="medium_policy", priority=80)
    def medium_policy(context):
        time.sleep(0.002)
        return ALLOW

    @Policy(name="slow_policy", priority=70)
    def slow_policy(context):
        time.sleep(0.005)
        return ALLOW

    metrics = PolicyMetrics()
    engine = PolicyEngine(metrics=metrics)

    # Run multiple evaluations
    for _ in range(10):
        ctx = create_context("user1", "agent1")
        with context_scope(ctx):
            engine.evaluate()

    # Find slowest policies
    print("\nSlowest Policies (Top 3):")
    slowest = metrics.get_slowest_policies(top_n=3)
    for i, (policy_name, stats) in enumerate(slowest, 1):
        print(f"  {i}. {policy_name}: {stats['avg_latency_ms']:.4f}ms")


def example_3_track_blocking_patterns():
    """Example: Analyzing which policies block most often."""
    print("\n=== Example 3: Track blocking patterns ===")
    reset_policies()

    @Policy(name="amount_limit", priority=100)
    def amount_limit_policy(context):
        if context.metadata.get("amount", 0) > 1000:
            return BLOCK("Amount exceeds limit")
        return ALLOW

    @Policy(name="role_check", priority=90)
    def role_check_policy(context):
        if context.metadata.get("role") == "guest":
            return BLOCK("Guests not allowed")
        return ALLOW

    @Policy(name="time_check", priority=80)
    def time_check_policy(context):
        if context.metadata.get("hour", 12) > 18:
            return BLOCK("After business hours")
        return ALLOW

    metrics = PolicyMetrics()
    engine = PolicyEngine(metrics=metrics)

    # Simulate various scenarios
    scenarios = [
        {"amount": 500, "role": "user", "hour": 14},  # All pass
        {"amount": 1500, "role": "user", "hour": 14},  # Amount blocks
        {"amount": 500, "role": "guest", "hour": 14},  # Role blocks
        {"amount": 500, "role": "user", "hour": 20},  # Time blocks
        {"amount": 1500, "role": "guest", "hour": 20},  # Amount blocks first
    ]

    print("\nRunning scenarios...")
    for i, scenario in enumerate(scenarios, 1):
        ctx = create_context("user1", "agent1", metadata=scenario)
        with context_scope(ctx):
            decision = engine.evaluate()
            status = (
                "✓ ALLOWED"
                if decision.action.value == "allow"
                else f"✗ {decision.action.value.upper()}"
            )
            print(f"  Scenario {i}: {status}")

    # Find top blocking policies
    print("\nTop Blocking Policies:")
    top_blockers = metrics.get_top_blocking_policies()
    for policy_name, stats in top_blockers:
        if stats["block_count"] > 0:
            block_rate = (stats["block_count"] / stats["eval_count"]) * 100
            print(
                f"  {policy_name}: {stats['block_count']}/{stats['eval_count']} ({block_rate:.1f}%)"
            )


def example_4_shared_metrics_across_engines():
    """Example: Using shared metrics across multiple engine instances."""
    print("\n=== Example 4: Shared metrics across engines ===")
    reset_policies()

    @Policy(name="shared_policy", priority=100)
    def shared_policy(context):
        if context.metadata.get("value", 0) > 50:
            return BLOCK("Value too high")
        return ALLOW

    # Create a shared metrics object
    shared_metrics = PolicyMetrics()

    # Create two engines with the same metrics
    engine1 = PolicyEngine(metrics=shared_metrics)
    engine2 = PolicyEngine(metrics=shared_metrics)

    # Use both engines
    for value in [10, 60, 30]:
        ctx1 = create_context("user1", "engine1", metadata={"value": value})
        ctx2 = create_context("user2", "engine2", metadata={"value": value + 5})

        with context_scope(ctx1):
            engine1.evaluate()

        with context_scope(ctx2):
            engine2.evaluate()

    # Get combined metrics
    summary = shared_metrics.summary()
    print("\nShared metrics across both engines:")
    print(f"  Total evaluations: {summary['shared_policy']['eval_count']}")
    print(f"  Total blocks: {summary['shared_policy']['block_count']}")
    print(f"  Avg latency: {summary['shared_policy']['avg_latency_ms']:.4f}ms")


def example_5_real_time_performance_monitoring():
    """Example: Real-time performance monitoring."""
    print("\n=== Example 5: Real-time performance monitoring ===")
    reset_policies()

    @Policy(name="varying_speed_policy", priority=100)
    def varying_speed_policy(context):
        # Simulate varying performance
        delay = context.metadata.get("complexity", 1) * 0.001
        time.sleep(delay)

        if context.metadata.get("value", 0) > 100:
            return BLOCK("Value too high")
        return ALLOW

    metrics = PolicyMetrics()
    engine = PolicyEngine(metrics=metrics)

    print("\nMonitoring performance over time:")
    complexities = [1, 2, 3, 4, 5]

    for complexity in complexities:
        ctx = create_context(
            "user1", "agent1", metadata={"complexity": complexity, "value": 50}
        )
        with context_scope(ctx):
            engine.evaluate()

        # Get current metrics
        current_stats = metrics.summary()["varying_speed_policy"]
        print(
            f"  After {current_stats['eval_count']} evals: "
            f"Avg latency = {current_stats['avg_latency_ms']:.4f}ms"
        )


if __name__ == "__main__":
    print("\nClearstone Policy Metrics Demo")
    print("=" * 60)

    example_1_basic_metrics()
    example_2_identify_slow_policies()
    example_3_track_blocking_patterns()
    example_4_shared_metrics_across_engines()
    example_5_real_time_performance_monitoring()

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("\nKey Takeaways:")
    print("- PolicyMetrics tracks performance and decision patterns")
    print("- Use get_slowest_policies() to find bottlenecks")
    print("- Use get_top_blocking_policies() to analyze blocking behavior")
    print("- Share metrics across engines for unified monitoring")
    print("- Zero-overhead tracking with minimal performance impact")
