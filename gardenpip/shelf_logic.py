import json
import os
from typing import Any, List


def load_shelves(path: str) -> List[Any]:
    """Load shelf data from JSON file."""
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def save_shelves(path: str, data: List[Any]) -> None:
    """Save shelf data to JSON file."""
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, indent=2)
