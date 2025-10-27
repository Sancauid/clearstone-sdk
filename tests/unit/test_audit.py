"""
Tests for audit trail functionality.
"""

import csv
import json

from clearstone.core.actions import ALERT, ALLOW, BLOCK
from clearstone.core.context import create_context
from clearstone.utils.audit import AuditTrail


class TestAuditTrail:
    """Test suite for AuditTrail class."""

    def test_audit_trail_record_decision(self):
        """Test that decisions are correctly recorded."""
        audit = AuditTrail()
        ctx = create_context("user1", "agent1")
        audit.record_decision("policy1", ctx, ALLOW)
        audit.record_decision("policy2", ctx, BLOCK("reason"))

        entries = audit.get_entries()
        assert len(entries) == 2
        assert entries[0]["policy_name"] == "policy1"
        assert entries[0]["decision"] == "allow"
        assert entries[1]["policy_name"] == "policy2"
        assert entries[1]["decision"] == "block"
        assert entries[1]["reason"] == "reason"

    def test_audit_trail_record_with_error(self):
        """Test recording decisions with error information."""
        audit = AuditTrail()
        ctx = create_context("user1", "agent1")
        audit.record_decision(
            "policy1", ctx, BLOCK("error"), error="Exception occurred"
        )

        entries = audit.get_entries()
        assert len(entries) == 1
        assert entries[0]["error"] == "Exception occurred"

    def test_audit_trail_get_entries_with_limit(self):
        """Test that get_entries respects the limit parameter."""
        audit = AuditTrail()
        ctx = create_context("user1", "agent1")

        for i in range(10):
            audit.record_decision(f"policy{i}", ctx, ALLOW)

        all_entries = audit.get_entries()
        assert len(all_entries) == 10

        limited_entries = audit.get_entries(limit=3)
        assert len(limited_entries) == 3
        assert limited_entries[0]["policy_name"] == "policy7"
        assert limited_entries[-1]["policy_name"] == "policy9"

    def test_audit_trail_summary_empty(self):
        """Test the summary for an empty audit trail."""
        audit = AuditTrail()
        summary = audit.summary()

        assert summary["total_decisions"] == 0
        assert summary["blocks"] == 0
        assert summary["alerts"] == 0
        assert summary["block_rate"] == 0.0

    def test_audit_trail_summary(self):
        """Test the summary statistics calculation."""
        audit = AuditTrail()
        ctx = create_context("user1", "agent1")

        audit.record_decision("p1", ctx, ALLOW)
        audit.record_decision("p2", ctx, BLOCK("b1"))
        audit.record_decision("p3", ctx, ALERT)
        audit.record_decision("p4", ctx, BLOCK("b2"))

        summary = audit.summary()
        assert summary["total_decisions"] == 4
        assert summary["blocks"] == 2
        assert summary["alerts"] == 1
        assert summary["block_rate"] == 0.5

    def test_audit_trail_summary_all_blocks(self):
        """Test summary when all decisions are blocks."""
        audit = AuditTrail()
        ctx = create_context("user1", "agent1")

        for i in range(5):
            audit.record_decision(f"p{i}", ctx, BLOCK(f"reason{i}"))

        summary = audit.summary()
        assert summary["total_decisions"] == 5
        assert summary["blocks"] == 5
        assert summary["block_rate"] == 1.0

    def test_audit_trail_to_json(self, tmp_path):
        """Test exporting the audit trail to a JSON file."""
        audit = AuditTrail()
        ctx = create_context("user1", "agent1")
        audit.record_decision("p1", ctx, ALLOW)

        json_file = tmp_path / "audit.json"
        audit.to_json(str(json_file))

        with open(json_file, "r") as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["policy_name"] == "p1"
        assert data[0]["user_id"] == "user1"
        assert data[0]["agent_id"] == "agent1"

    def test_audit_trail_to_json_multiple_entries(self, tmp_path):
        """Test JSON export with multiple entries."""
        audit = AuditTrail()
        ctx = create_context("user1", "agent1")

        audit.record_decision("p1", ctx, ALLOW)
        audit.record_decision("p2", ctx, BLOCK("test"))
        audit.record_decision("p3", ctx, ALERT)

        json_file = tmp_path / "audit.json"
        audit.to_json(str(json_file))

        with open(json_file, "r") as f:
            data = json.load(f)

        assert len(data) == 3
        assert data[1]["decision"] == "block"
        assert data[1]["reason"] == "test"

    def test_audit_trail_to_csv(self, tmp_path):
        """Test exporting the audit trail to a CSV file."""
        audit = AuditTrail()
        ctx = create_context("user1", "agent1")
        audit.record_decision("p1", ctx, BLOCK("test reason"))

        csv_file = tmp_path / "audit.csv"
        audit.to_csv(str(csv_file))

        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["policy_name"] == "p1"
        assert rows[0]["decision"] == "block"
        assert rows[0]["reason"] == "test reason"
        assert rows[0]["user_id"] == "user1"

    def test_audit_trail_to_csv_empty(self, tmp_path):
        """Test that CSV export handles empty audit trail gracefully."""
        audit = AuditTrail()
        csv_file = tmp_path / "audit.csv"
        audit.to_csv(str(csv_file))

        assert not csv_file.exists()

    def test_audit_trail_to_csv_multiple_entries(self, tmp_path):
        """Test CSV export with multiple entries."""
        audit = AuditTrail()
        ctx1 = create_context("user1", "agent1")
        ctx2 = create_context("user2", "agent2")

        audit.record_decision("p1", ctx1, ALLOW)
        audit.record_decision("p2", ctx2, BLOCK("denied"))

        csv_file = tmp_path / "audit.csv"
        audit.to_csv(str(csv_file))

        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["user_id"] == "user1"
        assert rows[1]["user_id"] == "user2"
        assert rows[1]["reason"] == "denied"

    def test_audit_trail_captures_context_information(self):
        """Test that all context information is captured."""
        audit = AuditTrail()
        ctx = create_context("user123", "agent456", session_id="session789")
        audit.record_decision("test_policy", ctx, ALLOW)

        entries = audit.get_entries()
        assert entries[0]["user_id"] == "user123"
        assert entries[0]["agent_id"] == "agent456"
        assert entries[0]["request_id"] == ctx.request_id
        assert "timestamp" in entries[0]
