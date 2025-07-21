import json
import os
from typing import Any, Dict

# default configuration values used when no entry is found
DEFAULT_CONFIG: Dict[str, Any] = {
    "screensaver_timeout": 300,  # seconds
}


def load_configs(path: str) -> Dict[str, Any]:
    """Load configuration entries from a JSON file."""
    if not os.path.exists(path):
        # return defaults when config file doesn't exist
        return DEFAULT_CONFIG.copy()
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def save_configs(path: str, data: Dict[str, Any]) -> None:
    """Save configuration data to a JSON file."""
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, indent=2)


def get_screensaver_timeout(config: Dict[str, Any]) -> int:
    """Return idle timeout in seconds from configuration data."""
    try:
        return int(config.get("screensaver_timeout", DEFAULT_CONFIG["screensaver_timeout"]))
    except (TypeError, ValueError):
        return DEFAULT_CONFIG["screensaver_timeout"]
