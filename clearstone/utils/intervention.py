# clearstone/utils/intervention.py

import sys
import threading
from typing import Dict

from clearstone.core.actions import Decision

_pending_interventions: Dict[str, Dict] = {}
_lock = threading.Lock()


class InterventionClient:
    """
    A simple client for handling Human-in-the-Loop (HITL) interventions.
    This default implementation uses command-line input/output.
    """

    def request_intervention(self, decision: Decision):
        """
        Logs a PAUSE decision as a pending intervention request.
        """
        if not decision.is_pause():
            return

        intervention_id = decision.metadata.get("intervention_id")
        if not intervention_id:
            return

        with _lock:
            _pending_interventions[intervention_id] = {
                "reason": decision.reason,
                "metadata": decision.metadata,
                "status": "pending",
            }

    def wait_for_approval(self, intervention_id: str, prompt: str = None) -> bool:
        """
        Waits for a human to approve or reject a pending intervention via the CLI.

        Args:
          intervention_id: The unique ID of the intervention to wait for.
          prompt: The message to display to the user.

        Returns:
          True if the action was approved, False otherwise.
        """
        with _lock:
            intervention = _pending_interventions.get(intervention_id)
            if not intervention:
                print(
                    f"Warning: Intervention ID '{intervention_id}' not found.",
                    file=sys.stderr,
                )
                return False

        prompt = (
            prompt or f"Approve action for intervention '{intervention_id}'? (yes/no): "
        )

        print("\n--- ⏸️ HUMAN INTERVENTION REQUIRED ---")
        print(f"  Reason: {intervention['reason']}")

        try:
            response = input(prompt).lower().strip()
            approved = response in ["y", "yes"]
        except (EOFError, KeyboardInterrupt):
            approved = False

        with _lock:
            _pending_interventions[intervention_id]["status"] = (
                "approved" if approved else "rejected"
            )

        if approved:
            print("--- ✅ ACTION APPROVED BY USER ---")
        else:
            print("--- ❌ ACTION REJECTED BY USER ---")

        return approved
