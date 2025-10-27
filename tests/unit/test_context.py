# tests/unit/test_context.py

import pytest
import asyncio
from dataclasses import FrozenInstanceError
from clearstone.core.context import (
    PolicyContext,
    get_current_context,
    set_current_context,
    context_scope,
    create_context,
)


def test_context_creation_and_defaults():
    """Test creating a PolicyContext with required and default values."""
    ctx = create_context(
        user_id="user-123", agent_id="agent-search-alpha", role="admin"
    )
    assert ctx.user_id == "user-123"
    assert ctx.agent_id == "agent-search-alpha"
    assert ctx.metadata["role"] == "admin"
    assert isinstance(ctx.request_id, str) and len(ctx.request_id) > 0
    assert isinstance(ctx.session_id, str) and len(ctx.session_id) > 0


def test_context_is_immutable():
    """Test that PolicyContext is a frozen dataclass."""
    ctx = create_context("user1", "agent1")
    with pytest.raises(FrozenInstanceError):
        ctx.user_id = "modified-user"


def test_manual_context_management_set_get():
    """Test the manual set_current_context and get_current_context functions."""
    ctx = create_context("user1", "agent1")
    assert get_current_context() is None
    set_current_context(ctx)
    assert get_current_context() == ctx
    assert PolicyContext.current() == ctx
    set_current_context(None)
    assert get_current_context() is None


def test_context_scope_manager_restores_context():
    """Test that the context_scope manager correctly sets and restores context."""
    ctx1 = create_context("user1", "agent1")
    ctx2 = create_context("user2", "agent2")

    set_current_context(ctx1)
    assert get_current_context() == ctx1

    with context_scope(ctx2):
        assert get_current_context() == ctx2

    assert get_current_context() == ctx1, "Context was not restored after scope exit."


@pytest.mark.asyncio
async def test_context_is_async_safe():
    """Test that context is properly isolated across concurrent async tasks."""
    results = {}

    async def task(user_id, agent_id, delay):
        ctx = create_context(user_id, agent_id)
        with context_scope(ctx):
            await asyncio.sleep(delay)
            current_ctx = get_current_context()
            results[user_id] = current_ctx.user_id

    await asyncio.gather(task("user1", "agentA", 0.02), task("user2", "agentB", 0.01))

    assert results["user1"] == "user1"
    assert results["user2"] == "user2"
