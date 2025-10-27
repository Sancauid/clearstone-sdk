"""
Policy debugging tools for tracing execution and understanding policy decisions.
"""

import inspect
import sys
from typing import Any, Callable, Dict, List, Tuple

from clearstone.core.actions import Decision
from clearstone.core.context import PolicyContext
from clearstone.utils.telemetry import get_telemetry_manager


class PolicyDebugger:
    """
    Provides tools to trace the execution of a single policy function,
    offering insight into its decision-making process.

    Example:
        debugger = PolicyDebugger()
        decision, trace = debugger.trace_evaluation(my_policy, context)
        print(debugger.format_trace(my_policy, decision, trace))
    """

    def __init__(self):
        """Initializes the PolicyDebugger."""
        get_telemetry_manager().record_event(
            "component_initialized", {"name": "PolicyDebugger"}
        )

    def trace_evaluation(
        self, policy: Callable[[PolicyContext], Decision], context: PolicyContext
    ) -> Tuple[Decision, List[Dict[str, Any]]]:
        """
        Executes a policy and records each line of code that runs, along with
        the state of local variables at that line.

        This uses Python's `sys.settrace` for a robust, line-by-line trace.

        Args:
            policy: The policy function to debug.
            context: The PolicyContext to run the policy against.

        Returns:
            A tuple containing:
            - The final Decision made by the policy.
            - A list of trace events (dictionaries).

        Example:
            decision, trace = debugger.trace_evaluation(my_policy, ctx)
            for event in trace:
                print(f"Line {event['line_no']}: {event['line_text']}")
        """
        trace_events = []

        try:
            lines, start_line = inspect.getsourcelines(policy)
            end_line = start_line + len(lines)
        except (TypeError, OSError):
            lines, start_line, end_line = [], -1, -1

        def tracer(frame, event, arg):
            if event == "line" and start_line <= frame.f_lineno < end_line:
                trace_events.append(
                    {
                        "line_no": frame.f_lineno,
                        "line_text": lines[frame.f_lineno - start_line].strip(),
                        "locals": {
                            k: repr(v)
                            for k, v in frame.f_locals.items()
                            if not k.startswith("__")
                        },
                    }
                )
            return tracer

        original_trace = sys.gettrace()
        sys.settrace(tracer)
        try:
            final_decision = policy(context)
        finally:
            sys.settrace(original_trace)

        return final_decision, trace_events

    def format_trace(
        self, policy: Callable, decision: Decision, trace: List[Dict[str, Any]]
    ) -> str:
        """
        Formats the output of a trace_evaluation into a human-readable string.

        Args:
            policy: The policy function that was traced.
            decision: The final decision from the policy.
            trace: The trace events from trace_evaluation.

        Returns:
            A formatted string showing the execution path.

        Example:
            formatted = debugger.format_trace(my_policy, decision, trace)
            print(formatted)
        """
        output = f"--- Policy Debug Trace for '{policy.__name__}' ---\n"
        output += f"Final Decision: {decision.action.value.upper()}\n"
        output += f"Final Reason: {decision.reason or 'N/A'}\n\n"
        output += "Execution Path:\n"
        if not trace:
            output += "  (No trace available for this function, it might be a built-in or C-extension).\n"
        for event in trace:
            output += f"  L{event['line_no']:<3} | {event['line_text']:<60} | Locals: {event['locals']}\n"
        return output
