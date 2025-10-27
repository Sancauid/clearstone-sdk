"""
Audit trail utilities for capturing and analyzing policy decisions.
"""

import csv
import json
from datetime import datetime, timezone
from typing import List, Dict, Any
from clearstone.core.context import PolicyContext
from clearstone.core.actions import Decision, ActionType


class AuditTrail:
    """
    Captures and provides utilities for analyzing a sequence of policy decisions.

    Example:
        audit = AuditTrail()
        engine = PolicyEngine(audit_trail=audit)
        # ... run policies ...
        print(audit.summary())
        audit.to_json("audit_log.json")
    """

    def __init__(self):
        self._entries: List[Dict[str, Any]] = []

    def record_decision(
        self,
        policy_name: str,
        context: PolicyContext,
        decision: Decision,
        error: str = None
    ):
        """
        Records a single policy evaluation event.

        Args:
            policy_name: Name of the policy that made the decision.
            context: The PolicyContext for this evaluation.
            decision: The Decision returned by the policy.
            error: Optional error message if the policy raised an exception.
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "policy_name": policy_name,
            "decision": decision.action.value,
            "reason": decision.reason,
            "user_id": context.user_id,
            "agent_id": context.agent_id,
            "request_id": context.request_id,
            "error": error
        }
        self._entries.append(entry)

    def get_entries(self, limit: int = 0) -> List[Dict[str, Any]]:
        """
        Returns the recorded audit entries.

        Args:
            limit: If > 0, returns only the last N entries. If 0, returns all.

        Returns:
            List of audit entry dictionaries.
        """
        if limit > 0:
            return self._entries[-limit:]
        return self._entries

    def summary(self) -> Dict[str, Any]:
        """
        Calculates and returns a summary of the decisions in the trail.

        Returns:
            Dictionary with summary statistics including:
            - total_decisions: Total number of decisions recorded
            - blocks: Number of BLOCK decisions
            - alerts: Number of ALERT decisions
            - block_rate: Ratio of blocks to total decisions
        """
        total = len(self._entries)
        if total == 0:
            return {"total_decisions": 0, "blocks": 0, "alerts": 0, "block_rate": 0.0}

        blocks = sum(1 for e in self._entries if e["decision"] == ActionType.BLOCK.value)
        alerts = sum(1 for e in self._entries if e["decision"] == ActionType.ALERT.value)

        return {
            "total_decisions": total,
            "blocks": blocks,
            "alerts": alerts,
            "block_rate": (blocks / total)
        }

    def to_json(self, filepath: str, **kwargs):
        """
        Exports the audit trail to a JSON file.

        Args:
            filepath: Path to the output JSON file.
            **kwargs: Additional arguments passed to json.dump().

        Example:
            audit.to_json("audit_log.json", indent=2)
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self._entries, f, indent=2, **kwargs)

    def to_csv(self, filepath: str, **kwargs):
        """
        Exports the audit trail to a CSV file.

        Args:
            filepath: Path to the output CSV file.
            **kwargs: Additional arguments passed to csv.DictWriter.

        Example:
            audit.to_csv("audit_log.csv")
        """
        if not self._entries:
            return

        headers = self._entries[0].keys()
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(self._entries)

