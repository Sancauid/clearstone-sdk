"""
Tests for policy composition utilities.
"""

import pytest
from clearstone.utils.composition import compose_and, compose_or
from clearstone.core.actions import ALLOW, BLOCK, ALERT, PAUSE, ActionType
from clearstone.core.context import create_context


def policy_allow(context):
    return ALLOW


def policy_block(context):
    return BLOCK("Blocked by test policy")


def policy_alert(context):
    return ALERT


def policy_pause(context):
    return PAUSE


class TestComposeAnd:
    """Test suite for compose_and composition."""

    def test_compose_and_all_allow(self):
        """If all policies allow, the result should be ALLOW."""
        composed = compose_and(policy_allow, policy_allow, policy_allow)
        ctx = create_context("user", "agent")
        decision = composed(ctx)
        assert decision.action == ActionType.ALLOW

    def test_compose_and_one_blocks(self):
        """If any policy blocks, the result should be that BLOCK decision."""
        composed = compose_and(policy_allow, policy_block, policy_allow)
        ctx = create_context("user", "agent")
        decision = composed(ctx)
        assert decision.action == ActionType.BLOCK
        assert decision.reason == "Blocked by test policy"

    def test_compose_and_first_blocks(self):
        """compose_and should short-circuit and not run subsequent policies."""
        call_log = []

        def logging_policy_allow(context):
            call_log.append("allow")
            return ALLOW

        def logging_policy_block(context):
            call_log.append("block")
            return BLOCK("Blocked")

        composed = compose_and(logging_policy_block, logging_policy_allow)
        composed(create_context("user", "agent"))
        assert call_log == ["block"], "Should not have called the second policy."

    def test_compose_and_with_no_policies(self):
        """Composing no policies with AND should result in ALLOW."""
        composed = compose_and()
        decision = composed(create_context("user", "agent"))
        assert decision.action == ActionType.ALLOW

    def test_compose_and_preserves_block_reason(self):
        """The BLOCK reason from the blocking policy should be preserved."""

        def custom_block(context):
            return BLOCK("Custom block reason")

        composed = compose_and(policy_allow, custom_block)
        ctx = create_context("user", "agent")
        decision = composed(ctx)
        assert decision.action == ActionType.BLOCK
        assert decision.reason == "Custom block reason"

    def test_compose_and_with_non_allow_non_block(self):
        """If a non-ALLOW, non-BLOCK decision is encountered, it should be ignored in AND logic."""
        composed = compose_and(policy_allow, policy_alert, policy_allow)
        ctx = create_context("user", "agent")
        decision = composed(ctx)
        assert decision.action == ActionType.ALLOW


class TestComposeOr:
    """Test suite for compose_or composition."""

    def test_compose_or_first_allows(self):
        """If the first policy allows, the result should be ALLOW."""
        composed = compose_or(policy_allow, policy_block)
        ctx = create_context("user", "agent")
        decision = composed(ctx)
        assert decision.action == ActionType.ALLOW

    def test_compose_or_second_allows(self):
        """The result should be the first non-blocking decision."""
        composed = compose_or(policy_block, policy_alert, policy_allow)
        ctx = create_context("user", "agent")
        decision = composed(ctx)
        assert decision.action == ActionType.ALERT

    def test_compose_or_all_block(self):
        """If all policies block, the result should be the first BLOCK decision."""
        composed = compose_or(policy_block, policy_block)
        ctx = create_context("user", "agent")
        decision = composed(ctx)
        assert decision.action == ActionType.BLOCK
        assert decision.reason == "Blocked by test policy"

    def test_compose_or_with_no_policies(self):
        """Composing no policies with OR should result in a fail-safe BLOCK."""
        composed = compose_or()
        decision = composed(create_context("user", "agent"))
        assert decision.action == ActionType.BLOCK

    def test_compose_or_short_circuits(self):
        """compose_or should stop at the first non-BLOCK decision."""
        call_log = []

        def logging_policy_allow(context):
            call_log.append("allow")
            return ALLOW

        def logging_policy_block(context):
            call_log.append("block")
            return BLOCK("Blocked")

        def logging_policy_alert(context):
            call_log.append("alert")
            return ALERT

        composed = compose_or(
            logging_policy_block, logging_policy_allow, logging_policy_alert
        )
        composed(create_context("user", "agent"))
        assert call_log == ["block", "allow"], "Should have stopped after allow."

    def test_compose_or_returns_first_block_when_all_block(self):
        """When all policies block, return the first block decision."""

        def block_1(context):
            return BLOCK("First block")

        def block_2(context):
            return BLOCK("Second block")

        composed = compose_or(block_1, block_2)
        ctx = create_context("user", "agent")
        decision = composed(ctx)
        assert decision.reason == "First block"


class TestCompositionIntegration:
    """Integration tests for complex policy compositions."""

    def test_nested_composition(self):
        """Test that compositions can be nested."""
        and_composed = compose_and(policy_allow, policy_allow)
        or_composed = compose_or(policy_block, and_composed)

        ctx = create_context("user", "agent")
        decision = or_composed(ctx)
        assert decision.action == ActionType.ALLOW

    def test_complex_composition_scenario(self):
        """Test a complex real-world-like composition."""

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

        ctx_admin_business_hours = create_context(
            "user", "agent", role="admin", hour=14
        )
        assert flexible_access(ctx_admin_business_hours).action == ActionType.ALLOW

        ctx_emergency = create_context(
            "user", "agent", role="guest", hour=22, emergency=True
        )
        assert flexible_access(ctx_emergency).action == ActionType.ALLOW

        ctx_no_access = create_context("user", "agent", role="guest", hour=22)
        assert flexible_access(ctx_no_access).action == ActionType.BLOCK
