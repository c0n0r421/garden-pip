import json
import os

import shutil
from datetime import datetime

from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.dropdownitem import MDDropDownItem
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ListProperty, StringProperty, BooleanProperty
from kivy.uix.scatter import Scatter
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.resources import resource_find

from gardenpip.nutrient_logic import load_nutrient_data, calculate_nutrients
from gardenpip.problem_logic import load_problem_data, search_problems
from gardenpip.shelf_logic import load_shelves, save_shelves

# Simple helper for displaying error popups
def show_error_popup(title, message):
    Popup(
        title=title,
        content=Label(text=message),
        size_hint=(None, None),
        size=(400, 200),
    ).open()

# Helper to load problem data
def load_hydroponic_problems():
    """Load and return problems from hydroponicProblems.json."""
    json_path = resource_find('hydroponicProblems.json')
    if not json_path:
        show_error_popup('Data Load Error', 'hydroponicProblems.json file not found.')
        return []
    try:
        return load_problem_data(json_path)
    except Exception as e:
        msg = f'Error loading {json_path}: {e}'
        print(msg)
        show_error_popup('Data Load Error', msg)
        return []

# Screen definitions
class MenuScreen(Screen):
    pass

class NutrientCalculatorScreen(Screen):
    manufacturers = ListProperty()
    series = ListProperty()
    stages = ListProperty()
    plant_categories = ListProperty()
    units = ListProperty(['metric', 'imperial'])
    cal_mag_supplements = ListProperty()
    results_text = StringProperty('')
    data_loaded = BooleanProperty(False)

    menu = None

    def on_pre_enter(self):
        # Load data once when entering the screen
        if not self.manufacturers:
            self.load_data()

    def load_data(self):
        json_path = resource_find('nutrients.json')
        if not json_path:
            msg = 'nutrients.json file not found.'
            self.results_text = msg
            show_error_popup('Data Load Error', msg)
            self.data_loaded = False
            return
        try:
            full = load_nutrient_data(json_path)
        except Exception as e:
            msg = f'Error loading nutrients data: {e}'
            self.results_text = msg
            show_error_popup('Data Load Error', msg)
            self.data_loaded = False
            return

        self.nutrient_data = full['nutrients']
        self.calmag_data = full['cal_mag_supplements']
        self.plant_cat_data = full.get('plant_categories', {})
        # Populate initial dropdowns
        self.manufacturers = [d['manufacturer'] for d in self.nutrient_data]
        self.plant_categories = list(self.plant_cat_data.keys())
        self.cal_mag_supplements = [c['product'] for c in self.calmag_data]
        self.data_loaded = True

    def open_dropdown(self, caller, items, callback=None):
        menu_items = [
            {
                'viewclass': 'OneLineListItem',
                'text': item,
                'on_release': lambda x=item: self._set_item(caller, x, callback)
            }
            for item in items
        ]
        if self.menu:
            self.menu.dismiss()
        self.menu = MDDropdownMenu(caller=caller, items=menu_items, width_mult=4)
        self.menu.open()

    def _set_item(self, caller, text_item, callback):
        caller.text = text_item
        if self.menu:
            self.menu.dismiss()
        if callback:
            callback(text_item)

    def on_manufacturer_select(self, manufacturer):
        # Filter series & stages when manufacturer changes
        item = next((d for d in self.nutrient_data if d['manufacturer'] == manufacturer), None)
        if item:
            self.series = [item['series']]
            self.stages = list(item['stages'].keys())
        else:
            self.series = []
            self.stages = []

    def calculate(self):
        # Gather inputs
        manu = self.ids.manufacturer.text
        series = self.ids.series.text
        stage = self.ids.stage.text
        plant_cat = self.ids.plant_category.text
        unit = self.ids.unit.text
        # Validate selections against loaded data
        if manu not in self.manufacturers:
            self.results_text = 'Select a valid manufacturer.'
            return
        # Verify nutrient series exists for the selected manufacturer
        nut_item = next((d for d in self.nutrient_data
                         if d['manufacturer'] == manu and d['series'] == series), None)
        if not nut_item:
            self.results_text = 'Select a valid nutrient series.'
            return
        if stage not in nut_item['stages']:
            self.results_text = 'Select a valid growth stage.'
            return
        if plant_cat not in self.plant_cat_data:
            self.results_text = 'Select a valid plant category.'
            return
        try:
            volume = float(self.ids.volume.text)
        except ValueError:
            self.results_text = 'Enter a valid volume.'
            return
        if volume <= 0:
            self.results_text = 'Enter a volume greater than zero.'
            return
        calmag = self.ids.calmag.text

        try:
            lines = calculate_nutrients(
                {
                    'nutrients': self.nutrient_data,
                    'cal_mag_supplements': self.calmag_data,
                    'plant_categories': self.plant_cat_data,
                },
                manu,
                series,
                stage,
                plant_cat,
                unit,
                volume,
                calmag,
            )
        except Exception as e:
            self.results_text = f'Calculation error: {e}'
            return

        self.results_text = '\n'.join(lines)

        # Log schedule entry on success
        if lines:
            self.log_schedule({
                'date': datetime.now().isoformat(),
                'manufacturer': manu,
                'series': series,
                'stage': stage,
                'plant_category': plant_cat,
                'unit': unit,
                'volume': volume,
                'cal_mag': calmag,
                'lines': lines,
            })

    def log_schedule(self, entry):
        app = MDApp.get_running_app()
        base_dir = getattr(app, 'user_data_dir',
                           os.path.join(os.path.dirname(__file__), 'data'))
        os.makedirs(base_dir, exist_ok=True)
        log_path = os.path.join(base_dir, 'schedule_log.json')
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
            except (json.JSONDecodeError, OSError) as e:
                self.results_text += f"\nFailed to read log file: {e}"
                data = []
            except Exception as e:
                self.results_text += f"\nUnexpected error reading log file: {e}"
                print(e)
                data = []
        else:
            data = []
        data.append(entry)
        try:
            with open(log_path, 'w', encoding='utf-8') as fh:
                json.dump(data, fh, indent=2)
        except OSError as e:
            self.results_text += f"\nFailed to write log file: {e}"
        except Exception as e:
            self.results_text += f"\nUnexpected error writing log file: {e}"
            print(e)


