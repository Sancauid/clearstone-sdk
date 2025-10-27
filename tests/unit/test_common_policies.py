"""
Tests for the pre-built common policies library.
"""

from unittest.mock import patch

import pytest

from clearstone.core.actions import ActionType
from clearstone.core.context import create_context, set_current_context
from clearstone.core.policy import reset_policies
from clearstone.policies.common import (
    admin_only_action_policy,
    alert_on_failed_auth_policy,
    alert_on_privileged_access_policy,
    block_dangerous_tools_policy,
    block_external_apis_policy,
    block_pii_tools_policy,
    business_hours_only_policy,
    create_audit_mode_policies,
    create_cost_control_policies,
    create_data_protection_policies,
    create_safe_mode_policies,
    create_security_policies,
    daily_cost_limit_policy,
    pause_before_write_policy,
    rate_limit_policy,
    rbac_tool_access_policy,
    redact_pii_policy,
    require_approval_for_high_cost_policy,
    session_cost_limit_policy,
    token_limit_policy,
)


@pytest.fixture(autouse=True)
def reset_policy_registry():
    reset_policies()
    set_current_context(None)


class TestTokenAndCostPolicies:
    """Test suite for token and cost control policies."""

    def test_token_limit_policy_allows_under_limit(self):
        ctx = create_context("user1", "agent1", token_limit=5000, tokens_used=3000)
        decision = token_limit_policy(ctx)
        assert decision.action == ActionType.ALLOW

    def test_token_limit_policy_blocks_over_limit(self):
        ctx = create_context("user1", "agent1", token_limit=5000, tokens_used=6000)
        decision = token_limit_policy(ctx)
        assert decision.action == ActionType.BLOCK
        assert "Token limit exceeded: 6000 > 5000" in decision.reason

    def test_token_limit_policy_allows_when_no_limit_set(self):
        ctx = create_context("user1", "agent1", tokens_used=10000)
        decision = token_limit_policy(ctx)
        assert decision.action == ActionType.ALLOW

    def test_session_cost_limit_policy_alerts_over_limit(self):
        ctx = create_context(
            "user1", "agent1", session_cost_limit=50.0, session_cost=55.0
        )
        decision = session_cost_limit_policy(ctx)
        assert decision.action == ActionType.ALERT

    def test_session_cost_limit_policy_allows_under_limit(self):
        ctx = create_context(
            "user1", "agent1", session_cost_limit=50.0, session_cost=45.0
        )
        decision = session_cost_limit_policy(ctx)
        assert decision.action == ActionType.ALLOW

    def test_daily_cost_limit_policy_blocks_over_limit(self):
        ctx = create_context(
            "user1", "agent1", daily_cost_limit=1000.0, daily_cost=1250.0
        )
        decision = daily_cost_limit_policy(ctx)
        assert decision.action == ActionType.BLOCK
        assert "Daily cost limit exceeded" in decision.reason

    def test_daily_cost_limit_policy_allows_under_limit(self):
        ctx = create_context(
            "user1", "agent1", daily_cost_limit=1000.0, daily_cost=500.0
        )
        decision = daily_cost_limit_policy(ctx)
        assert decision.action == ActionType.ALLOW


