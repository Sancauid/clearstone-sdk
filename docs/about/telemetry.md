# Telemetry

## Our Privacy-First Philosophy

Clearstone takes user privacy seriously. We believe in transparency, minimal data collection, and making opt-out simple. This page explains exactly what anonymous telemetry we collect and how to disable it.

## What We Collect

Clearstone collects **anonymous usage statistics** to help us understand which features are being used and prioritize improvements. The telemetry is:

- **Anonymous**: No personally identifiable information
- **Non-Sensitive**: Only component initialization events
- **Transparent**: All telemetry code is open source and auditable
- **Opt-Out**: Easy to disable at any time

### Data Collected

1. **Component Initialization Events**
   - When `PolicyEngine` is initialized
   - When `TracerProvider` is initialized
   - When `CheckpointManager` is initialized
   - When `PolicyTestHarness` is initialized

2. **SDK Metadata**
   - SDK version (e.g., "0.1.0")
   - Python version (e.g., "3.11.5")

3. **Anonymous Identifiers**
   - Session ID: Generated per-process, not persisted
   - User ID: Anonymous UUID, stored in `~/.clearstone/config.json`

### Example Telemetry Event

```json
{
  "event": "component_initialized",
  "component": "PolicyEngine",
  "sdk_version": "0.1.0",
  "python_version": "3.11.5",
  "session_id": "abc123",
  "user_id": "anonymous-uuid-xyz",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

## What We DON'T Collect

We explicitly **do not** collect:

- ❌ Your policy logic or decisions
- ❌ Trace data or agent outputs
- ❌ User identifiers or credentials
- ❌ Any personally identifiable information (PII)
- ❌ File paths or environment variables
- ❌ API keys or secrets
- ❌ IP addresses (anonymized by default)
- ❌ Specific metadata values from your PolicyContext
- ❌ Tool names, agent names, or any application-specific data

## How We Use the Data

The anonymous telemetry helps us:

1. **Prioritize Features**: Understand which components are most used
2. **Improve Reliability**: Detect if specific Python versions have issues
3. **Plan Deprecations**: Safely remove unused features
4. **Understand Adoption**: See overall SDK adoption trends

## How to Opt Out

### Option 1: Environment Variable (Recommended)

Set the `CLEARSTONE_TELEMETRY_DISABLED` environment variable:

```bash
export CLEARSTONE_TELEMETRY_DISABLED=1
```

Add this to your shell profile (`.bashrc`, `.zshrc`, etc.) to make it permanent:

```bash
echo 'export CLEARSTONE_TELEMETRY_DISABLED=1' >> ~/.zshrc
source ~/.zshrc
```

### Option 2: Configuration File

Create or edit `~/.clearstone/config.json`:

```json
{
  "telemetry": {
    "disabled": true
  }
}
```

**Create the config file:**

```bash
mkdir -p ~/.clearstone
cat > ~/.clearstone/config.json << EOF
{
  "telemetry": {
    "disabled": true
  }
}
EOF
```

### Option 3: Programmatic

Disable telemetry in your application code:

```python
from clearstone.utils.telemetry import disable_telemetry

disable_telemetry()
```

## Verifying Telemetry is Disabled

Check if telemetry is disabled:

```python
from clearstone.utils.telemetry import is_telemetry_enabled

if is_telemetry_enabled():
    print("Telemetry is ENABLED")
else:
    print("Telemetry is DISABLED")
```

## Data Retention

- **Session IDs**: Not persisted, exist only for the process lifetime
- **User IDs**: Stored locally in `~/.clearstone/config.json` only
- **Telemetry Events**: Sent to our servers and retained for 90 days

## Auditing the Code

All telemetry code is open source and auditable:

- **Telemetry Module**: `clearstone/utils/telemetry.py`
- **Configuration**: `~/.clearstone/config.json`

You can review the exact implementation to verify what data is collected:

```bash
# View the telemetry implementation
cat clearstone/utils/telemetry.py
```

## Transparency Report

We publish an annual transparency report showing:
- Total number of active installations
- Most-used components
- SDK version distribution
- Python version distribution

**No user-specific data** is ever included in these reports.

## Data Security

- All telemetry is sent over **HTTPS**
- No authentication tokens or credentials are ever transmitted
- Anonymous IDs cannot be reverse-engineered to identify users

## Frequently Asked Questions

### Does telemetry slow down my agent?

No. Telemetry events are:
- Sent asynchronously (non-blocking)
- Only triggered on component initialization (not during execution)
- Batched and rate-limited

### Can you identify me from the anonymous user ID?

No. The user ID is a randomly generated UUID with no connection to your identity, email, or any other identifying information.

### What if I forget to opt out and then decide to?

Just set the environment variable or config file. The SDK checks for opt-out on every process start.

### Does opting out affect functionality?

No. All features work identically whether telemetry is enabled or disabled.

### Do you sell telemetry data?

Absolutely not. We never sell, share, or monetize telemetry data. It's used solely for improving the SDK.

### Can I opt back in?

Yes. Simply remove the environment variable or set `"disabled": false` in the config file.

## Contact

If you have questions or concerns about telemetry:

- **GitHub Issues**: [Report Privacy Concerns](https://github.com/your-repo/clearstone-sdk/issues)

## Changes to This Policy

We will notify users of any changes to this telemetry policy via:
- SDK release notes
- GitHub announcements
- Documentation updates

**Last Updated**: October 2025

