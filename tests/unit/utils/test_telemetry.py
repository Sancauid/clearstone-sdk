# tests/unit/utils/test_telemetry.py

import pytest
import os
import json
from unittest.mock import patch, MagicMock
from clearstone.utils.telemetry import TelemetryManager, get_telemetry_manager, _TELEMETRY_DISABLED_ENV_VAR

@pytest.fixture
def clean_env(monkeypatch, tmp_path):
  """Fixture to ensure a clean environment for each test."""
  monkeypatch.delenv(_TELEMETRY_DISABLED_ENV_VAR, raising=False)
  
  config_dir = tmp_path / ".clearstone"
  config_file = config_dir / "config.json"
  
  with patch('clearstone.utils.telemetry._telemetry_manager', None):
    with patch('clearstone.utils.telemetry.CONFIG_DIR', config_dir):
      with patch('clearstone.utils.telemetry.CONFIG_FILE', config_file):
        with patch('clearstone.utils.telemetry._consent_message_shown', True):
          yield

def test_telemetry_is_enabled_by_default(clean_env):
  """Test that telemetry is on by default with no configuration."""
  manager = TelemetryManager()
  assert manager.is_enabled is True

def test_telemetry_is_disabled_by_env_var(clean_env, monkeypatch):
  """Test that setting the environment variable disables telemetry."""
  monkeypatch.setenv(_TELEMETRY_DISABLED_ENV_VAR, "1")
  manager = TelemetryManager()
  assert manager.is_enabled is False

def test_telemetry_is_disabled_by_config_file(clean_env, tmp_path):
  """Test that a config file can disable telemetry."""
  config_dir = tmp_path / ".clearstone"
  config_file = config_dir / "config.json"
  config_dir.mkdir()
  with open(config_file, 'w') as f:
    json.dump({"telemetry": {"disabled": True}}, f)
  
  with patch('clearstone.utils.telemetry.CONFIG_DIR', config_dir):
    with patch('clearstone.utils.telemetry.CONFIG_FILE', config_file):
      with patch('clearstone.utils.telemetry._consent_message_shown', True):
        manager = TelemetryManager()
        assert manager.is_enabled is False

@patch('clearstone.utils.telemetry.TelemetryManager._send_event')
def test_record_event_sends_data_when_enabled(mock_send, clean_env):
  """Test that record_event calls the sender when telemetry is enabled."""
  manager = get_telemetry_manager()
  manager.is_enabled = True
  
  manager.record_event("test_event", {"key": "value"})
  
  import time
  time.sleep(0.1)
  
  mock_send.assert_called_once()
  call_args = mock_send.call_args[0][0]
  assert call_args["event_name"] == "test_event"
  assert call_args["payload"] == {"key": "value"}
  assert "session_id" in call_args

@patch('clearstone.utils.telemetry.TelemetryManager._send_event')
def test_record_event_does_nothing_when_disabled(mock_send, clean_env, monkeypatch):
  """Test that record_event does nothing when telemetry is disabled."""
  monkeypatch.setenv(_TELEMETRY_DISABLED_ENV_VAR, "1")
  manager = get_telemetry_manager()
  
  manager.record_event("test_event", {"key": "value"})

  import time
  time.sleep(0.1)
  
  mock_send.assert_not_called()

