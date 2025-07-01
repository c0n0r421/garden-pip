import json


def load_nutrient_data(path):
    """Load nutrient configuration from a JSON file."""
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def calculate_nutrients(data, manufacturer, series, stage, plant_category,
                         unit, volume, cal_mag=None):
    """Return formatted nutrient amounts for the provided selection."""
    nutrient_data = data['nutrients']
    calmag_data = data.get('cal_mag_supplements', [])
    plant_cat_data = data.get('plant_categories', {})

    nut_item = next(
        (d for d in nutrient_data
         if d['manufacturer'] == manufacturer and d['series'] == series),
        None,
    )
    if not nut_item:
        raise ValueError('Invalid manufacturer or series')
    if stage not in nut_item['stages']:
        raise ValueError('Invalid growth stage')
    if plant_category not in plant_cat_data:
        raise ValueError('Invalid plant category')

    base = nut_item['base_unit'][unit]
    factor = volume / base['volume']

    cat_adj = plant_cat_data.get(plant_category, {}).get(
        'recommended_adjustments', {}
    )
    stage_adj = cat_adj.get(stage, {})

    lines = []
    for comp in nut_item['stages'][stage]:
        base_amt = comp['concentration'][unit] * factor
        adj = stage_adj.get(comp['name'], 0)
        amt = base_amt + adj
        unit_name = comp['unit'][unit]
        if adj:
            lines.append(
                f"{comp['name']}: {amt:.2f} {unit_name} (adjusted {adj})"
            )
        else:
            lines.append(f"{comp['name']}: {amt:.2f} {unit_name}")

    if cal_mag:
        cal_item = next((c for c in calmag_data if c['product'] == cal_mag), None)
        if cal_item:
            base2 = cal_item['base_unit'][unit]
            factor2 = volume / base2['volume']
            cal_amt = cal_item['concentration'][unit] * factor2
            lines.append(f"{cal_item['product']}: {cal_amt:.2f} {cal_item['unit']}")

    return lines
