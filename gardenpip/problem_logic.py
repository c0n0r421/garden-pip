import json


def load_problem_data(path):
    """Return list of problems from JSON file."""
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    return data.get('problems', [])


def search_problems(problems, plant='', stage='', medium='', system=''):
    """Filter problem list by the provided fields."""
    matches = []
    for prob in problems:
        if plant and plant not in prob.get('applicablePlants', []):
            continue
        if stage and stage not in prob.get('growthStages', []):
            continue
        if medium and medium not in prob.get('growMedia', []):
            continue
        if system and system not in ('--', '-- All Systems --') and \
                system not in prob.get('hydroponicSystems', []):
            continue
        matches.append(prob)
    return matches
