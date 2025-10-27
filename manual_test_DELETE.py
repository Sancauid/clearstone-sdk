# manual_test.py

import sys
from typing import List, Any
from langchain_core.callbacks.manager import CallbackManager

# --- Import everything we need from our SDK ---
from clearstone.core.actions import ALLOW, BLOCK, ALERT, Decision, ActionType
from clearstone.core.context import create_context, context_scope
from clearstone.core.policy import Policy, PolicyEngine, reset_policies
from clearstone.integrations.langchain.callbacks import (
    PolicyCallbackHandler,
    PolicyViolationError,
)

# ==============================================================================
# 1. DEFINE YOUR POLICIES
# These functions are automatically discovered by the PolicyEngine.
# ==============================================================================
reset_policies()


@Policy(name="security_block_dangerous_tools_for_guests", priority=100)
def block_dangerous_tools(context):
    """
    A high-priority security policy.
    It checks if a user with the 'guest' role is trying to use a destructive tool.
    """
    role = context.metadata.get("role")
    tool_name = context.metadata.get("tool_name")

    # This is the core policy logic
    if role == "guest" and tool_name == "delete_files":
        return BLOCK(
            f"Role '{role}' is not authorized to use the dangerous tool '{tool_name}'."
        )

    # If the condition isn't met, this policy allows the action.
    return ALLOW


@Policy(name="monitoring_alert_on_large_text", priority=50)
def alert_on_large_text(context):
    """
    A medium-priority monitoring policy.
    It creates an ALERT if a tool is called with a very large text input.
    """
    tool_input = context.metadata.get("tool_input", "")

    if context.metadata.get("event_type") == "on_tool_start" and len(tool_input) > 100:
        return Decision(
            action=ActionType.ALERT,
            reason=f"Large input detected ({len(tool_input)} characters).",
        )

    return ALLOW


# ==============================================================================
# 2. SETUP THE ENGINE AND A (SIMULATED) LANGCHAIN AGENT
# ==============================================================================

# The PolicyEngine automatically finds all functions decorated with @Policy
try:
    POLICY_ENGINE = PolicyEngine()
    # The handler is the bridge between LangChain and our engine
    POLICY_HANDLER = PolicyCallbackHandler(POLICY_ENGINE)
except ValueError as e:
    print(f"Error initializing PolicyEngine: {e}")
    sys.exit(1)


def run_simulated_agent_tool(tool_name: str, tool_input: str, callbacks: List[Any]):
    """
    This function simulates a LangChain agent executing a tool.
    It manually triggers the on_tool_start event to run our policies.
    """
    print(f"Agent is attempting to run tool '{tool_name}'...")

    try:
        # Call the handler directly to properly catch exceptions in our test
        for handler in callbacks:
            handler.on_tool_start(serialized={"name": tool_name}, input_str=tool_input)

        # If no exception was raised, the tool execution is allowed to proceed.
        print(f"✅ SUCCESS: Policy check passed. Executing tool '{tool_name}'.\n")

    except PolicyViolationError as e:
        # Our handler raises this specific error if a policy returns BLOCK.
        print(f"❌ BLOCKED: {e}\n")
    except Exception as e:
        # Catch any other unexpected errors.
        print(f"🔥 UNEXPECTED ERROR: {e}\n")


# ==============================================================================
# 3. RUN YOUR SCENARIOS
# ==============================================================================

if __name__ == "__main__":
    print("--- Running Manual Test Scenarios for Clearstone SDK ---\n")

    # --- SCENARIO 1: A GUEST TRIES TO USE A DANGEROUS TOOL ---
    # EXPECTATION: The 'security_block_dangerous_tools_for_guests' policy should
    #              return BLOCK, and the handler should raise a PolicyViolationError.
    print("--- SCENARIO 1: Guest tries to delete files (should be BLOCKED) ---")
    guest_context = create_context(
        user_id="user-guest-789",
        agent_id="file-manager-agent",
        session_id="session-alpha",
        role="guest",  # The critical piece of metadata for our policy
    )
    # The `with context_scope(...)` block makes the context available to the handler
    with context_scope(guest_context):
        run_simulated_agent_tool(
            tool_name="delete_files",
            tool_input="/path/to/important/data",
            callbacks=[POLICY_HANDLER],
        )

    # --- SCENARIO 2: AN ADMIN USES A TOOL WITH A VERY LARGE INPUT ---
    # EXPECTATION: The security policy should ALLOW it. The monitoring policy should
    #              return an ALERT. The final decision is ALERT, which is non-blocking.
    #              The tool should execute successfully.
    print("--- SCENARIO 2: Admin summarizes large text (should ALERT but SUCCEED) ---")
    admin_context = create_context(
        user_id="user-admin-123",
        agent_id="research-agent",
        session_id="session-beta",
        role="admin",
    )
    large_text = (
        "This is a very long string designed to be over 100 characters to trigger our monitoring policy..."
        * 3
    )
    with context_scope(admin_context):
        run_simulated_agent_tool(
            tool_name="summarize_text",
            tool_input=large_text,
            callbacks=[POLICY_HANDLER],
        )

    # --- 4. INSPECT THE AUDIT TRAIL ---
    print("--- FINAL AUDIT TRAIL ---")
    # The audit trail contains a record of every single policy evaluation
    audit_trail = POLICY_ENGINE.get_audit_trail()
    for i, entry in enumerate(audit_trail):
        print(
            f"{i+1}. Policy '{entry['policy_name']}' ran for user '{entry['user_id']}'. Decision: {entry['decision']}."
        )
