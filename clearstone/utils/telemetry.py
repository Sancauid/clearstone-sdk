# clearstone/utils/telemetry.py

import os
import sys
import uuid
import json
import platform
import threading
from threading import Lock
from urllib import request
from pathlib import Path
from typing import Dict, Any, Optional

TELEMETRY_ENDPOINT = "https://telemetry.clearstone.dev/event"
CONFIG_DIR = Path.home() / ".clearstone"
CONFIG_FILE = CONFIG_DIR / "config.json"
SESSION_ID = f"sess_{uuid.uuid4().hex}"
_TELEMETRY_DISABLED_ENV_VAR = "CLEARSTONE_TELEMETRY_DISABLED"
_consent_message_shown = False

class TelemetryManager:
  """
  Manages the collection and sending of anonymous, opt-out usage data.
  Designed to be transparent, respectful of privacy, and have zero performance impact.
  """
  def __init__(self):
    self.is_enabled = self._check_if_enabled()
    self.anonymous_id = self._get_or_create_anonymous_id()
    self._queue = []
    self._lock = threading.Lock()
    
    if self.is_enabled:
      self._show_consent_message()

  def _check_if_enabled(self) -> bool:
    """Checks environment variables and config files to see if telemetry is disabled."""
    if os.environ.get(_TELEMETRY_DISABLED_ENV_VAR, "0").strip().lower() in ["1", "true"]:
      return False
    
    try:
      if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
          config = json.load(f)
        if config.get("telemetry", {}).get("disabled", False):
          return False
    except (IOError, json.JSONDecodeError):
      pass
        
    return True

  def _get_or_create_anonymous_id(self) -> str:
    """
    Retrieves a persistent anonymous user ID from the config file,
    or creates a new one if it doesn't exist.
    """
    CONFIG_DIR.mkdir(exist_ok=True)
    config = {}
    if CONFIG_FILE.exists():
      try:
        with open(CONFIG_FILE, 'r') as f:
          config = json.load(f)
      except (IOError, json.JSONDecodeError):
        pass

    if "anonymous_id" not in config:
      config["anonymous_id"] = f"user_{uuid.uuid4().hex}"
      try:
        with open(CONFIG_FILE, 'w') as f:
          json.dump(config, f, indent=2)
      except IOError:
        pass
    
    return config["anonymous_id"]

  def _show_consent_message(self):
    """Prints the one-time consent message to the user's console."""
    global _consent_message_shown
    if not _consent_message_shown:
      print("\n[Clearstone Telemetry] To help improve our open-source tools, Clearstone collects anonymous usage statistics.", file=sys.stderr)
      print(f"This is completely anonymous and helps us understand how the SDK is used. To disable, set the {_TELEMETRY_DISABLED_ENV_VAR}=1 environment variable.", file=sys.stderr)
      print("For more info, please see: [Link to your future telemetry docs page]\n", file=sys.stderr)
      _consent_message_shown = True

  def record_event(self, event_name: str, payload: Dict[str, Any]):
    """Records a telemetry event to be sent in the background."""
    if not self.is_enabled:
      return

    sdk_version = "1.0.0"

    full_payload = {
      "anonymous_id": self.anonymous_id,
      "session_id": SESSION_ID,
      "event_name": event_name,
      "sdk_version": sdk_version,
      "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
      "platform": platform.system().lower(),
      "payload": payload,
    }

    thread = threading.Thread(target=self._send_event, args=(full_payload,), daemon=True)
    thread.start()

  def _send_event(self, data: Dict[str, Any]):
    """The actual network call. Must never crash the user's application."""
    try:
      json_data = json.dumps(data).encode('utf-8')
      req = request.Request(TELEMETRY_ENDPOINT, data=json_data, headers={'Content-Type': 'application/json'})
      request.urlopen(req, timeout=2)
    except Exception:
      pass

_telemetry_manager: Optional[TelemetryManager] = None
_manager_lock = Lock()

def get_telemetry_manager() -> TelemetryManager:
  """Gets the global singleton TelemetryManager instance."""
  global _telemetry_manager
  with _manager_lock:
    if _telemetry_manager is None:
      _telemetry_manager = TelemetryManager()
    return _telemetry_manager

