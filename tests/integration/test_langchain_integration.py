# tests/integration/test_langchain_integration.py

import pytest
from clearstone.integrations.langchain.callbacks import (
    PolicyCallbackHandler, PolicyViolationError, PolicyPauseError
)
from clearstone.core.policy import Policy, PolicyEngine, reset_policies
from clearstone.core.context import create_context, context_scope, PolicyContext
from clearstone.core.actions import ALLOW, BLOCK, PAUSE

@pytest.fixture(autouse=True)
def reset_policy_registry():
    reset_policies()

def test_handler_raises_if_no_context_is_active():
    """The handler must raise an error if a LangChain event fires outside a context."""
    @Policy(name="p")
    def p(context): return ALLOW
    engine = PolicyEngine()
    handler = PolicyCallbackHandler(engine)
    
    with pytest.raises(RuntimeError, match="requires an active PolicyContext"):
        handler.on_llm_start({}, [])

def test_handler_blocks_llm_call_on_block_decision():
    """A BLOCK decision from a policy should raise PolicyViolationError during on_llm_start."""
    @Policy(name="block_llm")
    def block_llm_policy(context: PolicyContext):
        if context.metadata.get("event_type") == "on_llm_start":
            return BLOCK("LLM usage is forbidden.")
        return ALLOW

    engine = PolicyEngine()
    handler = PolicyCallbackHandler(engine)
    ctx = create_context("user1", "agent1")

    with context_scope(ctx):
        with pytest.raises(PolicyViolationError) as exc_info:
            handler.on_llm_start({"name": "test_llm"}, ["prompt"])
        assert "LLM usage is forbidden" in str(exc_info.value)

def test_handler_blocks_tool_call_on_block_decision():
    """A BLOCK decision should raise PolicyViolationError during on_tool_start."""
    @Policy(name="block_dangerous_tool")
    def block_tool_policy(context: PolicyContext):
        if context.metadata.get("tool_name") == "shell_exec":
            return BLOCK("Shell execution is not allowed.")
        return ALLOW
    
    engine = PolicyEngine()
    handler = PolicyCallbackHandler(engine)
    ctx = create_context("user1", "agent1")

    with context_scope(ctx):
        with pytest.raises(PolicyViolationError):
            handler.on_tool_start({"name": "shell_exec"}, "ls -l")
        
        try:
            handler.on_tool_start({"name": "calculator"}, "2+2")
        except PolicyViolationError:
            pytest.fail("The calculator tool should have been allowed.")

def test_handler_pauses_on_pause_decision():
    """A PAUSE decision should raise a PolicyPauseError."""
    @Policy(name="pause_on_tool")
    def pause_policy(context: PolicyContext):
        return PAUSE

    engine = PolicyEngine()
    handler = PolicyCallbackHandler(engine)
    ctx = create_context("user1", "agent1")

    with context_scope(ctx):
        with pytest.raises(PolicyPauseError) as exc_info:
            handler.on_tool_start({"name": "deploy_to_prod"}, "v1.2.3")

def test_handler_enriches_context_for_evaluation():
    """The handler should add event-specific metadata to the context for policies to use."""
    captured_metadata = {}

    @Policy(name="context_inspector")
    def inspector_policy(context: PolicyContext):
        nonlocal captured_metadata
        captured_metadata = context.metadata
        return ALLOW

    engine = PolicyEngine()
    handler = PolicyCallbackHandler(engine)
    ctx = create_context("user1", "agent1", original_key="original_value")

    with context_scope(ctx):
        handler.on_tool_start({"name": "my_tool"}, "input string")

    assert captured_metadata["event_type"] == "on_tool_start"
    assert captured_metadata["tool_name"] == "my_tool"
    assert captured_metadata["tool_input"] == "input string"
    assert captured_metadata["original_key"] == "original_value"
