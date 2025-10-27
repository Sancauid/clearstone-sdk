"""
Tests for PolicyMetrics.
"""

import pytest
from clearstone.utils.metrics import PolicyMetrics
from clearstone.core.actions import ALLOW, BLOCK, ALERT


class TestPolicyMetrics:
    """Test suite for PolicyMetrics class."""

    def test_metrics_record(self):
        """Test that metrics are recorded correctly for different decisions."""
        metrics = PolicyMetrics()
        metrics.record("policy_allow", ALLOW, 0.1)
        metrics.record("policy_block", BLOCK("reason"), 0.2)
        metrics.record("policy_block", BLOCK("reason2"), 0.3)
        metrics.record("policy_alert", ALERT, 0.4)

        stats = metrics.stats
        assert stats["policy_allow"]["eval_count"] == 1
        assert stats["policy_block"]["eval_count"] == 2
        assert stats["policy_block"]["block_count"] == 2
        assert stats["policy_alert"]["alert_count"] == 1
        assert stats["policy_block"]["total_latency_ms"] == pytest.approx(0.5)

    def test_metrics_summary_calculates_averages(self):
        """Test that the summary calculates average latency correctly."""
        metrics = PolicyMetrics()
        metrics.record("fast_policy", ALLOW, 0.1)
        metrics.record("fast_policy", ALLOW, 0.3)

        summary = metrics.summary()
        assert summary["fast_policy"]["eval_count"] == 2
        assert summary["fast_policy"]["avg_latency_ms"] == pytest.approx(0.2)

    def test_metrics_get_slowest_policies(self):
        """Test sorting policies by latency."""
        metrics = PolicyMetrics()
        metrics.record("fast", ALLOW, 0.1)
        metrics.record("slow", BLOCK("reason"), 1.5)
        metrics.record("medium", ALERT, 0.5)

        slowest = metrics.get_slowest_policies()
        assert len(slowest) == 3
        assert slowest[0][0] == "slow"
        assert slowest[1][0] == "medium"
        assert slowest[2][0] == "fast"

    def test_metrics_get_top_blocking_policies(self):
        """Test sorting policies by block count."""
        metrics = PolicyMetrics()
        metrics.record("p1_blocks_twice", BLOCK("reason1"), 0.1)
        metrics.record("p1_blocks_twice", BLOCK("reason2"), 0.1)
        metrics.record("p2_blocks_once", BLOCK("reason3"), 0.1)
        metrics.record("p3_never_blocks", ALLOW, 0.1)

        top_blockers = metrics.get_top_blocking_policies()
        assert len(top_blockers) == 3
        assert top_blockers[0][0] == "p1_blocks_twice"
        assert top_blockers[1][0] == "p2_blocks_once"
        assert top_blockers[2][0] == "p3_never_blocks"

    def test_metrics_empty_summary(self):
        """Test that an empty metrics object returns an empty summary."""
        metrics = PolicyMetrics()
        summary = metrics.summary()
        assert summary == {}

    def test_metrics_get_slowest_policies_with_limit(self):
        """Test that get_slowest_policies respects the top_n limit."""
        metrics = PolicyMetrics()
        for i in range(10):
            metrics.record(f"policy_{i}", ALLOW, float(i))

        slowest = metrics.get_slowest_policies(top_n=3)
        assert len(slowest) == 3
        assert slowest[0][0] == "policy_9"
        assert slowest[1][0] == "policy_8"
        assert slowest[2][0] == "policy_7"

    def test_metrics_get_top_blocking_policies_with_limit(self):
        """Test that get_top_blocking_policies respects the top_n limit."""
        metrics = PolicyMetrics()
        for i in range(10):
            decision = BLOCK("reason") if i % 2 == 0 else ALLOW
            for _ in range(i):
                metrics.record(f"policy_{i}", decision, 0.1)

        top_blockers = metrics.get_top_blocking_policies(top_n=2)
        assert len(top_blockers) == 2

    def test_metrics_mixed_decisions_for_single_policy(self):
        """Test that a single policy can have multiple types of decisions tracked."""
        metrics = PolicyMetrics()
        metrics.record("mixed_policy", ALLOW, 0.1)
        metrics.record("mixed_policy", BLOCK("reason"), 0.2)
        metrics.record("mixed_policy", ALERT, 0.3)

        summary = metrics.summary()
        assert summary["mixed_policy"]["eval_count"] == 3
        assert summary["mixed_policy"]["block_count"] == 1
        assert summary["mixed_policy"]["alert_count"] == 1
        assert summary["mixed_policy"]["avg_latency_ms"] == pytest.approx(0.2)

    def test_metrics_zero_latency_handled_correctly(self):
        """Test that zero latency is handled without division errors."""
        metrics = PolicyMetrics()
        metrics.record("instant_policy", ALLOW, 0.0)

        summary = metrics.summary()
        assert summary["instant_policy"]["avg_latency_ms"] == 0.0

