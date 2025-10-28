# Architecture Overview

Clearstone SDK is built on a modular, extensible architecture designed for production-grade AI agent governance and observability.

## System Architecture

The SDK is organized into several independent but complementary pillars:

```
clearstone/
├── core/               # Framework-agnostic governance engine
├── observability/      # Distributed tracing system
├── debugging/          # Time-travel debugging and checkpointing
├── testing/            # AI-native testing framework
├── integrations/       # Framework-specific adapters
│   ├── langchain/
│   └── future/
├── policies/           # Pre-built policy library
├── serialization/      # Hybrid JSON/pickle serialization
├── storage/            # SQLite persistence layer
└── utils/              # Cross-cutting utilities
```

## Core Pillars

### 1. Governance (Policy-as-Code)

**Location:** `clearstone/core/`

The governance pillar provides declarative policy enforcement for AI agents.

**Key Components:**
- **PolicyEngine**: Discovers, evaluates, and enforces policies
- **Policy Decorator**: Registers functions as policies with metadata
- **PolicyContext**: Immutable execution context passed to policies
- **Decision Actions**: ALLOW, BLOCK, ALERT, PAUSE, REDACT

**Design Characteristics:**
- Zero dependencies on AI frameworks
- Composable policy logic
- Fail-safe defaults (errors don't crash)
- Performance metrics and audit trails built-in

### 2. Observability (Distributed Tracing)

**Location:** `clearstone/observability/`

OpenTelemetry-aligned distributed tracing for complete agent visibility.

**Key Components:**
- **TracerProvider**: Entry point for tracing system
- **Tracer**: Creates and manages spans
- **Span**: Represents a single operation with timing/metadata
- **TraceStore**: SQLite-based persistence with WAL mode

**Design Characteristics:**
- Non-blocking capture (< 1μs overhead)
- Automatic parent-child span linking
- Batched writes for performance
- Thread-safe operations

### 3. Testing & Backtesting

**Location:** `clearstone/testing/`

AI-native testing framework for validating agent behavior.

**Key Components:**
- **PolicyTestHarness**: Simulates policy enforcement on historical traces
- **Behavioral Assertions**: Declarative tests for agent behavior
- **TestResult**: Impact analysis and metrics

**Design Characteristics:**
- Tests "how" agents behave, not just "what" they return
- Historical backtesting against production data
- pytest integration
- Regression prevention

### 4. Time-Travel Debugging

**Location:** `clearstone/debugging/`

Checkpoint and replay agent execution from any point in history.

**Key Components:**
- **CheckpointManager**: Creates, saves, and loads agent snapshots
- **ReplayEngine**: Restores agent state and enables debugging
- **DeterministicExecutionContext**: Mocks non-deterministic functions

**Design Characteristics:**
- Complete state preservation
- Deterministic replay
- Interactive debugging sessions
- Upstream span tracking

## Cross-Cutting Concerns

### Serialization

**Location:** `clearstone/serialization/`

Hybrid JSON-first approach with pickle fallback for complex objects.

**Features:**
- Automatic format selection based on serializability
- Size limits for safety
- Human-readable JSON when possible

### Storage

**Location:** `clearstone/storage/`

SQLite-based persistence with production-grade features.

**Features:**
- Write-Ahead Logging (WAL) for concurrency
- Asynchronous batching with `SpanBuffer`
- Thread-safe operations
- Efficient indexing and querying

### Integrations

**Location:** `clearstone/integrations/`

Framework-specific adapters that keep the core framework-agnostic.

**Current:**
- **LangChain**: `PolicyCallbackHandler` for automatic policy enforcement

**Future:**
- CrewAI integration
- AutoGen integration
- Custom framework support

## Data Flow

### Policy Enforcement Flow

```
User Action
    ↓
LangChain Callback
    ↓
PolicyCallbackHandler (integration)
    ↓
PolicyEngine.evaluate() (core)
    ↓
Policy Functions (sorted by priority)
    ↓
Decision (ALLOW/BLOCK/PAUSE/ALERT/REDACT)
    ↓
Action Taken or Exception Raised
```

### Tracing Flow

```
Agent Operation
    ↓
tracer.span() context manager
    ↓
Span creation (in-memory)
    ↓
SpanBuffer (batching)
    ↓
TraceStore (SQLite with WAL)
    ↓
Queryable trace data
```

### Testing Flow

```
Production Agent Run
    ↓
Traces captured to SQLite
    ↓
PolicyTestHarness.load_traces()
    ↓
PolicyTestHarness.simulate_policy()
    ↓
TestResult with impact analysis
    ↓
pytest assertions
```

## Design Principles

Clearstone's architecture follows these key principles:

1. **Modularity**: Each pillar can be used independently
2. **Framework Agnostic**: Core SDK has zero AI framework dependencies
3. **Production Ready**: Thread-safe, performant, fail-safe
4. **Developer Friendly**: Standard Python patterns, strong typing
5. **Extensible**: Easy to add new integrations and policies

See the [Design Philosophy](design-philosophy.md) document for deeper insights into our architectural decisions.

## Performance Characteristics

### PolicyEngine

- **Evaluation Time**: < 1ms per policy (typical)
- **Memory Overhead**: Minimal (policies are pure functions)
- **Concurrency**: Thread-safe evaluation

### Tracing

- **Capture Overhead**: < 1μs per span
- **Write Throughput**: 10,000+ spans/second with batching
- **Storage Growth**: ~1KB per span (depends on attributes)
- **Query Performance**: Indexed by trace_id, parent_span_id

### Testing

- **Simulation Speed**: 1,000+ traces/second
- **Memory Usage**: Loads traces in batches (configurable)

## Deployment Considerations

### Database

- SQLite with WAL mode (concurrent reads, single writer)
- Recommended: Regular backups of trace database
- Optional: External storage for long-term archive

### Scaling

- **Vertical**: Single process handles 10,000+ policy evaluations/second
- **Horizontal**: Each process has its own SQLite database
- **Aggregation**: Use external tools to aggregate traces from multiple processes

### Monitoring

- Built-in `PolicyMetrics` for policy performance
- Built-in `AuditTrail` for compliance logging
- Export traces to external systems via TraceStore API

## Next Steps

- **[Design Philosophy](design-philosophy.md)**: Understand our architectural decisions
- **[Core Concepts](../guide/core-concepts.md)**: Learn the three pillars
- **[API Reference](../api/governance.md)**: Complete API documentation
- **[Contributing](../about/contributing.md)**: Help improve the architecture

