"""
Example: LangChain Integration with Policy Enforcement

This example demonstrates how to integrate Clearstone policies with LangChain
agents using the PolicyCallbackHandler.
"""

from clearstone import ALLOW, BLOCK, Policy, PolicyEngine, context_scope, create_context
from clearstone.integrations.langchain import (
    PolicyCallbackHandler,
    PolicyViolationError,
)


@Policy(name="block_dangerous_tools", priority=100)
def block_dangerous_tools(context):
    """Block execution of potentially dangerous tools."""
    tool_name = context.metadata.get("tool_name")

    dangerous_tools = ["shell", "terminal", "file_delete", "system_command"]

    if tool_name and any(danger in tool_name.lower() for danger in dangerous_tools):
        return BLOCK(f"Tool '{tool_name}' is not allowed for security reasons.")

    return ALLOW


@Policy(name="require_approval_for_external_apis", priority=50)
def require_approval_for_external_apis(context):
    """Require manual approval for external API calls."""
    tool_name = context.metadata.get("tool_name")

    if tool_name and "api" in tool_name.lower():
        user_role = context.metadata.get("role", "guest")
        if user_role != "admin":
            return BLOCK(
                f"External API access requires admin role. Current role: {user_role}"
            )

    return ALLOW


def mock_langchain_agent_run():
    """
    Simulates a LangChain agent execution with policy enforcement.

    In a real scenario, you would:
    1. Create your LangChain agent
    2. Instantiate the PolicyCallbackHandler
    3. Pass it to your agent's run() method via callbacks parameter
    """

    engine = PolicyEngine()
    handler = PolicyCallbackHandler(engine)

    ctx = create_context(user_id="user-123", agent_id="research-assistant", role="user")

    print("=== Simulating LangChain Agent with Policy Enforcement ===\n")

    with context_scope(ctx):
        print("1. Testing allowed tool (calculator)...")
        try:
            handler.on_tool_start(serialized={"name": "calculator"}, input_str="2 + 2")
            print("   ✅ Calculator tool allowed\n")
        except PolicyViolationError as e:
            print(f"   ❌ Blocked: {e}\n")

        print("2. Testing dangerous tool (shell)...")
        try:
            handler.on_tool_start(
                serialized={"name": "shell_executor"}, input_str="rm -rf /"
            )
            print("   ✅ Shell tool allowed\n")
        except PolicyViolationError as e:
            print(f"   ❌ Blocked: {e.decision.reason}\n")

        print("3. Testing external API (non-admin user)...")
        try:
            handler.on_tool_start(
                serialized={"name": "external_api_client"},
                input_str="GET https://api.example.com/data",
            )
            print("   ✅ External API allowed\n")
        except PolicyViolationError as e:
            print(f"   ❌ Blocked: {e.decision.reason}\n")

        print("4. Testing LLM call...")
        try:
            handler.on_llm_start(
                serialized={"name": "gpt-4"}, prompts=["What is the capital of France?"]
            )
            print("   ✅ LLM call allowed\n")
        except PolicyViolationError as e:
            print(f"   ❌ Blocked: {e.decision.reason}\n")

    print("\n=== Audit Trail ===")
    for entry in engine.get_audit_trail():
        print(f"[{entry['timestamp']}] {entry['policy_name']}: {entry['decision']}")
        if entry.get("reason"):
            print(f"  Reason: {entry['reason']}")


def example_with_admin_role():
    """
    Example showing how admin users have different permissions.
    """
    engine = PolicyEngine()
    handler = PolicyCallbackHandler(engine)

    ctx = create_context(
        user_id="admin-456", agent_id="research-assistant", role="admin"
    )

    print("\n\n=== Admin User Example ===\n")

    with context_scope(ctx):
        print("Testing external API as admin user...")
        try:
            handler.on_tool_start(
                serialized={"name": "external_api_client"},
                input_str="GET https://api.example.com/data",
            )
            print("✅ External API allowed for admin\n")
        except PolicyViolationError as e:
            print(f"❌ Blocked: {e.decision.reason}\n")


if __name__ == "__main__":
    mock_langchain_agent_run()
    example_with_admin_role()