class TestRBACPolicies:
    """Test suite for role-based access control policies."""

    def test_rbac_tool_access_blocks_forbidden_tool(self):
        ctx = create_context(
            "user1",
            "agent1",
            user_role="guest",
            tool_name="delete_database",
            restricted_tools={
                "guest": ["delete_database", "admin_panel"],
                "user": ["admin_panel"],
            },
        )
        decision = rbac_tool_access_policy(ctx)
        assert decision.action == ActionType.BLOCK
        assert "Role 'guest' cannot access tool 'delete_database'" in decision.reason

    def test_rbac_tool_access_allows_permitted_tool(self):
        ctx = create_context(
            "user1",
            "agent1",
            user_role="user",
            tool_name="read_data",
            restricted_tools={
                "guest": ["delete_database", "admin_panel"],
                "user": ["admin_panel"],
            },
        )
        decision = rbac_tool_access_policy(ctx)
        assert decision.action == ActionType.ALLOW

    def test_rbac_defaults_to_guest_role(self):
        ctx = create_context(
            "user1",
            "agent1",
            tool_name="admin_panel",
            restricted_tools={"guest": ["admin_panel"]},
        )
        decision = rbac_tool_access_policy(ctx)
        assert decision.action == ActionType.BLOCK

    def test_admin_only_action_blocks_non_admin(self):
        ctx = create_context(
            "user1",
            "agent1",
            user_role="user",
            tool_name="delete_all_users",
            require_admin_for=["delete_all_users", "export_database"],
        )
        decision = admin_only_action_policy(ctx)
        assert decision.action == ActionType.BLOCK
        assert "Admin role required" in decision.reason

    def test_admin_only_action_allows_admin(self):
        ctx = create_context(
            "user1",
            "agent1",
            user_role="admin",
            tool_name="delete_all_users",
            require_admin_for=["delete_all_users"],
        )
        decision = admin_only_action_policy(ctx)
        assert decision.action == ActionType.ALLOW

    def test_admin_only_action_allows_unrestricted_tools(self):
        ctx = create_context(
            "user1",
            "agent1",
            user_role="user",
            tool_name="read_data",
            require_admin_for=["delete_all_users"],
        )
        decision = admin_only_action_policy(ctx)
        assert decision.action == ActionType.ALLOW


class TestPIIProtectionPolicies:
    """Test suite for PII and sensitive data protection policies."""

    def test_redact_pii_policy_redacts_configured_fields(self):
        ctx = create_context(
            "user1",
            "agent1",
            tool_name="fetch_user_data",
            pii_fields={"fetch_user_data": ["ssn", "credit_card", "email"]},
        )
        decision = redact_pii_policy(ctx)
        assert decision.action == ActionType.REDACT
        assert decision.metadata["fields_to_redact"] == ["ssn", "credit_card", "email"]

    def test_redact_pii_policy_allows_non_pii_tools(self):
        ctx = create_context(
            "user1",
            "agent1",
            tool_name="fetch_public_data",
            pii_fields={"fetch_user_data": ["ssn", "credit_card"]},
        )
        decision = redact_pii_policy(ctx)
        assert decision.action == ActionType.ALLOW

    def test_block_pii_tools_blocks_non_privileged_users(self):
        ctx = create_context(
            "user1",
            "agent1",
            user_role="guest",
            tool_name="fetch_ssn",
            pii_tools=["fetch_ssn", "get_credit_card"],
        )
        decision = block_pii_tools_policy(ctx)
        assert decision.action == ActionType.BLOCK
        assert "PII access denied" in decision.reason

    def test_block_pii_tools_allows_admin(self):
        ctx = create_context(
            "user1",
            "agent1",
            user_role="admin",
            tool_name="fetch_ssn",
            pii_tools=["fetch_ssn"],
        )
        decision = block_pii_tools_policy(ctx)
        assert decision.action == ActionType.ALLOW

    def test_block_pii_tools_allows_data_engineer(self):
        ctx = create_context(
            "user1",
            "agent1",
            user_role="data_engineer",
            tool_name="fetch_ssn",
            pii_tools=["fetch_ssn"],
        )
        decision = block_pii_tools_policy(ctx)
        assert decision.action == ActionType.ALLOW


class TestDangerousOperationPolicies:
    """Test suite for dangerous operation prevention policies."""

    def test_block_dangerous_tools_blocks_delete_database(self):
        ctx = create_context("user1", "agent1", tool_name="delete_database")
        decision = block_dangerous_tools_policy(ctx)
        assert decision.action == ActionType.BLOCK
        assert "Dangerous tool blocked" in decision.reason

    def test_block_dangerous_tools_blocks_drop_table(self):
        ctx = create_context("user1", "agent1", tool_name="drop_table")
        decision = block_dangerous_tools_policy(ctx)
        assert decision.action == ActionType.BLOCK

    def test_block_dangerous_tools_case_insensitive(self):
        ctx = create_context("user1", "agent1", tool_name="DELETE_DATABASE")
        decision = block_dangerous_tools_policy(ctx)
        assert decision.action == ActionType.BLOCK

    def test_block_dangerous_tools_allows_safe_tools(self):
        ctx = create_context("user1", "agent1", tool_name="read_data")
        decision = block_dangerous_tools_policy(ctx)
        assert decision.action == ActionType.ALLOW

    def test_pause_before_write_pauses_for_delete(self):
        ctx = create_context(
            "user1",
            "agent1",
            tool_name="delete_user",
            require_pause_for=["create", "update", "delete"],
        )
        decision = pause_before_write_policy(ctx)
        assert decision.action == ActionType.PAUSE

    def test_pause_before_write_pauses_for_update(self):
        ctx = create_context(
            "user1",
            "agent1",
            tool_name="update_record",
            require_pause_for=["update", "delete"],
        )
        decision = pause_before_write_policy(ctx)
        assert decision.action == ActionType.PAUSE

    def test_pause_before_write_allows_read_operations(self):
        ctx = create_context(
            "user1",
            "agent1",
            tool_name="read_data",
            require_pause_for=["update", "delete"],
        )
        decision = pause_before_write_policy(ctx)
        assert decision.action == ActionType.ALLOW


