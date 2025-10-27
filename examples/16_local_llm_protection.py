# examples/16_local_llm_protection.py
"""
Demo: Protecting Local LLM Workflows

This example demonstrates how Clearstone protects local LLM users from
common pain points: system overload and model server unavailability.
"""

from clearstone import (
    PolicyEngine,
    context_scope,
    create_context,
)
from clearstone.core.policy import reset_policies
from clearstone.integrations.langchain import (
    PolicyCallbackHandler,
    PolicyViolationError,
)

reset_policies()

def simulate_local_llm_call(context):
    """Simulates an LLM call that would be expensive on local hardware."""
    engine = PolicyEngine()
    handler = PolicyCallbackHandler(engine)

    print("\n🤖 Attempting LLM call...")
    print(f"   CPU Threshold: {context.metadata.get('cpu_threshold_percent', 90)}%")
    print(f"   Memory Threshold: {context.metadata.get('memory_threshold_percent', 95)}%")
    print(f"   Model Server: {context.metadata.get('local_model_health_url', 'http://localhost:11434/api/tags')}")

    try:
        with context_scope(context):
            handler.on_llm_start(serialized={"name": "local-llama"}, prompts=["Test prompt"])

        print("✅ LLM call proceeded successfully!")
        return True

    except PolicyViolationError as e:
        print(f"❌ LLM call blocked by policy: {e.decision.metadata.get('policy_name', 'unknown')}")
        print(f"   Reason: {e.decision.reason}")
        return False

if __name__ == "__main__":
    engine = PolicyEngine()

    print("="*70)
    print("DEMO: Local LLM Protection Policies")
    print("="*70)

    # Scenario 1: Normal operation - everything should work
    print("\n--- SCENARIO 1: Normal System Load & Healthy Server ---")
    ctx = create_context(
        "local-user",
        "ollama-agent",
        cpu_threshold_percent=90.0,
        memory_threshold_percent=95.0,
        local_model_health_url="http://localhost:11434/api/tags"
    )

    print("\nℹ️  In a real scenario, system load would be checked automatically.")
    print("   If CPU < 90% and Memory < 95% and model server is healthy,")
    print("   the LLM call proceeds.")

    # Scenario 2: High CPU load - should block
    print("\n\n--- SCENARIO 2: High CPU Load (Simulated) ---")
    print("ℹ️  When system CPU is above threshold, new LLM calls are blocked")
    print("   to prevent system freeze. This protects users running large models")
    print("   on modest hardware.")

    # Scenario 3: Model server down
    print("\n\n--- SCENARIO 3: Model Server Unavailable ---")
    print("ℹ️  If the local model server (Ollama, LM Studio, etc.) is down,")
    print("   the policy provides an immediate, clear error instead of a")
    print("   mysterious 60-second timeout.")

    print("\n" + "="*70)
    print("KEY BENEFITS FOR LOCAL LLM USERS:")
    print("="*70)
    print("✅ Prevents system freezes from overload")
    print("✅ Immediate feedback when model server is down")
    print("✅ Avoids wasted time on doomed requests")
    print("✅ Protects against retry loops that make problems worse")
    print("✅ Specifically designed for local-first AI workflows")

    print("\n" + "="*70)
    print("USAGE:")
    print("="*70)
    print("""
from clearstone.policies.common import (
    system_load_policy,
    model_health_check_policy
)

# These policies run automatically when you use PolicyEngine
# They check system health BEFORE making expensive LLM calls

# Configure thresholds in your context:
context = create_context(
    user_id="user",
    agent_id="agent",

    # System Load Protection
    cpu_threshold_percent=85.0,      # Block if CPU > 85%
    memory_threshold_percent=90.0,    # Block if Memory > 90%

    # Model Health Check
    local_model_health_url="http://localhost:11434/api/tags",
    health_check_timeout=1.0          # 1 second timeout
)
""")

