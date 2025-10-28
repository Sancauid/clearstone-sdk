# tests/unit/test_policy_engine.py

import pytest

from clearstone.core.actions import ALERT, ALLOW, BLOCK, PAUSE, ActionType
from clearstone.core.context import context_scope, create_context, set_current_context
from clearstone.core.policy import Policy, PolicyEngine, get_policies, reset_policies


@pytest.fixture(autouse=True)
def reset_policy_registry():
    reset_policies()
    set_current_context(None)


def test_policy_decorator_registration():
    """Ensure the @Policy decorator correctly registers a function."""

    @Policy(name="test_policy", priority=10)
    def my_policy(context):
        return ALLOW

    policies = get_policies()
    assert len(policies) == 1
    assert policies[0].name == "test_policy"
    assert policies[0].priority == 10
    assert callable(policies[0].func)


def test_policy_priority_sorting():
    """Ensure get_policies returns policies sorted by priority (descending)."""

    @Policy(name="p0", priority=0)
    def p0(context):
        return ALLOW

    @Policy(name="p100", priority=100)
    def p100(context):
        return ALLOW

    @Policy(name="p50", priority=50)
    def p50(context):
        return ALLOW

    policies = get_policies()
    assert [p.name for p in policies] == ["p100", "p50", "p0"]


def test_policy_decorator_raises_on_invalid_signature():
    """Ensure the decorator validates the function signature."""
    with pytest.raises(TypeError, match="must have the signature"):

        @Policy(name="bad_sig")
        def bad_policy(wrong_arg):
            return ALLOW


def test_engine_raises_if_no_policies_registered():
    """Ensure PolicyEngine.__init__ raises an error if no policies exist."""
    with pytest.raises(ValueError, match="initialized with no valid policies"):
        PolicyEngine()


def test_engine_raises_if_no_context_is_active():
    """Ensure engine.evaluate raises an error if context is missing."""

    @Policy(name="dummy")
    def p(context):
        return ALLOW

    engine = PolicyEngine()
    with pytest.raises(RuntimeError, match="No PolicyContext is active"):
        engine.evaluate()


def test_engine_block_is_a_veto():
    """Test the core veto logic: a BLOCK decision stops execution immediately."""
    call_log = []

    @Policy(name="blocker", priority=100)
    def block_policy(context):
        call_log.append("blocker")
        return BLOCK("Access denied")

    @Policy(name="never_called", priority=0)
    def never_called_policy(context):
        call_log.append("never_called")
        return ALLOW

    engine = PolicyEngine()
    ctx = create_context("user1", "agent1")
    with context_scope(ctx):
        decision = engine.evaluate()

    assert decision.action == ActionType.BLOCK
    assert decision.reason == "Access denied"
    assert call_log == ["blocker"], "Execution should stop after the blocking policy."


def test_engine_returns_first_non_allow_decision():
    """Test that the engine returns the highest-priority non-ALLOW decision."""

    @Policy(name="p1_pause", priority=100)
    def p1(context):
        return PAUSE("Test pause")

    @Policy(name="p2_alert", priority=50)
    def p2(context):
        return ALERT

    @Policy(name="p3_allow", priority=0)
    def p3(context):
        return ALLOW

    engine = PolicyEngine()
    ctx = create_context("user1", "agent1")
    with context_scope(ctx):
        decision = engine.evaluate()

    assert (
        decision.action == ActionType.PAUSE
    ), "Highest priority action (PAUSE) should be returned."


def test_engine_policy_exception_causes_fail_safe_block():
    """Ensure that an exception within a policy results in a BLOCK."""

    @Policy(name="buggy_policy", priority=100)
    def buggy_policy(context):
        raise ValueError("Something went wrong")

    engine = PolicyEngine()
    ctx = create_context("user1", "agent1")
    with context_scope(ctx):
        decision = engine.evaluate()

    assert decision.action == ActionType.BLOCK
    assert "raised an exception: Something went wrong" in decision.reason


def test_engine_audit_trail():
    """Verify that the audit trail logs policy evaluations correctly."""

    @Policy(name="p1")
    def p1(context):
        return ALLOW

    @Policy(name="p2")
    def p2(context):
        return ALERT

    engine = PolicyEngine()
    ctx = create_context("user1", "agent1")
    with context_scope(ctx):
        engine.evaluate()

    audit_trail = engine.get_audit_trail()
    assert len(audit_trail) == 2
    assert audit_trail[0]["policy_name"] == "p1"
    assert audit_trail[0]["decision"] == "allow"
    assert audit_trail[1]["policy_name"] == "p2"
    assert audit_trail[1]["decision"] == "alert"


def test_engine_with_explicit_policies_list():
    """Test that the engine uses ONLY the policies provided in the constructor."""

    # These policies are defined but SHOULD NOT be auto-discovered
    @Policy(name="should_be_ignored", priority=100)
    def ignored_policy(context):
        return BLOCK("This should not run")

    # These are the policies we will explicitly pass
    @Policy(name="explicit_policy_1", priority=10)
    def explicit_1(context):
        return ALLOW

    @Policy(name="explicit_policy_2", priority=20)
    def explicit_2(context):
        return ALLOW

    # Initialize the engine with an explicit list
    engine = PolicyEngine(policies=[explicit_1, explicit_2])

    # Check that ONLY the explicit policies are loaded, and they are sorted
    assert len(engine._policies) == 2
    assert engine._policies[0].name == "explicit_policy_2"  # Higher priority first
    assert engine._policies[1].name == "explicit_policy_1"


def test_engine_with_explicit_empty_list_raises_error():
    """Test that initializing with an empty list of policies raises a ValueError."""
    with pytest.raises(ValueError, match="initialized with no valid policies"):
        PolicyEngine(policies=[])


def test_engine_auto_discovery_still_works_by_default():
    """Test that calling PolicyEngine() with no args preserves auto-discovery."""

    @Policy(name="auto_discovered_1")
    def auto_1(context):
        return ALLOW

    @Policy(name="auto_discovered_2")
    def auto_2(context):
        return ALLOW

    # Initialize with no arguments
    engine = PolicyEngine()

    assert len(engine._policies) == 2
    policy_names = {p.name for p in engine._policies}
    assert "auto_discovered_1" in policy_names
    assert "auto_discovered_2" in policy_names
