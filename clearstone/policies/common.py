"""
Pre-built policy library for common governance scenarios.

This module provides battle-tested policies for:
- Token & Cost Control
- Role-Based Access Control (RBAC)
- PII & Sensitive Data Protection
- Dangerous Operation Prevention
- Security Alerts
- Time-Based Restrictions
"""

from typing import List, Tuple, Callable
from datetime import datetime
from clearstone.core.policy import Policy, PolicyInfo
from clearstone.core.context import PolicyContext
from clearstone.core.actions import Decision, ALLOW, BLOCK, PAUSE, ALERT, REDACT


@Policy(name="token_limit", priority=100)
def token_limit_policy(context: PolicyContext) -> Decision:
    """
    Block execution if token usage exceeds a threshold.

    Metadata required:
        - token_limit: Maximum tokens allowed (int)
        - tokens_used: Current tokens consumed (int, defaults to 0)

    Example:
        metadata = {
            "token_limit": 5000,
            "tokens_used": 6000
        }
    """
    limit = context.metadata.get("token_limit")
    tokens = context.metadata.get("tokens_used", 0)

    if limit is not None and tokens > limit:
        return BLOCK(f"Token limit exceeded: {tokens} > {limit}")
    return ALLOW


@Policy(name="session_cost_limit", priority=100)
def session_cost_limit_policy(context: PolicyContext) -> Decision:
    """
    Alert if session cost exceeds a threshold.

    Metadata required:
        - session_cost_limit: Maximum session cost in dollars (float)
        - session_cost: Current session cost in dollars (float, defaults to 0)

    Example:
        metadata = {
            "session_cost_limit": 50.0,
            "session_cost": 55.0
        }
    """
    limit = context.metadata.get("session_cost_limit")
    cost = context.metadata.get("session_cost", 0.0)

    if limit is not None and cost > limit:
        return ALERT
    return ALLOW


@Policy(name="daily_cost_limit", priority=100)
def daily_cost_limit_policy(context: PolicyContext) -> Decision:
    """
    Block execution if daily cost exceeds a threshold.

    Metadata required:
        - daily_cost_limit: Maximum daily cost in dollars (float)
        - daily_cost: Current daily cost in dollars (float, defaults to 0)

    Example:
        metadata = {
            "daily_cost_limit": 1000.0,
            "daily_cost": 1250.0
        }
    """
    limit = context.metadata.get("daily_cost_limit")
    cost = context.metadata.get("daily_cost", 0.0)

    if limit is not None and cost > limit:
        return BLOCK(f"Daily cost limit exceeded: ${cost:.2f} > ${limit:.2f}")
    return ALLOW


@Policy(name="rbac_tool_access", priority=90)
def rbac_tool_access_policy(context: PolicyContext) -> Decision:
    """
    Block tool access based on user role.

    Metadata required:
        - user_role: User's role (str, defaults to "guest")
        - tool_name: Name of the tool being called (str)
        - restricted_tools: Dict mapping roles to forbidden tools (dict)

    Example:
        metadata = {
            "user_role": "guest",
            "tool_name": "delete_database",
            "restricted_tools": {
                "guest": ["delete_database", "admin_panel"],
                "user": ["admin_panel"]
            }
        }
    """
    user_role = context.metadata.get("user_role", "guest")
    tool_name = context.metadata.get("tool_name", "")
    restricted = context.metadata.get("restricted_tools", {})

    forbidden = restricted.get(user_role, [])

    if tool_name in forbidden:
        return BLOCK(f"Role '{user_role}' cannot access tool '{tool_name}'")
    return ALLOW


@Policy(name="admin_only_action", priority=95)
def admin_only_action_policy(context: PolicyContext) -> Decision:
    """
    Block execution unless user is admin.

    Metadata required:
        - user_role: User's role (str, defaults to "guest")
        - tool_name: Name of the tool being called (str)
        - require_admin_for: List of tool names requiring admin role (list)

    Example:
        metadata = {
            "user_role": "user",
            "tool_name": "delete_all_users",
            "require_admin_for": ["delete_all_users", "export_database"]
        }
    """
    user_role = context.metadata.get("user_role", "guest")
    tool_name = context.metadata.get("tool_name", "")
    require_admin = context.metadata.get("require_admin_for", [])

    if tool_name in require_admin and user_role != "admin":
        return BLOCK(
            f"Admin role required for '{tool_name}'. Current role: '{user_role}'"
        )
    return ALLOW


