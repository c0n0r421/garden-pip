import json
from typing import Any, Dict, List, Optional


def load_nutrient_data(path: str) -> Dict[str, Any]:
    """Load nutrient data from a JSON file."""
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def calculate_nutrients(
    data: Dict[str, Any],
    manufacturer: str,
    series: str,
    stage: str,
    plant_category: str,
    unit: str,
    volume: float,
    cal_mag: Optional[str],
) -> List[str]:
    """Return formatted nutrient lines for the given parameters."""
    nutrients = data.get("nutrients", [])
    entry = next(
        (n for n in nutrients if n.get("manufacturer") == manufacturer and n.get("series") == series),
        None,
    )
    if not entry:
        return []

    base_volume = entry.get("base_unit", {}).get(unit, {}).get("volume", 1)
    lines: List[str] = []
    stage_data = entry.get("stages", {}).get(stage, [])
    for comp in stage_data:
        conc = comp.get("concentration", {}).get(unit, 0)
        amt = conc * (float(volume) / base_volume)
        name = comp.get("name", "")
        u = comp.get("unit", {}).get(unit, "")
        lines.append(f"{name}: {amt:.1f} {u}")

    if cal_mag:
        supp = next(
            (s for s in data.get("cal_mag_supplements", []) if s.get("product") == cal_mag),
            None,
        )
        if supp:
            base_vol_s = supp.get("base_unit", {}).get(unit, {}).get("volume", 1)
            conc_s = supp.get("concentration", {}).get(unit, 0)
            amt_s = conc_s * (float(volume) / base_vol_s)
            lines.append(f"{cal_mag}: {amt_s:.1f} {supp.get('unit', '')}")

    return lines