class TestSecurityAlertPolicies:
    """Test suite for security alert policies."""

    def test_alert_on_privileged_access_alerts_on_privileged_tool(self):
        ctx = create_context(
            "user1",
            "agent1",
            tool_name="export_all_data",
            privileged_tools=["export_all_data", "admin_console"],
        )
        decision = alert_on_privileged_access_policy(ctx)
        assert decision.action == ActionType.ALERT

    def test_alert_on_privileged_access_allows_normal_tools(self):
        ctx = create_context(
            "user1",
            "agent1",
            tool_name="read_data",
            privileged_tools=["export_all_data"],
        )
        decision = alert_on_privileged_access_policy(ctx)
        assert decision.action == ActionType.ALLOW

    def test_alert_on_failed_auth_alerts_after_threshold(self):
        ctx = create_context("user1", "agent1", auth_failed=True, attempt_count=5)
        decision = alert_on_failed_auth_policy(ctx)
        assert decision.action == ActionType.ALERT

    def test_alert_on_failed_auth_allows_under_threshold(self):
        ctx = create_context("user1", "agent1", auth_failed=True, attempt_count=2)
        decision = alert_on_failed_auth_policy(ctx)
        assert decision.action == ActionType.ALLOW

    def test_alert_on_failed_auth_allows_successful_auth(self):
        ctx = create_context("user1", "agent1", auth_failed=False)
        decision = alert_on_failed_auth_policy(ctx)
        assert decision.action == ActionType.ALLOW


class TestTimeBasedPolicies:
    """Test suite for time-based restriction policies."""

    def test_business_hours_only_allows_during_hours(self):
        ctx = create_context("user1", "agent1", current_hour=14, business_hours=(9, 17))
        decision = business_hours_only_policy(ctx)
        assert decision.action == ActionType.ALLOW

    def test_business_hours_only_blocks_before_hours(self):
        ctx = create_context("user1", "agent1", current_hour=7, business_hours=(9, 17))
        decision = business_hours_only_policy(ctx)
        assert decision.action == ActionType.BLOCK
        assert "business hours" in decision.reason

    def test_business_hours_only_blocks_after_hours(self):
        ctx = create_context("user1", "agent1", current_hour=22, business_hours=(9, 17))
        decision = business_hours_only_policy(ctx)
        assert decision.action == ActionType.BLOCK

    def test_business_hours_only_uses_defaults(self):
        ctx = create_context("user1", "agent1", current_hour=10)
        decision = business_hours_only_policy(ctx)
        assert decision.action == ActionType.ALLOW