class ScheduleLogScreen(Screen):
    log_entries = ListProperty([])
    status_text = StringProperty('')

    def on_pre_enter(self):
        self.load_log()

    def load_log(self):
        app = MDApp.get_running_app()
        base_dir = getattr(app, 'user_data_dir',
                           os.path.join(os.path.dirname(__file__), 'data'))
        os.makedirs(base_dir, exist_ok=True)
        log_path = os.path.join(base_dir, 'schedule_log.json')
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
            except (json.JSONDecodeError, OSError) as e:
                self.status_text = f"Failed to read log: {e}"
                data = []
            except Exception as e:
                self.status_text = f"Unexpected error reading log: {e}"
                print(e)
                data = []
        else:
            data = []
        self.log_entries = [
            f"{e['date']} - {e['plant_category']} {e['stage']} {e['volume']} {e['unit']}"
            for e in data
        ]

    def clear_log(self):
        app = MDApp.get_running_app()
        base_dir = getattr(app, 'user_data_dir',
                           os.path.join(os.path.dirname(__file__), 'data'))
        os.makedirs(base_dir, exist_ok=True)
        log_path = os.path.join(base_dir, 'schedule_log.json')
        try:
            if os.path.exists(log_path):
                os.remove(log_path)
        except OSError as e:
            self.status_text = f"Failed to clear log: {e}"
        except Exception as e:
            self.status_text = f"Unexpected error clearing log: {e}"
            print(e)
        self.load_log()

    def export_log(self):
        app = MDApp.get_running_app()
        base_dir = getattr(app, 'user_data_dir',
                           os.path.join(os.path.dirname(__file__), 'data'))
        os.makedirs(base_dir, exist_ok=True)
        log_path = os.path.join(base_dir, 'schedule_log.json')
        if os.path.exists(log_path):
            export_path = os.path.join(base_dir, 'schedule_log_export.json')
            try:
                shutil.copy(log_path, export_path)
            except OSError as e:
                self.status_text = f"Failed to export log: {e}"
            except Exception as e:
                self.status_text = f"Unexpected error exporting log: {e}"
                print(e)
        else:
            self.status_text = 'No log file to export.'

