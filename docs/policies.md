# Pre-Built Policy Library

Clearstone provides 17+ production-ready policies for common governance scenarios. Import them from `clearstone.policies.common` and use them immediately.

## Cost Control Policies

### token_limit_policy

Block execution if token usage exceeds a threshold.

**Priority:** 100

**Metadata Required:**
- `token_limit`: Maximum tokens allowed (int)
- `tokens_used`: Current tokens consumed (int, defaults to 0)

**Example:**
```python
from clearstone import create_context, PolicyEngine
from clearstone.policies.common import token_limit_policy

engine = PolicyEngine()

context = create_context(
    "user_123", "agent_1",
    metadata={"token_limit": 5000, "tokens_used": 6000}
)

decision = engine.evaluate(context)
```

---

### session_cost_limit_policy

Alert if session cost exceeds a threshold.

**Priority:** 100

**Metadata Required:**
- `session_cost_limit`: Maximum session cost in dollars (float)
- `session_cost`: Current session cost in dollars (float, defaults to 0)

**Example:**
```python
context = create_context(
    "user_123", "agent_1",
    metadata={"session_cost_limit": 50.0, "session_cost": 55.0}
)
```

---

### daily_cost_limit_policy

Block execution if daily cost exceeds a threshold.

**Priority:** 100

**Metadata Required:**
- `daily_cost_limit`: Maximum daily cost in dollars (float)
- `daily_cost`: Current daily cost in dollars (float, defaults to 0)

**Example:**
```python
context = create_context(
    "user_123", "agent_1",
    metadata={"daily_cost_limit": 1000.0, "daily_cost": 1250.0}
)
```

---

### require_approval_for_high_cost_policy

Pause for human approval if operation cost exceeds threshold.

**Priority:** 90

**Metadata Required:**
- `operation_cost`: Estimated cost of operation (float)
- `high_cost_threshold`: Cost threshold requiring approval (float, defaults to 10.0)

**Example:**
```python
context = create_context(
    "user_123", "agent_1",
    metadata={"operation_cost": 25.0, "high_cost_threshold": 10.0}
)
```

---

## Access Control Policies

### rbac_tool_access_policy

Block tool access based on user role.

**Priority:** 90

**Metadata Required:**
- `user_role`: User's role (str, defaults to "guest")
- `tool_name`: Name of the tool being called (str)
- `restricted_tools`: Dict mapping roles to forbidden tools (dict)

**Example:**
```python
context = create_context(
    "user_123", "agent_1",
    metadata={
        "user_role": "guest",
        "tool_name": "delete_database",
        "restricted_tools": {
            "guest": ["delete_database", "admin_panel"],
            "user": ["admin_panel"]
        }
    }
)
```

---

### admin_only_action_policy

Block execution unless user is admin.

**Priority:** 95

**Metadata Required:**
- `user_role`: User's role (str, defaults to "guest")
- `tool_name`: Name of the tool being called (str)
- `require_admin_for`: List of tool names requiring admin role (list)

**Example:**
```python
context = create_context(
    "user_123", "agent_1",
    metadata={
        "user_role": "user",
        "tool_name": "delete_all_users",
        "require_admin_for": ["delete_all_users", "export_database"]
    }
)
```

---

## Data Protection Policies

### redact_pii_policy

Redact PII fields from outputs automatically.

**Priority:** 85

**Metadata Required:**
- `tool_name`: Name of tool being called (str)
- `pii_fields`: Dict mapping tool names to fields to redact (dict)

**Example:**
```python
context = create_context(
    "user_123", "agent_1",
    metadata={
        "tool_name": "fetch_user_data",
        "pii_fields": {
            "fetch_user_data": ["ssn", "credit_card", "email"],
            "get_medical_records": ["diagnosis", "prescription"]
        }
    }
)
```

---

### block_pii_tools_policy

Block access to PII-sensitive tools for non-privileged users.

**Priority:** 90

**Metadata Required:**
- `user_role`: User's role (str, defaults to "guest")
- `tool_name`: Tool being called (str)
- `pii_tools`: List of PII-sensitive tool names (list)

