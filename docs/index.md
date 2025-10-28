# Clearstone SDK

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Stars](https://img.shields.io/github/stars/Sancauid/clearstone-sdk?style=social)](https://github.com/Sancauid/clearstone-sdk)

**[Join the Waitlist](https://t.co/4geEAPFzXC) for our upcoming cloud platform and enterprise features!**

**Production-Grade Governance and Observability for AI Agent Systems.**

Clearstone is a comprehensive Python SDK that provides safety, governance, and observability for multi-agent AI workflows. It combines declarative Policy-as-Code with OpenTelemetry-aligned distributed tracing to help you build reliable, debuggable, and compliant AI systems.

---

## The Problem

Autonomous AI agents are powerful but operate in a high-stakes environment. Without robust guardrails and observability, they can be:

*   **Unsafe:** Accidentally executing destructive actions (e.g., deleting files).
*   **Costly:** Over-using expensive tools or LLM tokens.
*   **Non-compliant:** Mishandling sensitive data (PII).
*   **Unpredictable:** Difficult to debug when they fail.
*   **Opaque:** No visibility into what they're actually doing at runtime.

Clearstone provides the tools to manage these risks with declarative Policy-as-Code governance and production-ready distributed tracing.

## Key Features

### Policy Governance
*   ✅ **Declarative Policy-as-Code:** Write policies as simple Python functions using the `@Policy` decorator. No YAML or complex DSLs.
*   ✅ **Seamless LangChain Integration:** Drop the `PolicyCallbackHandler` into any LangChain agent to enforce policies at runtime.
*   ✅ **Rich Pre-Built Policy Library:** Get started in minutes with 17+ production-ready policies for cost control, RBAC, PII redaction, security alerts, and more.
*   ✅ **Local LLM Protection:** Built-in policies for system load monitoring and model server health checks—specifically designed for local-first AI workflows.
*   ✅ **Human-in-the-Loop Controls:** Pause agent execution for manual approval with the `PAUSE` action and `InterventionClient` for high-stakes decisions.
*   ✅ **Pre-Deploy Validation:** Catch buggy, slow, or non-deterministic policies *before* they reach production with the `PolicyValidator`.
*   ✅ **Line-by-Line Debugging:** Understand exactly why a policy made a decision with the `PolicyDebugger`'s execution trace.
*   ✅ **Performance Metrics:** Track policy execution times, identify bottlenecks, and analyze decision patterns with `PolicyMetrics`.
*   ✅ **Composable Logic:** Build complex rules from simple, reusable policies with `compose_and` and `compose_or` helpers.
*   ✅ **Exportable Audit Trails:** Generate JSON or CSV audit logs for every policy decision, perfect for compliance and analysis.
*   ✅ **Developer CLI:** Accelerate development by scaffolding new, well-structured policy files with the `clearstone new-policy` command.

### Observability & Tracing
*   ✅ **Production-Ready Tracing:** OpenTelemetry-aligned distributed tracing for complete agent execution visibility.
*   ✅ **Automatic Hierarchy Tracking:** Nested spans automatically establish parent-child relationships without manual configuration.
*   ✅ **High-Fidelity Capture:** Nanosecond-precision timing, input/output snapshots, and full error stack traces.
*   ✅ **Thread-Safe Persistence:** SQLite storage with Write-Ahead Logging (WAL) for concurrent-safe trace storage.
*   ✅ **Asynchronous Batching:** Non-blocking span capture with automatic batch writes for zero performance impact.
*   ✅ **Hybrid Serialization:** Smart JSON-first serialization with automatic pickle fallback for complex objects.
*   ✅ **Single-Line Setup:** Initialize the entire tracing system with one `TracerProvider` instantiation.

### AI-Native Testing & Backtesting
*   ✅ **Behavioral Assertions:** Declarative test functions for validating agent behavior (tool usage, execution order, costs, errors).
*   ✅ **Historical Backtesting:** Test new policies against real production traces to predict impact before deployment.
*   ✅ **Policy Test Harness:** Simulate policy enforcement on historical data with detailed impact reports and metrics.
*   ✅ **pytest Integration:** Seamlessly integrate behavioral tests into existing test workflows and CI/CD pipelines.
*   ✅ **Trace-Level Validation:** Assert on complete execution flows, not just individual operations or outputs.
*   ✅ **Comprehensive Reporting:** Track block rates, decision distributions, and identify problematic traces.

### Time-Travel Debugging
*   ✅ **Checkpoint System:** Capture complete agent state at any point in execution history.
*   ✅ **Agent Rehydration:** Dynamically restore agents from checkpoints with full state preservation.
*   ✅ **Deterministic Replay:** Mock non-deterministic functions (time, random) for reproducible debugging sessions.
*   ✅ **Interactive Debugging:** Drop into pdb at any historical execution point with full context.
*   ✅ **Hybrid Serialization:** JSON metadata with pickle state for human-readable yet high-fidelity checkpoints.
*   ✅ **Upstream Span Tracking:** Automatically capture parent span hierarchy for complete execution context.

## Installation

The SDK requires Python 3.10+.

```bash
pip install clearstone-sdk
```

## Quick Example

See how easy it is to protect an agent from performing unauthorized actions.

```python
from clearstone import Policy, ALLOW, BLOCK, PolicyEngine, create_context, context_scope
from clearstone.integrations.langchain import PolicyCallbackHandler

@Policy(name="block_admin_tools_for_guests", priority=100)
def block_admin_tools_policy(context):
    role = context.metadata.get("role")
    tool_name = context.metadata.get("tool_name")

    if role == "guest" and tool_name == "admin_panel":
        return BLOCK(f"Role '{role}' is not authorized to access '{tool_name}'.")
    
    return ALLOW

engine = PolicyEngine()
handler = PolicyCallbackHandler(engine)

context = create_context(
    user_id="user_guest",
    agent_id="admin_agent_v1",
    metadata={"role": "guest"}
)

with context_scope(context):
    handler.on_tool_start(serialized={"name": "admin_panel"}, input_str="")
```

## Next Steps

- **[Getting Started](getting-started.md)**: 5-minute quickstart tutorial
- **[Core Concepts](guide/core-concepts.md)**: Understand the foundational concepts
- **[Pre-Built Policies](policies.md)**: Explore the policy library
- **[User Guide](guide/governance.md)**: Deep dive into governance features
- **[API Reference](api/governance.md)**: Complete API documentation

## Anonymous Usage Telemetry

To help improve Clearstone, the SDK collects anonymous usage statistics by default. This telemetry is:

- **Anonymous:** Only component initialization events are tracked (e.g., "PolicyEngine initialized")
- **Non-Identifying:** No user data, policy logic, or trace content is ever collected
- **Transparent:** All telemetry code is open source and auditable
- **Opt-Out:** Easy to disable at any time

### How to Opt Out

**Option 1: Environment Variable (Recommended)**
```bash
export CLEARSTONE_TELEMETRY_DISABLED=1
```

**Option 2: Config File**

Edit or create `~/.clearstone/config.json`:
```json
{
  "telemetry": {
    "disabled": true
  }
}
```

Learn more in the [Telemetry documentation](about/telemetry.md).

## Contributing

Contributions are welcome! Please see our [Contributing Guide](about/contributing.md) for details on how to submit pull requests, set up a development environment, and run tests.

## License

This project is licensed under the MIT License. See the [LICENSE](about/license.md) file for details.

---

## Community & Support

Join our community to ask questions, share your projects, and get help from the team and other users.

*   **Discord:** [Join the Clearstone Community](https://discord.gg/VZAX4vk8dT)
*   **Twitter:** Follow [@clearstonedev](https://twitter.com/clearstonedev) for the latest news and updates.
*   **GitHub Issues:** [Report a bug or suggest a feature](https://github.com/Sancauid/clearstone-sdk/issues).
*   **Email:** For other inquiries, you can reach out to [pablo@clearstone.dev](mailto:pablo@clearstone.dev).
