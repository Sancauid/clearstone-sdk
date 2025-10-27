# Getting Started

This guide will help you get started with Clearstone SDK in just 5 minutes.

## Installation

The SDK requires Python 3.10 or higher.

```bash
pip install clearstone-sdk
```

## 5-Minute Quickstart

See how easy it is to protect an agent from performing unauthorized actions.

### 1. Define Your Policies

Create a file `my_app/policies.py`. Our policies will check a user's role before allowing access to a tool.

```python
# my_app/policies.py
from clearstone import Policy, ALLOW, BLOCK

@Policy(name="block_admin_tools_for_guests", priority=100)
def block_admin_tools_policy(context):
    """A high-priority policy to enforce Role-Based Access Control (RBAC)."""
    
    # Policies read data from the context's metadata
    role = context.metadata.get("role")
    tool_name = context.metadata.get("tool_name")

    if role == "guest" and tool_name == "admin_panel":
        return BLOCK(f"Role '{role}' is not authorized to access '{tool_name}'.")
    
    return ALLOW
```

### 2. Integrate with Your Agent

In your main application file, initialize the engine and add the `PolicyCallbackHandler` to your agent call.

```python
# my_app/main.py
from clearstone import (
    create_context,
    context_scope,
    PolicyEngine,
    PolicyViolationError
)
from clearstone.integrations.langchain import PolicyCallbackHandler

# This import discovers and registers the policies we just wrote
import my_app.policies

# --- Setup Clearstone (do this once) ---
engine = PolicyEngine()
handler = PolicyCallbackHandler(engine)

def run_agent_with_tool(user_role: str):
    """Simulates running an agent for a user with a specific role."""
    print(f"\n--- Running agent for user with role: '{user_role}' ---")

    # 1. Create a context for this specific run
    context = create_context(
        user_id=f"user_{user_role}",
        agent_id="admin_agent_v1",
        metadata={"role": user_role}
    )

    try:
        # 2. Run the agent within the context scope and with the handler
        with context_scope(context):
            # In a real app, this would be: agent.invoke(..., callbacks=[handler])
            # We simulate the tool call for this example:
            print("Agent is attempting to access 'admin_panel' tool...")
            handler.on_tool_start(serialized={"name": "admin_panel"}, input_str="")
        
        print("✅ SUCCESS: Agent action was approved by all policies.")

    except PolicyViolationError as e:
        # 3. Handle policy violations gracefully
        print(f"❌ BLOCKED: The action was stopped by a policy.")
        print(f"   Reason: {e.decision.reason}")

# --- Run Scenarios ---
run_agent_with_tool("admin")
run_agent_with_tool("guest")
```

### 3. Run and See the Result

```
--- Running agent for user with role: 'admin' ---
Agent is attempting to access 'admin_panel' tool...
✅ SUCCESS: Agent action was approved by all policies.

--- Running agent for user with role: 'guest' ---
Agent is attempting to access 'admin_panel' tool...
❌ BLOCKED: The action was stopped by a policy.
   Reason: Role 'guest' is not authorized to access 'admin_panel'.
```

## Next Steps

- Learn more about [Writing Policies](writing-policies.md)
- Explore the [Developer Toolkit](developer-toolkit.md)
- Check out the [API Reference](../api/index.md)

