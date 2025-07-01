import json
import sys
import types

# Stub out heavy kivy and kivymd modules so main.py can be imported
stub_modules = {
    'kivymd.app': ['MDApp'],
    'kivymd.uix.menu': ['MDDropdownMenu'],
    'kivymd.uix.toolbar': ['MDTopAppBar'],
    'kivymd.uix.dropdownitem': ['MDDropDownItem'],
    'kivymd.uix.button': ['MDRaisedButton'],
    'kivymd.uix.label': ['MDLabel'],
    'kivymd.uix.textfield': ['MDTextField'],
    'kivymd.uix.boxlayout': ['MDBoxLayout'],
    'kivymd.uix.gridlayout': ['MDGridLayout'],
    'kivy.lang': ['Builder'],
    'kivy.uix.screenmanager': ['ScreenManager', 'Screen'],
    'kivy.properties': ['ListProperty', 'StringProperty', 'BooleanProperty'],
    'kivy.uix.scatter': ['Scatter'],
    'kivy.uix.label': ['Label'],
    'kivy.uix.popup': ['Popup'],
    'kivy.resources': ['resource_find'],
}
class _Dummy:
    def __init__(self, *a, **k):
        pass

for name, attrs in stub_modules.items():
    mod = types.ModuleType(name)
    for attr in attrs:
        if name == 'kivy.resources' and attr == 'resource_find':
            setattr(mod, attr, lambda x: x)
        elif name == 'kivy.properties':
            setattr(mod, attr, lambda *a, **k: None)
        else:
            setattr(mod, attr, _Dummy)
    sys.modules[name] = mod

# Prepare minimal MDApp stub
class DummyMDApp:
    @staticmethod
    def get_running_app():
        return None
sys.modules['kivymd.app'].MDApp = DummyMDApp

import importlib.util
spec = importlib.util.spec_from_file_location('main', 'main.py')
main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main)


def test_log_written_when_user_data_dir_missing(tmp_path, monkeypatch):
    base = tmp_path / 'data_dir'
    dummy_app = types.SimpleNamespace(user_data_dir=str(base))
    monkeypatch.setattr(main.MDApp, 'get_running_app', lambda: dummy_app)

    screen = main.NutrientCalculatorScreen(name='calc')
    entry = {
        'date': '2024-01-01',
        'manufacturer': 'M',
        'series': 'S',
        'stage': 'Stage',
        'plant_category': 'Cat',
        'unit': 'metric',
        'volume': 1,
        'cal_mag': None,
        'lines': ['line'],
    }

    screen.log_schedule(entry)

    log_file = base / 'schedule_log.json'
    assert log_file.exists()
    with open(log_file, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    assert entry in data