class TestAdditionalPolicies:
    """Test suite for additional common policies."""

    def test_rate_limit_policy_blocks_over_limit(self):
        ctx = create_context("user1", "agent1", rate_limit=100, rate_count=105)
        decision = rate_limit_policy(ctx)
        assert decision.action == ActionType.BLOCK
        assert "Rate limit exceeded" in decision.reason

    def test_rate_limit_policy_allows_under_limit(self):
        ctx = create_context("user1", "agent1", rate_limit=100, rate_count=50)
        decision = rate_limit_policy(ctx)
        assert decision.action == ActionType.ALLOW

    def test_block_external_apis_blocks_non_whitelisted(self):
        ctx = create_context(
            "user1",
            "agent1",
            tool_name="call_third_party_api",
            external_api_tools=["call_third_party_api", "fetch_weather"],
            whitelisted_apis=["fetch_weather"],
        )
        decision = block_external_apis_policy(ctx)
        assert decision.action == ActionType.BLOCK
        assert "not whitelisted" in decision.reason

    def test_block_external_apis_allows_whitelisted(self):
        ctx = create_context(
            "user1",
            "agent1",
            tool_name="fetch_weather",
            external_api_tools=["call_third_party_api", "fetch_weather"],
            whitelisted_apis=["fetch_weather"],
        )
        decision = block_external_apis_policy(ctx)
        assert decision.action == ActionType.ALLOW

    def test_require_approval_for_high_cost_pauses_over_threshold(self):
        ctx = create_context(
            "user1", "agent1", operation_cost=25.0, high_cost_threshold=10.0
        )
        decision = require_approval_for_high_cost_policy(ctx)
        assert decision.action == ActionType.PAUSE

    def test_require_approval_for_high_cost_allows_under_threshold(self):
        ctx = create_context(
            "user1", "agent1", operation_cost=5.0, high_cost_threshold=10.0
        )
        decision = require_approval_for_high_cost_policy(ctx)
        assert decision.action == ActionType.ALLOW


class TestPolicyFactories:
    """Test suite for policy factory functions."""

    def test_create_safe_mode_policies_returns_list(self):
        policies = create_safe_mode_policies()
        assert len(policies) == 4
        assert all(callable(p) for p in policies)

    def test_create_audit_mode_policies_returns_list(self):
        policies = create_audit_mode_policies()
        assert len(policies) == 4
        assert all(callable(p) for p in policies)

    def test_create_cost_control_policies_returns_list(self):
        policies = create_cost_control_policies()
        assert len(policies) == 4
        assert all(callable(p) for p in policies)

    def test_create_security_policies_returns_list(self):
        policies = create_security_policies()
        assert len(policies) == 6
        assert all(callable(p) for p in policies)

    def test_create_data_protection_policies_returns_list(self):
        policies = create_data_protection_policies()
        assert len(policies) == 3
        assert all(callable(p) for p in policies)


class TestIntegratedPolicyScenarios:
    """Integration tests for real-world policy scenarios."""

    def test_safe_mode_blocks_dangerous_operations(self):
        ctx = create_context(
            "user1",
            "agent1",
            tool_name="delete_database",
            token_limit=5000,
            tokens_used=3000,
        )

        decision = block_dangerous_tools_policy(ctx)
        assert decision.action == ActionType.BLOCK

    def test_combined_rbac_and_pii_protection(self):
        ctx = create_context(
            "user1",
            "agent1",
            user_role="guest",
            tool_name="fetch_ssn",
            pii_tools=["fetch_ssn"],
            restricted_tools={"guest": ["delete_database"]},
        )

        pii_decision = block_pii_tools_policy(ctx)
        assert pii_decision.action == ActionType.BLOCK

    def test_cost_limits_cascade_properly(self):
        ctx_under_limit = create_context(
            "user1",
            "agent1",
            token_limit=5000,
            tokens_used=3000,
            session_cost_limit=50.0,
            session_cost=40.0,
            daily_cost_limit=1000.0,
            daily_cost=500.0,
        )

        assert token_limit_policy(ctx_under_limit).action == ActionType.ALLOW
        assert session_cost_limit_policy(ctx_under_limit).action == ActionType.ALLOW
        assert daily_cost_limit_policy(ctx_under_limit).action == ActionType.ALLOW

        ctx_over_limit = create_context(
            "user1", "agent1", daily_cost_limit=1000.0, daily_cost=1500.0
        )

        assert daily_cost_limit_policy(ctx_over_limit).action == ActionType.BLOCK


