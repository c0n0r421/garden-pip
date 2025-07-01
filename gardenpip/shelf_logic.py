import json
import os


def load_shelves(path):
    """Load shelf layout data from a JSON file."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r') as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return []


def save_shelves(path, shelves):
    """Save shelf layout to JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as fh:
        json.dump(shelves, fh)
