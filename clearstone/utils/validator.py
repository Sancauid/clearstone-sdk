"""
Policy validation tools for pre-deployment checks.

This module provides utilities to validate that policies are safe, performant,
and deterministic before deploying them to production.
"""

import timeit
from typing import Callable, List

from clearstone.core.actions import Decision
from clearstone.core.context import PolicyContext, create_context
from clearstone.utils.telemetry import get_telemetry_manager


class PolicyValidationError(AssertionError):
    """Custom exception for policy validation failures."""

    pass


class PolicyValidator:
    """
    A tool for running pre-deployment checks on policy functions to ensure
    they are safe, performant, and deterministic.

    Example:
        validator = PolicyValidator()
        failures = validator.run_all_checks(my_policy)
        if failures:
            print("Policy validation failed:")
            for failure in failures:
                print(f"  - {failure}")
    """

    def __init__(self, default_context: PolicyContext = None):
        """
        Initializes the validator.

        Args:
            default_context: A sample PolicyContext to use for tests. If None,
                             a generic one will be created.
        """
        self._default_context = default_context or create_context(
            user_id="validation_user",
            agent_id="validation_agent",
            session_id="validation_session",
        )

        get_telemetry_manager().record_event(
            "component_initialized", {"name": "PolicyValidator"}
        )

    def validate_determinism(
        self, policy: Callable[[PolicyContext], Decision], num_runs: int = 5
    ) -> None:
        """
        Checks if a policy returns the same output for the same input.
        This catches policies that rely on non-deterministic functions (e.g., random, datetime.now()).

        Args:
            policy: The policy function to validate.
            num_runs: Number of times to run the policy to check consistency.

        Raises:
            PolicyValidationError: If the policy produces different decisions for the same context.
        """
        try:
            first_decision = policy(self._default_context)
            for i in range(num_runs - 1):
                next_decision = policy(self._default_context)
                if first_decision != next_decision:
                    raise PolicyValidationError(
                        f"Policy '{policy.__name__}' is non-deterministic. "
                        f"Run {i+2} produced a different result than run 1."
                    )
        except PolicyValidationError:
            raise
        except Exception as e:
            raise PolicyValidationError(
                f"Policy '{policy.__name__}' raised an exception during determinism testing: "
                f"'{type(e).__name__}: {e}'"
            ) from e

    def validate_performance(
        self,
        policy: Callable[[PolicyContext], Decision],
        max_latency_ms: float = 1.0,
        num_runs: int = 1000,
    ) -> None:
        """
        Checks if a policy executes within a given latency budget.
        This catches slow policies that might perform network requests or heavy computation.

        Args:
            policy: The policy function to validate.
            max_latency_ms: Maximum acceptable average latency in milliseconds.
            num_runs: Number of runs to average over.

        Raises:
            PolicyValidationError: If the policy's average execution time exceeds the threshold.
        """
        try:
            timer = timeit.Timer(lambda: policy(self._default_context))
            total_time_s = timer.timeit(number=num_runs)
            avg_latency_ms = (total_time_s / num_runs) * 1000

            if avg_latency_ms > max_latency_ms:
                raise PolicyValidationError(
                    f"Policy '{policy.__name__}' is too slow. "
                    f"Average latency: {avg_latency_ms:.4f}ms, Budget: {max_latency_ms}ms."
                )
        except PolicyValidationError:
            raise
        except Exception as e:
            raise PolicyValidationError(
                f"Policy '{policy.__name__}' raised an exception during performance testing: "
                f"'{type(e).__name__}: {e}'"
            ) from e

    def validate_exception_safety(
        self, policy: Callable[[PolicyContext], Decision]
    ) -> None:
        """
        Checks if a policy crashes when given a context with missing metadata.
        A safe policy should handle missing keys gracefully (e.g., using .get() with defaults).

        Args:
            policy: The policy function to validate.

        Raises:
            PolicyValidationError: If the policy raises an unexpected exception.
        """
        empty_meta_context = create_context("user", "agent")
        try:
            result = policy(empty_meta_context)
            if not isinstance(result, Decision):
                raise TypeError(
                    f"Policy '{policy.__name__}' did not return a Decision object."
                )
        except Exception as e:
            raise PolicyValidationError(
                f"Policy '{policy.__name__}' is not exception-safe. "
                f"It raised '{type(e).__name__}: {e}' on a context with empty metadata."
            ) from e

    def run_all_checks(self, policy: Callable[[PolicyContext], Decision]) -> List[str]:
        """
        Runs all validation checks on a single policy and returns a list of failures.

        Args:
            policy: The policy function to validate.

        Returns:
            A list of strings, where each string is an error message. An empty list means all checks passed.

        Example:
            validator = PolicyValidator()
            failures = validator.run_all_checks(my_policy)
            if not failures:
                print("All checks passed!")
        """
        failures = []

        try:
            self.validate_determinism(policy)
        except PolicyValidationError as e:
            failures.append(str(e))

        try:
            self.validate_performance(policy)
        except PolicyValidationError as e:
            failures.append(str(e))

        try:
            self.validate_exception_safety(policy)
        except PolicyValidationError as e:
            failures.append(str(e))

        return failures
