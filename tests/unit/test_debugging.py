"""
Tests for policy debugger.
"""

import pytest
from clearstone.utils.debugging import PolicyDebugger
from clearstone.core.actions import ALLOW, BLOCK
from clearstone.core.context import create_context


def branching_policy(context):
    """A policy with multiple logical branches for testing the debugger."""
    role = context.metadata.get("role", "guest")
    amount = context.metadata.get("amount", 0)

    if role == "admin":
        return ALLOW

    if amount > 1000:
        return BLOCK("Amount exceeds 1000 for non-admins.")

    return ALLOW


class TestPolicyDebugger:
    """Test suite for PolicyDebugger."""

    def test_debugger_trace_evaluation_allow_path(self):
        """Test that the debugger traces the correct path for an ALLOW decision."""
        debugger = PolicyDebugger()
        ctx = create_context("user", "agent", role="user", amount=500)

        decision, trace = debugger.trace_evaluation(branching_policy, ctx)

        assert decision.action == ALLOW.action
        assert len(trace) >= 4

        line_texts = [event['line_text'] for event in trace]
        assert 'role = context.metadata.get("role", "guest")' in line_texts
        assert 'if role == "admin":' in line_texts
        assert 'if amount > 1000:' in line_texts
        assert 'return ALLOW' in line_texts
        assert 'return BLOCK("Amount exceeds 1000 for non-admins.")' not in line_texts

    def test_debugger_trace_evaluation_block_path(self):
        """Test that the debugger traces the correct path for a BLOCK decision."""
        debugger = PolicyDebugger()
        ctx = create_context("user", "agent", role="user", amount=2000)

        decision, trace = debugger.trace_evaluation(branching_policy, ctx)

        assert decision.is_block()
        assert decision.reason == "Amount exceeds 1000 for non-admins."

        line_texts = [event['line_text'] for event in trace]
        assert 'if amount > 1000:' in line_texts
        assert 'return BLOCK("Amount exceeds 1000 for non-admins.")' in line_texts

    def test_debugger_trace_evaluation_admin_path(self):
        """Test that the debugger traces the admin path correctly."""
        debugger = PolicyDebugger()
        ctx = create_context("admin_user", "agent", role="admin", amount=5000)

        decision, trace = debugger.trace_evaluation(branching_policy, ctx)

        assert decision.action == ALLOW.action

        line_texts = [event['line_text'] for event in trace]
        assert 'if role == "admin":' in line_texts
        assert 'return ALLOW' in line_texts

    def test_debugger_format_trace(self):
        """Test the human-readable formatting of a trace."""
        debugger = PolicyDebugger()
        ctx = create_context("user", "agent", role="user", amount=500)
        decision, trace = debugger.trace_evaluation(branching_policy, ctx)

        formatted_string = debugger.format_trace(branching_policy, decision, trace)

        assert "--- Policy Debug Trace for 'branching_policy' ---" in formatted_string
        assert "Execution Path:" in formatted_string
        assert "L" in formatted_string
        assert "Locals:" in formatted_string
        assert "Final Decision: ALLOW" in formatted_string

    def test_debugger_trace_captures_locals(self):
        """Test that the debugger captures local variables correctly."""
        debugger = PolicyDebugger()
        ctx = create_context("user", "agent", role="user", amount=500)

        decision, trace = debugger.trace_evaluation(branching_policy, ctx)

        found_role_local = False
        found_amount_local = False

        for event in trace:
            if 'role' in event['locals']:
                found_role_local = True
            if 'amount' in event['locals']:
                found_amount_local = True

        assert found_role_local, "Should capture 'role' local variable"
        assert found_amount_local, "Should capture 'amount' local variable"

    def test_debugger_with_simple_policy(self):
        """Test debugger with a simple one-line policy."""
        def simple_policy(context):
            return ALLOW

        debugger = PolicyDebugger()
        ctx = create_context("user", "agent")

        decision, trace = debugger.trace_evaluation(simple_policy, ctx)

        assert decision.action == ALLOW.action
        assert len(trace) >= 1

    def test_debugger_format_trace_with_block_reason(self):
        """Test formatting includes the block reason."""
        debugger = PolicyDebugger()
        ctx = create_context("user", "agent", role="user", amount=2000)

        decision, trace = debugger.trace_evaluation(branching_policy, ctx)
        formatted = debugger.format_trace(branching_policy, decision, trace)

        assert "Amount exceeds 1000 for non-admins." in formatted
        assert "Final Decision: BLOCK" in formatted