@Policy(name="redact_pii", priority=85)
def redact_pii_policy(context: PolicyContext) -> Decision:
    """
    Redact PII fields from outputs automatically.

    Metadata required:
        - tool_name: Name of tool being called (str)
        - pii_fields: Dict mapping tool names to fields to redact (dict)

    Example:
        metadata = {
            "tool_name": "fetch_user_data",
            "pii_fields": {
                "fetch_user_data": ["ssn", "credit_card", "email"],
                "get_medical_records": ["diagnosis", "prescription"]
            }
        }
    """
    tool_name = context.metadata.get("tool_name", "")
    pii_config = context.metadata.get("pii_fields", {})

    if tool_name in pii_config:
        fields = pii_config[tool_name]
        return REDACT(reason=f"PII redaction for tool '{tool_name}'", fields=fields)
    return ALLOW


@Policy(name="block_pii_tools", priority=90)
def block_pii_tools_policy(context: PolicyContext) -> Decision:
    """
    Block access to PII-sensitive tools for non-privileged users.

    Metadata required:
        - user_role: User's role (str, defaults to "guest")
        - tool_name: Tool being called (str)
        - pii_tools: List of PII-sensitive tool names (list)

    Example:
        metadata = {
            "user_role": "guest",
            "tool_name": "fetch_ssn",
            "pii_tools": ["fetch_ssn", "get_credit_card", "view_medical_records"]
        }
    """
    user_role = context.metadata.get("user_role", "guest")
    tool_name = context.metadata.get("tool_name", "")
    pii_tools = context.metadata.get("pii_tools", [])

    if tool_name in pii_tools and user_role not in ["admin", "data_engineer"]:
        return BLOCK(f"PII access denied for role '{user_role}'")
    return ALLOW


@Policy(name="block_dangerous_tools", priority=100)
def block_dangerous_tools_policy(context: PolicyContext) -> Decision:
    """
    Block inherently dangerous tools (delete, drop, truncate, etc).

    Metadata required:
        - tool_name: Name of tool being called (str)

    Example:
        metadata = {
            "tool_name": "drop_table"
        }
    """
    dangerous = [
        "delete_database",
        "drop_table",
        "truncate",
        "format_drive",
        "shutdown",
        "restart",
        "hard_delete",
        "purge",
        "destroy",
    ]

    tool_name = context.metadata.get("tool_name", "").lower()

    if any(d in tool_name for d in dangerous):
        return BLOCK(f"Dangerous tool blocked: '{tool_name}'")
    return ALLOW


@Policy(name="pause_before_write", priority=80)
def pause_before_write_policy(context: PolicyContext) -> Decision:
    """
    Pause (for manual review) before any write/delete operation.

    Metadata required:
        - tool_name: Name of tool (str)
        - require_pause_for: List of write operations requiring pause (list)

    Example:
        metadata = {
            "tool_name": "delete_user",
            "require_pause_for": ["create", "update", "delete", "modify"]
        }
    """
    tool_name = context.metadata.get("tool_name", "").lower()
    require_pause = context.metadata.get("require_pause_for", [])

    if any(action in tool_name for action in require_pause):
        return PAUSE(f"Manual review required for write operation: '{tool_name}'")

    return ALLOW


@Policy(name="alert_on_privileged_access", priority=75)
def alert_on_privileged_access_policy(context: PolicyContext) -> Decision:
    """
    Alert security team when privileged tools are accessed.

    Metadata required:
        - tool_name: Name of tool (str)
        - privileged_tools: List of privileged tools to alert on (list)
        - user_id: User performing the action (str, from context)

    Example:
        metadata = {
            "tool_name": "export_all_data",
            "privileged_tools": ["export_all_data", "admin_console", "grant_permissions"]
        }
    """
    tool_name = context.metadata.get("tool_name", "")
    privileged = context.metadata.get("privileged_tools", [])
    user_id = context.user_id

    if tool_name in privileged:
        return ALERT
    return ALLOW


@Policy(name="alert_on_failed_auth", priority=100)
def alert_on_failed_auth_policy(context: PolicyContext) -> Decision:
    """
    Alert on suspicious authentication failures.

    Metadata required:
        - auth_failed: Boolean indicating auth failure (bool)
        - user_id: User ID (str, from context)
        - attempt_count: Number of failed attempts (int, defaults to 1)

    Example:
        metadata = {
            "auth_failed": True,
            "attempt_count": 5
        }
    """
    if context.metadata.get("auth_failed"):
        attempts = context.metadata.get("attempt_count", 1)
        user_id = context.user_id

        if attempts > 3:
            return ALERT

    return ALLOW


@Policy(name="business_hours_only", priority=70)
def business_hours_only_policy(context: PolicyContext) -> Decision:
    """
    Block execution outside of business hours.

    Metadata required:
        - current_hour: Current hour 0-23 (int, optional - defaults to current time)
        - business_hours: Tuple of (start_hour, end_hour) (tuple, defaults to (9, 17))

    Example:
        metadata = {
            "current_hour": 22,
            "business_hours": (9, 17)
        }
    """
    current_hour = context.metadata.get("current_hour")
    if current_hour is None:
        current_hour = datetime.now().hour

    business_hours = context.metadata.get("business_hours", (9, 17))
    start, end = business_hours

    if not (start <= current_hour < end):
        return BLOCK(
            f"Operation only allowed during business hours ({start}:00-{end}:00)"
        )

    return ALLOW


