# examples/15_human_in_the_loop.py
import dataclasses
from clearstone import (
    Policy,
    PolicyEngine,
    create_context,
    context_scope,
    ALLOW,
    PAUSE,
    InterventionClient,
)
from clearstone.integrations.langchain import PolicyCallbackHandler, PolicyPauseError
from clearstone.core.policy import reset_policies

reset_policies()


@Policy(name="require_approval_for_large_spend", priority=100)
def approval_policy(context):
    """Pauses execution if a transaction is over $1000 and not yet approved."""
    amount = context.metadata.get("amount", 0)
    is_approved = context.metadata.get("is_approved", False)

    if amount > 1000 and not is_approved:
        return PAUSE(f"Transaction of ${amount} requires manual approval.")

    return ALLOW


def run_financial_transaction(engine: PolicyEngine, context):
    """Simulates running a transaction that is subject to policy checks."""
    handler = PolicyCallbackHandler(engine)

    print(
        f"\nAttempting transaction for user '{context.user_id}' of amount ${context.metadata.get('amount', 0)}..."
    )

    try:
        with context_scope(context):
            handler.on_tool_start(serialized={"name": "execute_payment"}, input_str="")

        print("✅ Transaction successful without intervention.")
        return True

    except PolicyPauseError as e:
        print(
            f"⏸️ Transaction Paused by policy '{e.decision.metadata.get('policy_name', 'unknown')}'."
        )

        intervention_client = InterventionClient()
        intervention_client.request_intervention(e.decision)
        intervention_id = e.decision.metadata.get("intervention_id")

        if intervention_client.wait_for_approval(intervention_id):
            print("Re-running transaction with approval...")
            approved_context = dataclasses.replace(
                context, metadata={**context.metadata, "is_approved": True}
            )
            return run_financial_transaction(engine, approved_context)
        else:
            print("Transaction aborted by user.")
            return False


if __name__ == "__main__":
    engine = PolicyEngine()

    print("--- SCENARIO 1: Small transaction (should pass automatically) ---")
    small_transaction_ctx = create_context("user-1", "finance-agent", amount=500)
    run_financial_transaction(engine, small_transaction_ctx)

    print("\n" + "=" * 50 + "\n")

    print("--- SCENARIO 2: Large transaction (should trigger human approval) ---")
    large_transaction_ctx = create_context("user-2", "finance-agent", amount=2500)
    run_financial_transaction(engine, large_transaction_ctx)
