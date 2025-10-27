# tests/unit/test_intervention.py

from unittest.mock import patch

from clearstone.core.actions import PAUSE
from clearstone.utils.intervention import InterventionClient


def test_intervention_client_request_intervention():
    """Test that an intervention is correctly logged."""
    client = InterventionClient()
    pause_decision = PAUSE("Manual approval needed", intervention_id="test-123")

    from clearstone.utils.intervention import _pending_interventions

    _pending_interventions.clear()

    client.request_intervention(pause_decision)

    assert "test-123" in _pending_interventions
    assert _pending_interventions["test-123"]["status"] == "pending"
    assert _pending_interventions["test-123"]["reason"] == "Manual approval needed"


@patch("builtins.input", return_value="yes")
def test_wait_for_approval_approves(mock_input):
    """Test that 'yes' input results in an approval."""
    client = InterventionClient()
    pause_decision = PAUSE("Test approval", intervention_id="approve-test")
    client.request_intervention(pause_decision)

    is_approved = client.wait_for_approval("approve-test")

    assert is_approved is True
    mock_input.assert_called_once()

    from clearstone.utils.intervention import _pending_interventions

    assert _pending_interventions["approve-test"]["status"] == "approved"


@patch("builtins.input", return_value="no")
def test_wait_for_approval_rejects(mock_input):
    """Test that 'no' or any other input results in a rejection."""
    client = InterventionClient()
    pause_decision = PAUSE("Test rejection", intervention_id="reject-test")
    client.request_intervention(pause_decision)

    is_approved = client.wait_for_approval("reject-test")

    assert is_approved is False
    mock_input.assert_called_once()

    from clearstone.utils.intervention import _pending_interventions

    assert _pending_interventions["reject-test"]["status"] == "rejected"
