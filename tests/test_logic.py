import os
from gardenpip.nutrient_logic import load_nutrient_data, calculate_nutrients
from gardenpip.problem_logic import load_problem_data, search_problems
from gardenpip.shelf_logic import load_shelves, save_shelves

ROOT = os.path.dirname(os.path.dirname(__file__))


def test_calculate_nutrients_basic():
    path = os.path.join(ROOT, 'nutrients.json')
    data = load_nutrient_data(path)
    lines = calculate_nutrients(
        data,
        'General Hydroponics',
        'Flora Series',
        'Seedling',
        'Tomatoes',
        'metric',
        100,
        None,
    )
    assert any('Micro' in l for l in lines)
    assert any('Grow' in l for l in lines)
    assert any('Bloom' in l for l in lines)


def test_problem_search_by_plant():
    path = os.path.join(ROOT, 'hydroponicProblems.json')
    problems = load_problem_data(path)
    matches = search_problems(problems, plant='Cucumber')
    assert any('Cucumber' in p['title'] or 'cucumber' in p['title'].lower() for p in matches)


def test_shelf_save_and_load(tmp_path):
    data = [{'pos': [1, 2], 'size': [3, 4]}]
    json_path = tmp_path / 'shelves.json'
    save_shelves(str(json_path), data)
    loaded = load_shelves(str(json_path))
    assert loaded == data
