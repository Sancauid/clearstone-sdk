"""
Tests for policy validator.
"""

import pytest
import random
import time
from clearstone.utils.validator import PolicyValidator, PolicyValidationError
from clearstone.core.actions import ALLOW, BLOCK
from clearstone.core.context import create_context


def good_policy(context):
    """A well-behaved policy."""
    if context.metadata.get("role") == "admin":
        return BLOCK("Admin blocked for test")
    return ALLOW


_call_counter = 0

def non_deterministic_policy(context):
    """A policy that uses a counter, making it non-deterministic."""
    global _call_counter
    _call_counter += 1
    if _call_counter % 2 == 0:
        return BLOCK("Blocked by chance")
    return ALLOW


def slow_policy(context):
    """A policy that is intentionally slow."""
    time.sleep(0.002)
    return ALLOW


def fragile_policy(context):
    """A policy that will crash if metadata is missing."""
    if context.metadata["role"] == "admin":
        return BLOCK("Admin blocked")
    return ALLOW


class TestPolicyValidator:
    """Test suite for PolicyValidator."""

    def test_validator_with_good_policy(self):
        """A good policy should pass all validation checks."""
        validator = PolicyValidator()
        failures = validator.run_all_checks(good_policy)
        assert len(failures) == 0, f"A good policy should have no validation failures. Got: {failures}"

    def test_validate_determinism_fails(self):
        """The validator should catch non-deterministic policies."""
        validator = PolicyValidator()
        with pytest.raises(PolicyValidationError, match="is non-deterministic"):
            validator.validate_determinism(non_deterministic_policy)

    def test_validate_determinism_passes(self):
        """A deterministic policy should pass the determinism check."""
        validator = PolicyValidator()
        validator.validate_determinism(good_policy)

    def test_validate_performance_fails(self):
        """The validator should catch slow policies."""
        validator = PolicyValidator()
        with pytest.raises(PolicyValidationError, match="is too slow"):
            validator.validate_performance(slow_policy, max_latency_ms=1.0)

    def test_validate_performance_passes(self):
        """A fast policy should pass the performance check."""
        validator = PolicyValidator()
        validator.validate_performance(good_policy, max_latency_ms=10.0)

    def test_validate_exception_safety_fails(self):
        """The validator should catch fragile policies that crash on missing keys."""
        validator = PolicyValidator()
        with pytest.raises(PolicyValidationError, match="is not exception-safe"):
            validator.validate_exception_safety(fragile_policy)

    def test_validate_exception_safety_passes(self):
        """A safe policy should pass the exception safety check."""
        validator = PolicyValidator()
        validator.validate_exception_safety(good_policy)

    def test_run_all_checks_collects_multiple_failures(self):
        """The run_all_checks helper should report all failures found."""
        def multi_fail_policy(context):
            if random.random() > 0.5:
                return BLOCK("Random block")
            if context.metadata["should_crash"]:
                return BLOCK("Crash block")
            return ALLOW

        validator = PolicyValidator()
        failures = validator.run_all_checks(multi_fail_policy)
        assert len(failures) >= 2
        assert any("exception" in f.lower() for f in failures)
        assert any("KeyError" in f for f in failures)

    def test_custom_validation_context(self):
        """Test that a custom validation context can be provided."""
        custom_context = create_context(
            "custom_user",
            "custom_agent",
            role="admin"
        )
        validator = PolicyValidator(default_context=custom_context)

        decision = good_policy(validator._default_context)
        assert decision.action.name == "BLOCK"

    def test_performance_check_with_custom_budget(self):
        """Test performance validation with different time budgets."""
        validator = PolicyValidator()

        validator.validate_performance(good_policy, max_latency_ms=5.0, num_runs=100)

        with pytest.raises(PolicyValidationError):
            validator.validate_performance(slow_policy, max_latency_ms=0.5, num_runs=10)

    def test_determinism_check_with_custom_runs(self):
        """Test determinism validation with different number of runs."""
        validator = PolicyValidator()

        validator.validate_determinism(good_policy, num_runs=10)

        with pytest.raises(PolicyValidationError):
            validator.validate_determinism(non_deterministic_policy, num_runs=10)


class TestPolicyValidationError:
    """Test suite for PolicyValidationError exception."""

    def test_policy_validation_error_is_assertion_error(self):
        """PolicyValidationError should be a subclass of AssertionError."""
        error = PolicyValidationError("Test error")
        assert isinstance(error, AssertionError)

    def test_policy_validation_error_message(self):
        """PolicyValidationError should preserve the error message."""
        message = "Custom validation error message"
        error = PolicyValidationError(message)
        assert str(error) == message

