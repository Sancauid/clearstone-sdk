# Changelog

All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.1] - 2025-10-27

### ✨ Enhancements

*   **Refactored `PolicyEngine` for Explicit Configuration:** The `PolicyEngine` constructor now accepts an optional `policies` list. This allows developers to bypass auto-discovery and provide an explicit, controlled set of policies, which is the recommended pattern for production and testing. The engine remains fully backward-compatible, with auto-discovery as the default behavior.

---

## [0.1.0] - 2025-10-27

### 🎉 Initial Public Release

This is the first public release of the Clearstone SDK, a comprehensive, local-first toolkit designed to make Python AI agents safe, observable, reliable, and debuggable.

### ✨ Features Added

#### 🛡️ Governance Pillar
*   **Policy Engine:** A lightweight, in-process engine for enforcing rules written in native Python using a `@Policy` decorator.
*   **LangChain Integration:** A seamless `PolicyCallbackHandler` to integrate the engine into the LangChain lifecycle.
*   **Pre-Built Policy Library:** A rich library of common policies for cost control, security, RBAC, and local system protection.
*   **Human-in-the-Loop:** An `InterventionClient` and `PAUSE` decision type to enable interactive approval workflows.

#### 🔭 Observability Pillar
*   **Local-First Tracing:** A `@trace` decorator and `TracerProvider` for capturing agent execution flows into a local SQLite database.
*   **Hardened Storage:** A concurrent-safe, batched-write `TraceStore` and `SpanBuffer`.
*   **High-Fidelity Serialization:** A `HybridSerializer` for capturing complex Python objects.

#### 🧪 Testing Pillar
*   **Policy Test Harness:** A `PolicyTestHarness` for backtesting new governance policies against historical traces.
*   **Behavioral Assertion Library:** A suite of `assert_*` functions for writing high-level, declarative tests about an agent's behavior.

#### 🕰️ Time-Travel Debugging Pillar
*   **Checkpoint System:** A `CheckpointManager` for saving the complete state of an agent at any point in a trace.
*   **Replay Engine:** The `ReplayEngine` for "rehydrating" an agent from a checkpoint into an interactive `pdb` debugging session.

#### 🔧 Developer Toolkit & DX
*   **Utilities:** A full suite of developer tools including `PolicyValidator`, `PolicyDebugger`, `AuditTrail`, and `PolicyMetrics`.
*   **CLI:** A `clearstone new-policy` command for scaffolding boilerplate policy files.

### 📦 Project Scaffolding
*   **Professional Packaging:** The project is configured with a modern `pyproject.toml`.
*   **Continuous Integration:** A GitHub Actions workflow automatically runs tests and style checks.
*   **Code Quality:** Automated code formatting and linting are enforced with `black` and `ruff`.
*   **Comprehensive Documentation:** A full documentation website built with `MkDocs`.
*   **Privacy-First Telemetry:** Includes a simple, opt-out anonymous usage telemetry system.