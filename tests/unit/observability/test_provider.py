# tests/unit/observability/test_provider.py

import pytest

from clearstone.observability.provider import (
    TracerProvider,
    get_tracer_provider,
    reset_tracer_provider,
)
from clearstone.observability.tracer import Tracer


@pytest.fixture
def provider(tmp_path):
    """Fixture to create a TracerProvider with a temporary db path."""
    db_path = tmp_path / "provider_test.db"
    return TracerProvider(db_path=str(db_path))


@pytest.fixture(autouse=True)
def clean_global_provider():
    """Ensure each test starts with a clean global provider."""
    reset_tracer_provider()
    yield
    reset_tracer_provider()


def test_provider_initializes_storage_and_buffer(provider):
    """Test that the provider correctly sets up its components."""
    assert provider.trace_store is not None
    assert provider.span_buffer is not None
    assert provider.span_buffer._writer is provider.trace_store


def test_get_tracer_returns_configured_tracer(provider):
    """Test that tracers obtained from the provider share the same buffer."""
    tracer1 = provider.get_tracer("agent_A")
    tracer2 = provider.get_tracer("agent_B")
    tracer_a_again = provider.get_tracer("agent_A")

    assert isinstance(tracer1, Tracer)
    assert tracer1 is tracer_a_again
    assert tracer1 is not tracer2

    assert tracer1._buffer is provider.span_buffer
    assert tracer2._buffer is provider.span_buffer


def test_global_get_tracer_provider_is_singleton():
    """Test that the global provider is a singleton."""
    provider1 = get_tracer_provider()
    provider2 = get_tracer_provider()
    assert provider1 is provider2
