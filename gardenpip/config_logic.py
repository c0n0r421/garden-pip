import json
import os
from typing import Any, Dict


def load_configs(path: str) -> Dict[str, Any]:
    """Load configuration entries from a JSON file."""
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def save_configs(path: str, data: Dict[str, Any]) -> None:
    """Save configuration data to a JSON file."""
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, indent=2)
