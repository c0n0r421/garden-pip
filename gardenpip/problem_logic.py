import json
from typing import Any, Dict, List, Optional


def load_problem_data(path: str) -> List[Dict[str, Any]]:
    """Load problem entries from a JSON file."""
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    return data.get("problems", [])


def search_problems(problems: List[Dict[str, Any]], plant: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return problems matching the given plant name."""
    if plant is None:
        return problems
    plant_l = plant.lower()
    return [p for p in problems if plant_l in p.get("title", "").lower() or plant_l in p.get("description", "").lower()]
