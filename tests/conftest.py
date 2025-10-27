# tests/conftest.py
# pytest fixtures

from unittest.mock import patch

import pytest


@pytest.fixture(scope="function", autouse=True)
def mock_telemetry_paths(tmp_path_factory, monkeypatch):
    """Automatically mock telemetry config paths for all tests to avoid permission issues."""
    test_config_dir = tmp_path_factory.mktemp("clearstone_config")
    test_config_file = test_config_dir / "config.json"

    monkeypatch.setattr("clearstone.utils.telemetry.CONFIG_DIR", test_config_dir)
    monkeypatch.setattr("clearstone.utils.telemetry.CONFIG_FILE", test_config_file)
    monkeypatch.setattr("clearstone.utils.telemetry._consent_message_shown", True)

    with patch("clearstone.utils.telemetry._telemetry_manager", None):
        yield
