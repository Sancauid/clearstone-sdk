"""
Policy performance and decision metrics collector.
"""

from collections import defaultdict
from typing import Dict, Any, List
from clearstone.core.actions import Decision, ActionType


class PolicyMetrics:
    """
    A simple, in-memory collector for policy performance and decision metrics.
    This class is zero-dependency and designed for local-first analysis.
    """

    def __init__(self):
        self.stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "eval_count": 0,
                "block_count": 0,
                "alert_count": 0,
                "total_latency_ms": 0.0,
            }
        )

    def record(self, policy_name: str, decision: Decision, latency_ms: float):
        """Records a single policy evaluation event."""
        s = self.stats[policy_name]
        s["eval_count"] += 1
        s["total_latency_ms"] += latency_ms

        if decision.action == ActionType.BLOCK:
            s["block_count"] += 1
        elif decision.action == ActionType.ALERT:
            s["alert_count"] += 1

    def summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns a summary of all collected metrics, calculating averages.
        """
        summary_data = {}
        for name, data in self.stats.items():
            eval_count = data["eval_count"]
            avg_latency = (data["total_latency_ms"] / eval_count) if eval_count > 0 else 0
            summary_data[name] = {
                "eval_count": eval_count,
                "block_count": data["block_count"],
                "alert_count": data["alert_count"],
                "avg_latency_ms": round(avg_latency, 4),
            }
        return summary_data

    def get_slowest_policies(self, top_n: int = 5) -> List[tuple]:
        """Returns the top N policies sorted by average latency."""
        summary = self.summary()
        sorted_policies = sorted(
            summary.items(),
            key=lambda item: item[1]["avg_latency_ms"],
            reverse=True
        )
        return sorted_policies[:top_n]

    def get_top_blocking_policies(self, top_n: int = 5) -> List[tuple]:
        """Returns the top N policies that blocked most often."""
        summary = self.summary()
        sorted_policies = sorted(
            summary.items(),
            key=lambda item: item[1]["block_count"],
            reverse=True
        )
        return sorted_policies[:top_n]

