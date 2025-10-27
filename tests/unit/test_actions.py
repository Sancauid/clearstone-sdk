# tests/unit/test_actions.py

from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from clearstone.core.actions import (
    ALERT,
    ALLOW,
    BLOCK,
    PAUSE,
    REDACT,
    SKIP,
    ActionType,
    Decision,
)


def test_singleton_instances():
    """Test that simple actions are pre-allocated singletons."""
    assert ALLOW.action == ActionType.ALLOW
    assert ALERT.action == ActionType.ALERT
    assert SKIP.action == ActionType.SKIP
    assert ALLOW == Decision(ActionType.ALLOW)
    assert ALLOW is ALLOW


def test_block_factory_requires_reason():
    """Test that the BLOCK factory function requires a reason."""
    with pytest.raises(ValueError, match="requires a non-empty string reason"):
        BLOCK("")
    with pytest.raises(ValueError, match="requires a non-empty string reason"):
        BLOCK(None)


def test_block_factory_creates_correct_decision():
    """Test that the BLOCK factory function creates a valid Decision object."""
    decision = BLOCK("Token limit exceeded", code=429)
    assert isinstance(decision, Decision)
    assert decision.action == ActionType.BLOCK
    assert decision.reason == "Token limit exceeded"
    assert decision.metadata == {"code": 429}
    assert decision.is_block() is True


def test_redact_factory_requires_fields():
    """Test that the REDACT factory requires a list of fields."""
    with pytest.raises(ValueError, match="requires a non-empty list of fields"):
        REDACT("PII found", fields=[])
    with pytest.raises(ValueError, match="requires a non-empty list of fields"):
        REDACT("PII found", fields=None)


def test_redact_factory_adds_fields_to_metadata():
    """Test that the REDACT factory correctly populates metadata."""
    decision = REDACT("PII detected", fields=["ssn", "email"], source="scanner-v2")
    assert isinstance(decision, Decision)
    assert decision.action == ActionType.REDACT
    assert decision.reason == "PII detected"
    assert decision.metadata["fields_to_redact"] == ["ssn", "email"]
    assert decision.metadata["source"] == "scanner-v2"


def test_pause_factory_requires_reason():
    """Test that the PAUSE factory function requires a reason."""
    with pytest.raises(ValueError, match="requires a non-empty string reason"):
        PAUSE("")
    with pytest.raises(ValueError, match="requires a non-empty string reason"):
        PAUSE(None)


def test_pause_factory_creates_correct_decision():
    """Test that the PAUSE factory function creates a valid Decision object."""
    decision = PAUSE("Manual approval required")
    assert isinstance(decision, Decision)
    assert decision.action == ActionType.PAUSE
    assert decision.reason == "Manual approval required"
    assert "intervention_id" in decision.metadata
    assert decision.metadata["intervention_id"].startswith("intervention_")
    assert decision.is_pause() is True


def test_pause_factory_accepts_custom_intervention_id():
    """Test that PAUSE accepts a custom intervention_id."""
    decision = PAUSE("Manual approval required", intervention_id="custom-123")
    assert decision.metadata["intervention_id"] == "custom-123"


def test_decision_is_frozen_and_immutable():
    """Test that Decision objects are immutable."""
    assert is_dataclass(ALLOW)
    with pytest.raises(FrozenInstanceError):
        ALLOW.reason = "This should fail"

    block_decision = BLOCK("test")
    with pytest.raises(FrozenInstanceError):
        block_decision.action = ActionType.ALLOW