class TestSystemLoadPolicy:
    @patch("psutil.cpu_percent", return_value=50.0)
    @patch(
        "psutil.virtual_memory",
        return_value=type("obj", (object,), {"percent": 70.0})(),
    )
    def test_system_ok(self, mock_mem, mock_cpu):
        """Test that the policy allows action when system load is normal."""
        from clearstone.policies.common import system_load_policy

        ctx = create_context("user", "agent")
        decision = system_load_policy(ctx)
        assert decision.action == ActionType.ALLOW

    @patch("psutil.cpu_percent", return_value=95.0)
    @patch(
        "psutil.virtual_memory",
        return_value=type("obj", (object,), {"percent": 70.0})(),
    )
    def test_high_cpu_blocks(self, mock_mem, mock_cpu):
        """Test that the policy blocks when CPU load is too high."""
        from clearstone.policies.common import system_load_policy

        ctx = create_context("user", "agent")
        decision = system_load_policy(ctx)
        assert decision.action == ActionType.BLOCK
        assert "CPU load is critical" in decision.reason

    @patch("psutil.cpu_percent", return_value=50.0)
    @patch(
        "psutil.virtual_memory",
        return_value=type("obj", (object,), {"percent": 98.0})(),
    )
    def test_high_memory_blocks(self, mock_mem, mock_cpu):
        """Test that the policy blocks when memory usage is too high."""
        from clearstone.policies.common import system_load_policy

        ctx = create_context("user", "agent")
        decision = system_load_policy(ctx)
        assert decision.action == ActionType.BLOCK
        assert "System memory usage is critical" in decision.reason

    @patch("psutil.cpu_percent", return_value=85.0)
    @patch(
        "psutil.virtual_memory",
        return_value=type("obj", (object,), {"percent": 70.0})(),
    )
    def test_custom_cpu_threshold(self, mock_cpu, mock_mem):
        """Test that a custom CPU threshold in context is respected."""
        from clearstone.policies.common import system_load_policy

        ctx_low_threshold = create_context("user", "agent", cpu_threshold_percent=80.0)
        decision = system_load_policy(ctx_low_threshold)
        assert decision.action == ActionType.BLOCK


class TestModelHealthCheckPolicy:
    @patch("requests.head")
    def test_healthy_server_allows(self, mock_head):
        """Test that a healthy server allows the action."""
        mock_head.return_value.status_code = 200
        from clearstone.policies.common import model_health_check_policy

        ctx = create_context("user", "agent")
        decision = model_health_check_policy(ctx)
        assert decision.action == ActionType.ALLOW
        mock_head.assert_called_once()

    @patch("requests.head")
    def test_unhealthy_server_blocks(self, mock_head):
        """Test that an unhealthy server (non-200 status) blocks."""
        mock_head.return_value.status_code = 503
        from clearstone.policies.common import model_health_check_policy

        ctx = create_context("user", "agent")
        decision = model_health_check_policy(ctx)
        assert decision.action == ActionType.BLOCK
        assert "unhealthy" in decision.reason.lower()
        assert "503" in decision.reason

    @patch("requests.head")
    def test_unreachable_server_blocks(self, mock_head):
        """Test that an unreachable server blocks."""
        import requests

        mock_head.side_effect = requests.exceptions.ConnectionError(
            "Connection refused"
        )
        from clearstone.policies.common import model_health_check_policy

        ctx = create_context("user", "agent")
        decision = model_health_check_policy(ctx)
        assert decision.action == ActionType.BLOCK
        assert "unreachable" in decision.reason.lower()

    @patch("requests.head")
    def test_timeout_blocks(self, mock_head):
        """Test that a timeout blocks."""
        import requests

        mock_head.side_effect = requests.exceptions.Timeout("Request timed out")
        from clearstone.policies.common import model_health_check_policy

        ctx = create_context("user", "agent")
        decision = model_health_check_policy(ctx)
        assert decision.action == ActionType.BLOCK
        assert "unreachable" in decision.reason.lower()

    @patch("requests.head")
    def test_custom_health_url(self, mock_head):
        """Test that a custom health check URL is used."""
        mock_head.return_value.status_code = 200
        from clearstone.policies.common import model_health_check_policy

        custom_url = "http://localhost:8080/health"
        ctx = create_context("user", "agent", local_model_health_url=custom_url)
        decision = model_health_check_policy(ctx)
        assert decision.action == ActionType.ALLOW
        mock_head.assert_called_with(custom_url, timeout=0.5)

    @patch("requests.head")
    def test_custom_timeout(self, mock_head):
        """Test that a custom timeout is respected."""
        mock_head.return_value.status_code = 200
        from clearstone.policies.common import model_health_check_policy

        ctx = create_context("user", "agent", health_check_timeout=2.0)
        decision = model_health_check_policy(ctx)
        assert decision.action == ActionType.ALLOW
        assert mock_head.call_args[1]["timeout"] == 2.0