**Example:**
```python
context = create_context(
    "user_123", "agent_1",
    metadata={
        "user_role": "guest",
        "tool_name": "fetch_ssn",
        "pii_tools": ["fetch_ssn", "get_credit_card", "view_medical_records"]
    }
)
```

---

## Safety Policies

### block_dangerous_tools_policy

Block inherently dangerous tools (delete, drop, truncate, etc).

**Priority:** 100

**Metadata Required:**
- `tool_name`: Name of tool being called (str)

**Dangerous Operations Blocked:**
- delete_database
- drop_table
- truncate
- format_drive
- shutdown
- restart
- hard_delete
- purge
- destroy

**Example:**
```python
context = create_context(
    "user_123", "agent_1",
    metadata={"tool_name": "drop_table"}
)
```

---

### pause_before_write_policy

Pause (for manual review) before any write/delete operation.

**Priority:** 80

**Metadata Required:**
- `tool_name`: Name of tool (str)
- `require_pause_for`: List of write operations requiring pause (list)

**Example:**
```python
context = create_context(
    "user_123", "agent_1",
    metadata={
        "tool_name": "delete_user",
        "require_pause_for": ["create", "update", "delete", "modify"]
    }
)
```

---

## Security Policies

### alert_on_privileged_access_policy

Alert security team when privileged tools are accessed.

**Priority:** 75

**Metadata Required:**
- `tool_name`: Name of tool (str)
- `privileged_tools`: List of privileged tools to alert on (list)
- `user_id`: User performing the action (str, from context)

**Example:**
```python
context = create_context(
    "user_123", "agent_1",
    metadata={
        "tool_name": "export_all_data",
        "privileged_tools": ["export_all_data", "admin_console", "grant_permissions"]
    }
)
```

---

### alert_on_failed_auth_policy

Alert on suspicious authentication failures.

**Priority:** 100

**Metadata Required:**
- `auth_failed`: Boolean indicating auth failure (bool)
- `user_id`: User ID (str, from context)
- `attempt_count`: Number of failed attempts (int, defaults to 1)

**Example:**
```python
context = create_context(
    "user_123", "agent_1",
    metadata={"auth_failed": True, "attempt_count": 5}
)
```

---

## Rate Limiting Policies

### rate_limit_policy

Block execution if rate limit is exceeded.

**Priority:** 95

**Metadata Required:**
- `rate_limit`: Maximum requests allowed in time window (int)
- `rate_count`: Current request count (int)

**Example:**
```python
context = create_context(
    "user_123", "agent_1",
    metadata={"rate_limit": 100, "rate_count": 105}
)
```

---

### business_hours_only_policy

Block execution outside of business hours.

**Priority:** 70

**Metadata Required:**
- `current_hour`: Current hour 0-23 (int, optional - defaults to current time)
- `business_hours`: Tuple of (start_hour, end_hour) (tuple, defaults to (9, 17))

**Example:**
```python
context = create_context(
    "user_123", "agent_1",
    metadata={"current_hour": 22, "business_hours": (9, 17)}
)
```

---

### block_external_apis_policy

Block calls to external APIs that are not whitelisted.

**Priority:** 85

**Metadata Required:**
- `tool_name`: Name of tool being called (str)
- `external_api_tools`: List of tools that call external APIs (list)
- `whitelisted_apis`: List of allowed external API tools (list, defaults to [])

**Example:**
```python
context = create_context(
    "user_123", "agent_1",
    metadata={
        "tool_name": "call_third_party_api",
        "external_api_tools": ["call_third_party_api", "fetch_weather"],
        "whitelisted_apis": ["fetch_weather"]
    }
)
```

---

## Local System Policies

These policies are specifically designed for users running local LLMs.

### system_load_policy

Blocks new, intensive actions if the local system's CPU or memory is overloaded.

**Priority:** 200 (Highest - Critical for system stability)

**Metadata Required:**
- `cpu_threshold_percent`: CPU usage percent to trigger block (optional, default 90)
- `memory_threshold_percent`: Memory usage percent to trigger block (optional, default 95)

**Example:**
```python
context = create_context(
    "user_123", "agent_1",
    metadata={
        "cpu_threshold_percent": 85.0,
        "memory_threshold_percent": 90.0
    }
)
```

