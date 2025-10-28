# Design Philosophy

The Clearstone SDK is designed to be a simple, powerful, and "Pythonic" toolkit. To achieve this, we've made several key architectural decisions that might differ from other tools you've used. Understanding these principles will help you use the SDK more effectively.

## 1. Explicit Configuration over "Magic"

**The Principle:** A developer should always have explicit control over the code that runs in their application.

**The Implementation:**

The `PolicyEngine` supports two modes:

*   **Auto-Discovery (`PolicyEngine()`):** Great for quickstarts and demos. It automatically finds all imported `@Policy` functions.
*   **Explicit Configuration (`PolicyEngine(policies=[...])`):** The recommended pattern for production. You provide an explicit list of the *only* policies you want to be active.

**Why this design?**

While auto-discovery is convenient, it can lead to "magic" behavior where policies you didn't know about are running. In a production environment, being explicit is safer, more predictable, and easier to test. We provide the convenience of auto-discovery for development but give you the explicit control needed for production.

**Example:**

```python
from clearstone import PolicyEngine, Policy, ALLOW, BLOCK

@Policy(name="auth_policy", priority=100)
def auth_policy(context):
    if not context.metadata.get("authenticated"):
        return BLOCK("Not authenticated")
    return ALLOW

@Policy(name="cost_policy", priority=90)
def cost_policy(context):
    if context.metadata.get("cost", 0) > 100:
        return BLOCK("Cost limit exceeded")
    return ALLOW

# Development: Auto-discovery (convenient)
dev_engine = PolicyEngine()

# Production: Explicit (safe, predictable)
prod_engine = PolicyEngine(policies=[auth_policy, cost_policy])
```

## 2. Pydantic Models over Custom Setters

**The Principle:** Data structures should be simple, transparent, and follow standard Python patterns.

**The Implementation:**

Our core data models, like the `Span` object from the observability pillar, are built using **Pydantic**. You interact with them like you would with any standard Python object or dictionary.

**Instead of:**

```python
# A common pattern in other libraries (e.g., OpenTelemetry)
span.set_attribute("my_key", "my_value")
```

**The Clearstone Way is:**

```python
# The standard, Pythonic way
span.attributes["my_key"] = "my_value"
```

**Why this design?**

By using standard Pydantic models, we avoid creating a custom, proprietary API for interacting with data. This means:

- ✅ Your IDE's autocomplete and type checking work perfectly
- ✅ The behavior is instantly familiar to any Python developer
- ✅ You can easily serialize our objects to JSON or dictionaries using standard Pydantic methods (`.model_dump()`)
- ✅ We chose to align with the Python ecosystem's best practices rather than inventing our own

**Example:**

```python
from clearstone.observability import TracerProvider

provider = TracerProvider(db_path="traces.db")
tracer = provider.get_tracer("my_agent")

with tracer.span("operation") as span:
    # Standard Python dict access
    span.attributes["user_id"] = "user_123"
    span.attributes["cost"] = 0.05
    
    # Standard Pydantic methods work
    span_dict = span.model_dump()
    
    # Standard Python attribute access
    print(f"Span ID: {span.span_id}")
    print(f"Duration: {span.duration_ms}ms")
```

## 3. Targeted Integration over Universal Abstractions

**The Principle:** Integration code should live where it is used.

**The Implementation:**

You'll notice that components specific to a particular framework are located in a dedicated integration module. For example, the `PolicyViolationError` and `PolicyPauseError` are in `clearstone.integrations.langchain`.

**Instead of:**

```python
# A common pattern of putting all exceptions in a central 'core' or 'domain' module
from clearstone.core import PolicyViolationError  # This does NOT exist
```

**The Clearstone Way is:**

```python
# Exceptions are located with the code that raises them
from clearstone.integrations.langchain import PolicyViolationError
```

**Why this design?**

This makes our core SDK (`clearstone.core`, `clearstone.observability`, etc.) completely framework-agnostic. The core engine knows nothing about LangChain. This is a deliberate choice that allows Clearstone to be easily adapted to any Python framework (CrewAI, AutoGen, etc.) simply by creating a new, small integration module for it. It keeps the core clean and universally applicable.

**Example:**

```python
from clearstone import PolicyEngine, create_context, context_scope
from clearstone.integrations.langchain import (
    PolicyCallbackHandler,
    PolicyViolationError,  # LangChain-specific
    PolicyPauseError        # LangChain-specific
)

engine = PolicyEngine()
handler = PolicyCallbackHandler(engine)

# These exceptions are specific to the LangChain integration
try:
    with context_scope(context):
        agent.invoke(input, callbacks=[handler])
except PolicyViolationError as e:
    print(f"Blocked: {e.decision.reason}")
except PolicyPauseError as e:
    print(f"Paused: {e.decision.reason}")
```

**Framework Extensibility:**

```python
# clearstone/core/ - Framework-agnostic
from clearstone.core import PolicyEngine

# clearstone/integrations/langchain/ - LangChain-specific
from clearstone.integrations.langchain import PolicyCallbackHandler

# clearstone/integrations/crewai/ - CrewAI-specific (future)
# from clearstone.integrations.crewai import CrewAIPolicyMiddleware

# clearstone/integrations/autogen/ - AutoGen-specific (future)
# from clearstone.integrations.autogen import AutoGenPolicyWrapper
```

## Core Design Values

These three principles reflect our broader design values:

### Clarity over Convenience

We prefer code that is explicit and easy to understand over code that is "clever" or relies on hidden magic.

### Python Standards over Custom Patterns

We use standard Python and Pydantic patterns wherever possible, rather than inventing proprietary APIs.

### Modularity over Monoliths

We keep the core SDK small, focused, and framework-agnostic. Framework-specific code lives in dedicated integration modules.

### Developer Experience

We optimize for:
- **IDE Support:** Autocomplete and type checking work perfectly
- **Discoverability:** APIs are intuitive and follow Python conventions
- **Flexibility:** Multiple ways to accomplish tasks (auto-discovery vs explicit)
- **Safety:** Production use cases get explicit, predictable behavior

## Next Steps

- **[Core Concepts](../guide/core-concepts.md)**: Understand the three pillars
- **[Governance Guide](../guide/governance.md)**: Learn about PolicyEngine configuration modes
- **[Contributing](../about/contributing.md)**: Help us maintain these principles

