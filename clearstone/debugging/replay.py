import pdb
from typing import Any, Dict, List
from unittest.mock import patch

from .checkpoint import Checkpoint


class DeterministicExecutionContext:
    """
    A context manager that mocks non-deterministic functions (like time and random)
    to ensure a replay is deterministic. It can also mock user-specified external calls.

    This flexible approach allows users to specify exactly which functions to mock
    and what their recorded return values should be, avoiding hardcoded import paths.
    """

    def __init__(self, checkpoint: Checkpoint, mock_targets: Dict[str, List[Any]]):
        """
        Args:
            checkpoint: The checkpoint to use for context.
            mock_targets: A dictionary mapping the import path of a function to mock
                          to a list of its recorded return values.
                          Example: {"myapp.llm.invoke": [response1, response2]}
        """
        self.checkpoint = checkpoint
        self.mock_targets = mock_targets
        self._patches = []

    def __enter__(self):
        """Applies all the patches."""
        # Patch standard non-deterministic modules
        patcher_time = patch(
            "time.time", return_value=self.checkpoint.timestamp_ns / 1e9
        )
        patcher_random = patch("random.random", return_value=0.5)
        self._patches.extend([patcher_time, patcher_random])

        # Dynamically patch the user-provided targets
        for target_path, side_effect_values in self.mock_targets.items():
            patcher = patch(target_path, side_effect=iter(side_effect_values))
            self._patches.append(patcher)

        # Start all patches
        for p in self._patches:
            p.start()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stops all patches."""
        for p in self._patches:
            p.stop()


class ReplayEngine:
    """
    Loads a checkpoint and rehydrates an agent to allow for interactive,
    time-travel debugging.
    """

    def __init__(self, checkpoint: Checkpoint, trace_store=None):
        self.checkpoint = checkpoint
        self.trace_store = trace_store
        self.agent = self._rehydrate_agent()

    def _rehydrate_agent(self) -> Any:
        """
        Dynamically imports the agent's class and restores its state
        from the checkpoint.
        """
        module_name, class_name = self.checkpoint.agent_class_path.rsplit(".", 1)
        try:
            module = __import__(module_name, fromlist=[class_name])
            agent_class = getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            raise ImportError(
                f"Could not import agent class '{self.checkpoint.agent_class_path}'. Ensure it's in your PYTHONPATH."
            ) from e

        agent_instance = agent_class.__new__(agent_class)

        if hasattr(agent_instance, "load_state"):
            agent_instance.load_state(self.checkpoint.agent_state)
        else:
            agent_instance.__dict__.update(self.checkpoint.agent_state)

        return agent_instance

    def start_debugging_session(
        self,
        function_to_replay: str,
        mock_config: Dict[str, str],
        *args,
        **kwargs,
    ):
        """
        Starts an interactive debugging session using pdb.

        Args:
            function_to_replay: The name of the method on the agent to call.
            mock_config: A mapping from a span_type (e.g., "llm") to the
                         import path of the function to mock (e.g., "my_app.utils.llm.invoke").
                         This tells the replay engine how to map trace data to your code.
            *args: Positional arguments to pass to the replay method.
            **kwargs: Keyword arguments to pass to the replay method.

        Example:
            mock_config = {
                "llm": "finops_autopilot.tools.llm.invoke",
                "tool": "finops_autopilot.tools.cloud_api.run_tool"
            }
            engine.start_debugging_session("run_analysis_step", mock_config=mock_config)
        """
        print("\n--- 🕰️ Welcome to the Clearstone Time-Travel Debugger ---")
        print(f"  Trace ID: {self.checkpoint.trace_id}")
        print(
            f"  Checkpoint: {self.checkpoint.checkpoint_id} (at span: '{self.checkpoint.current_span.name}')"
        )
        print(f"  Agent State: Rehydrated for '{self.checkpoint.agent_class_path}'")
        print(
            "\nDropping into interactive debugger (pdb). Type 'c' to continue execution from the checkpoint."
        )
        print("-" * 60)

        mock_targets = {}
        # Load ALL spans from the trace to find recorded outputs
        # This includes child spans that happen during replay
        if self.trace_store:
            from clearstone.observability.models import Trace

            full_trace = self.trace_store.get_trace(self.checkpoint.trace_id)
            all_spans_in_trace = full_trace.spans
        else:
            # Fallback to checkpoint spans if no trace_store provided
            all_spans_in_trace = self.checkpoint.upstream_spans + [
                self.checkpoint.current_span
            ]

        from clearstone.serialization.hybrid import HybridSerializer

        serializer = HybridSerializer()

        print("\n--- Pre-flight Mock Analysis ---")
        for span_type, target_path in mock_config.items():
            responses = []
            for span in sorted(all_spans_in_trace, key=lambda s: s.start_time_ns):
                # Match spans based on name prefix or custom span_type attribute
                # This allows flexible matching: "llm", "tool", "database", etc.
                span_type_attr = span.attributes.get("span_type", "")
                matches = (
                    span.name.startswith(span_type)
                    or span_type_attr == span_type
                    or span.kind.value.lower() == span_type.lower()
                )

                if (
                    matches
                    and span.output_snapshot
                    and span.output_snapshot.get("captured")
                ):
                    try:
                        deserialized_output = serializer.deserialize(
                            span.output_snapshot["data"]
                        )
                        responses.append(deserialized_output)
                    except Exception:
                        # If deserialization fails, append an error placeholder
                        responses.append(
                            RuntimeError("Failed to deserialize recorded output")
                        )

            mock_targets[target_path] = responses

            # Provide clear debugging information to the user
            print(f"  - Mocking '{target_path}' (for span_type='{span_type}')")
            print(f"    - Found {len(responses)} recorded response(s) in the trace.")

        # 2. Add better error handling
        for target_path, responses in mock_targets.items():
            if not responses:
                print(
                    f"  - ⚠️  WARNING: No recorded outputs found for '{target_path}'. "
                    f"If this function is called during replay, it will crash."
                )

        print("-" * 60)

        # 3. Call the replay method within the configured deterministic context
        replay_method = getattr(self.agent, function_to_replay)

        # Set a breakpoint right before the replay starts
        pdb.set_trace()

        try:
            with DeterministicExecutionContext(self.checkpoint, mock_targets):
                result = replay_method(*args, **kwargs)
                print("-" * 60)
                print(f"--- ✅ Replay finished. Final result: {result} ---")
                return result
        except StopIteration:
            print("\n" + "-" * 60)
            print("--- ❌ Replay Failed: StopIteration ---")
            print(
                "This usually means a mocked function was called more times than there were recorded responses in the trace."
            )
            print(
                "Please check the 'Pre-flight Mock Analysis' above to see how many responses were found."
            )
            # We re-raise the exception so test frameworks can catch it
            raise