**Why This Matters:**
Prevents system freezes when running resource-intensive local LLMs (Ollama, LM Studio, etc).

---

### model_health_check_policy

Performs a quick health check on a local model server endpoint before allowing an LLM call.

**Priority:** 190

**Metadata Required:**
- `local_model_health_url`: Health check endpoint URL (optional, default: "http://localhost:11434/api/tags")
- `health_check_timeout`: Timeout in seconds (optional, default: 0.5)

**Example:**
```python
context = create_context(
    "user_123", "agent_1",
    metadata={
        "local_model_health_url": "http://localhost:11434/api/tags",
        "health_check_timeout": 1.0
    }
)
```

**Why This Matters:**
Provides instant feedback when your local model server is down, avoiding mysterious 60-second timeout errors.

---

## Policy Sets

Pre-configured policy combinations for common use cases.

### create_safe_mode_policies()

Conservative execution mode for production environments.

**Includes:**
- block_dangerous_tools_policy
- pause_before_write_policy
- token_limit_policy
- alert_on_privileged_access_policy

**Example:**
```python
from clearstone import PolicyEngine
from clearstone.policies.common import create_safe_mode_policies

engine = PolicyEngine()

for policy in create_safe_mode_policies():
    engine.register_policy(policy)
```

---

### create_audit_mode_policies()

Full audit logging for compliance.

**Includes:**
- alert_on_privileged_access_policy
- alert_on_failed_auth_policy
- rbac_tool_access_policy
- rate_limit_policy

**Example:**
```python
from clearstone.policies.common import create_audit_mode_policies

for policy in create_audit_mode_policies():
    engine.register_policy(policy)
```

---

### create_cost_control_policies()

Strict cost control for budget management.

**Includes:**
- token_limit_policy
- session_cost_limit_policy
- daily_cost_limit_policy
- require_approval_for_high_cost_policy

**Example:**
```python
from clearstone.policies.common import create_cost_control_policies

for policy in create_cost_control_policies():
    engine.register_policy(policy)
```

---

### create_security_policies()

Comprehensive security enforcement.

**Includes:**
- rbac_tool_access_policy
- admin_only_action_policy
- block_pii_tools_policy
- alert_on_failed_auth_policy
- alert_on_privileged_access_policy
- block_dangerous_tools_policy

**Example:**
```python
from clearstone.policies.common import create_security_policies

for policy in create_security_policies():
    engine.register_policy(policy)
```

---

### create_data_protection_policies()

Sensitive data protection.

**Includes:**
- redact_pii_policy
- block_pii_tools_policy
- admin_only_action_policy

**Example:**
```python
from clearstone.policies.common import create_data_protection_policies

for policy in create_data_protection_policies():
    engine.register_policy(policy)
```

---

## Using Pre-Built Policies

### Option 1: Import and Register

```python
from clearstone import PolicyEngine
from clearstone.policies.common import token_limit_policy, cost_limit_policy

engine = PolicyEngine()
```

Policies are automatically registered when imported.

### Option 2: Use Policy Sets

```python
from clearstone import PolicyEngine
from clearstone.policies.common import create_security_policies

engine = PolicyEngine()

for policy in create_security_policies():
    pass
```

### Option 3: Compose Policies

```python
from clearstone import compose_and
from clearstone.policies.common import token_limit_policy, cost_limit_policy

combined = compose_and(token_limit_policy, cost_limit_policy)
```

## Customizing Pre-Built Policies

You can extend or modify pre-built policies:

```python
from clearstone import Policy, BLOCK, ALLOW
from clearstone.policies.common import token_limit_policy

@Policy(name="custom_token_limit", priority=100)
def custom_token_limit(context):
    result = token_limit_policy(context)
    
    if result.action == "BLOCK":
        return BLOCK(f"[CUSTOM] {result.reason}")
    
    return result
```

## Next Steps

- **[Governance Guide](guide/governance.md)**: Learn to write your own policies
- **[Getting Started](getting-started.md)**: See policies in action
- **[API Reference](api/governance.md)**: Complete API documentation