@Policy(name="rate_limit", priority=95)
def rate_limit_policy(context: PolicyContext) -> Decision:
    """
    Block execution if rate limit is exceeded.

    Metadata required:
        - rate_limit: Maximum requests allowed in time window (int)
        - rate_count: Current request count (int)

    Example:
        metadata = {
            "rate_limit": 100,
            "rate_count": 105
        }
    """
    limit = context.metadata.get("rate_limit")
    count = context.metadata.get("rate_count", 0)

    if limit is not None and count > limit:
        return BLOCK(f"Rate limit exceeded: {count} > {limit}")
    return ALLOW


@Policy(name="block_external_apis", priority=85)
def block_external_apis_policy(context: PolicyContext) -> Decision:
    """
    Block calls to external APIs that are not whitelisted.

    Metadata required:
        - tool_name: Name of tool being called (str)
        - external_api_tools: List of tools that call external APIs (list)
        - whitelisted_apis: List of allowed external API tools (list, defaults to [])

    Example:
        metadata = {
            "tool_name": "call_third_party_api",
            "external_api_tools": ["call_third_party_api", "fetch_weather"],
            "whitelisted_apis": ["fetch_weather"]
        }
    """
    tool_name = context.metadata.get("tool_name", "")
    external_tools = context.metadata.get("external_api_tools", [])
    whitelist = context.metadata.get("whitelisted_apis", [])

    if tool_name in external_tools and tool_name not in whitelist:
        return BLOCK(f"External API call blocked: '{tool_name}' is not whitelisted")
    return ALLOW


@Policy(name="require_approval_for_high_cost", priority=90)
def require_approval_for_high_cost_policy(context: PolicyContext) -> Decision:
    """
    Pause for approval if operation cost exceeds threshold.

    Metadata required:
        - operation_cost: Estimated cost of operation (float)
        - high_cost_threshold: Cost threshold requiring approval (float, defaults to 10.0)

    Example:
        metadata = {
            "operation_cost": 25.0,
            "high_cost_threshold": 10.0
        }
    """
    cost = context.metadata.get("operation_cost", 0.0)
    threshold = context.metadata.get("high_cost_threshold", 10.0)

    if cost > threshold:
        return PAUSE(
            f"High cost operation requires approval: ${cost:.2f} > ${threshold:.2f}"
        )

    return ALLOW


def create_safe_mode_policies() -> List[Callable]:
    """
    Create a set of policies for 'safe mode' (conservative execution).

    Combines:
    - Block dangerous tools
    - Pause before writes
    - Token limits
    - Alert on privileged access

    Returns:
        List of policy functions ready to be used
    """
    return [
        block_dangerous_tools_policy,
        pause_before_write_policy,
        token_limit_policy,
        alert_on_privileged_access_policy,
    ]


def create_audit_mode_policies() -> List[Callable]:
    """
    Create policies for full audit logging.

    Combines:
    - Alert on all privileged access
    - Alert on failed auth
    - RBAC enforcement
    - Rate limiting

    Returns:
        List of policy functions
    """
    return [
        alert_on_privileged_access_policy,
        alert_on_failed_auth_policy,
        rbac_tool_access_policy,
        rate_limit_policy,
    ]


def create_cost_control_policies() -> List[Callable]:
    """
    Create policies for strict cost control.

    Combines:
    - Token limits
    - Session cost limits
    - Daily cost limits
    - High cost approval

    Returns:
        List of policy functions
    """
    return [
        token_limit_policy,
        session_cost_limit_policy,
        daily_cost_limit_policy,
        require_approval_for_high_cost_policy,
    ]


def create_security_policies() -> List[Callable]:
    """
    Create comprehensive security policies.

    Combines:
    - RBAC
    - Admin-only actions
    - Block PII tools
    - Alert on failed auth
    - Alert on privileged access
    - Block dangerous tools

    Returns:
        List of policy functions
    """
    return [
        rbac_tool_access_policy,
        admin_only_action_policy,
        block_pii_tools_policy,
        alert_on_failed_auth_policy,
        alert_on_privileged_access_policy,
        block_dangerous_tools_policy,
    ]


def create_data_protection_policies() -> List[Callable]:
    """
    Create policies for sensitive data protection.

    Combines:
    - PII redaction
    - Block PII tools for non-privileged users
    - Admin-only access to sensitive data

    Returns:
        List of policy functions
    """
    return [
        redact_pii_policy,
        block_pii_tools_policy,
        admin_only_action_policy,
    ]