class ProblemSearchScreen(Screen):
    problems = []
    plant_options = ListProperty()
    stage_options = ListProperty()
    medium_options = ListProperty()
    system_options = ListProperty()
    menu = None

    def on_pre_enter(self):
        if not self.problems:
            self.problems = load_hydroponic_problems()

        plants = set()
        stages = set()
        media = set()
        systems = set()
        for prob in self.problems:
            plants.update(prob.get('applicablePlants', []))
            stages.update(prob.get('growthStages', []))
            media.update(prob.get('growMedia', []))
            systems.update(prob.get('hydroponicSystems', []))

        self.plant_options = sorted(plants)
        self.stage_options = sorted(stages)
        self.medium_options = sorted(media)
        self.system_options = ['-- All Systems --'] + sorted(systems)
        if not self.ids.problem_system.text:
            self.ids.problem_system.text = '-- All Systems --'

    def open_dropdown(self, caller, items):
        menu_items = [
            {
                'viewclass': 'OneLineListItem',
                'text': item,
                'on_release': lambda x=item: self._set_item(caller, x)
            }
            for item in items
        ]
        if self.menu:
            self.menu.dismiss()
        self.menu = MDDropdownMenu(caller=caller, items=menu_items, width_mult=4)
        self.menu.open()

    def _set_item(self, caller, text_item):
        caller.text = text_item
        if self.menu:
            self.menu.dismiss()

    def search(self):
        if not self.problems:
            self.problems = load_hydroponic_problems()

        plant = self.ids.problem_plant.text.strip()
        stage = self.ids.problem_stage.text.strip()
        medium = self.ids.problem_medium.text.strip()
        system = self.ids.problem_system.text.strip()

        if plant.startswith('Select'):
            plant = ''
        if stage.startswith('Select'):
            stage = ''
        if medium.startswith('Select'):
            medium = ''

        matches = search_problems(
            self.problems,
            plant=plant,
            stage=stage,
            medium=medium,
            system=system,
        )

        if not matches:
            self.ids.problem_results.text = 'No matching problems found.'
        else:
            lines = [f"{p['title']}: {p.get('description', '')}" for p in matches]
            self.ids.problem_results.text = '\n\n'.join(lines)


class PlantWidget(Scatter):
    """Draggable/resizable representation of a plant."""

    def __init__(self, data, update_cb, **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.update_cb = update_cb
        self.do_rotation = False
        self.do_scale = True
        self.add_widget(Label(text='\U0001F331', font_size=30))
        self.size = data.get('size', (50, 50))
        self.pos = data.get('pos', (100, 100))

    def on_touch_up(self, touch):
        result = super().on_touch_up(touch)
        if self.collide_point(*touch.pos):
            self.data['pos'] = list(self.pos)
            self.data['size'] = list(self.size)
            self.update_cb()
        return result


class ShelfLayoutScreen(Screen):
    shelves = ListProperty()

    def on_pre_enter(self):
        self.load_shelves()

    def load_shelves(self):
        app = MDApp.get_running_app()
        base_dir = getattr(app, 'user_data_dir', os.path.dirname(__file__))
        shelves_path = os.path.join(base_dir, 'shelves.json')
        self.shelves = load_shelves(shelves_path)

        self.ids.layout.clear_widgets()
        for plant in self.shelves:
            self.add_plant_widget(plant)

    def add_plant_widget(self, plant=None):
        if plant is None:
            plant = {'pos': [100, 100], 'size': [50, 50]}
            self.shelves.append(plant)
        widget = PlantWidget(plant, self.save_shelves)
        self.ids.layout.add_widget(widget)

    def save_shelves(self, *args):
        app = MDApp.get_running_app()
        base_dir = getattr(app, 'user_data_dir', os.path.dirname(__file__))
        shelves_path = os.path.join(base_dir, 'shelves.json')
        try:
            save_shelves(shelves_path, self.shelves)
        except OSError as e:
            print(f"Error saving shelves: {e}")

    def on_leave(self):
        self.save_shelves()



class GardenPipApp(MDApp):
    def build(self):
        kv_path = os.path.join(os.path.dirname(__file__), 'gardenpip.kv')
        self.sm = Builder.load_file(kv_path)
        return self.sm

if __name__ == '__main__':
    GardenPipApp().run()
