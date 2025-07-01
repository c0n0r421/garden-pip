import json
import os

import shutil
from datetime import datetime

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ListProperty, StringProperty
from kivy.uix.scatter import Scatter
from kivy.uix.label import Label

# Helper to load problem data
def load_hydroponic_problems():
    """Load and return problems from hydroponicProblems.json."""
    json_path = os.path.join(os.path.dirname(__file__), 'hydroponicProblems.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        return data.get('problems', [])
    except Exception as e:
        print(f'Error loading {json_path}: {e}')
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

    def on_pre_enter(self):
        # Load data once when entering the screen
        if not self.manufacturers:
            self.load_data()

    def load_data(self):
        json_path = os.path.join(os.path.dirname(__file__), 'nutrients.json')
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                full = json.load(f)
        except FileNotFoundError:
            self.results_text = f'Unable to find nutrients data at {json_path}.'
            return
        except json.JSONDecodeError:
            self.results_text = 'Error parsing nutrients.json.'
            return
        except Exception as e:
            self.results_text = f'Error loading nutrients data: {e}'
            return

        self.nutrient_data = full['nutrients']
        self.calmag_data = full['cal_mag_supplements']
        self.plant_cat_data = full.get('plant_categories', {})
        # Populate initial dropdowns
        self.manufacturers = [d['manufacturer'] for d in self.nutrient_data]
        self.plant_categories = list(self.plant_cat_data.keys())
        self.cal_mag_supplements = [c['product'] for c in self.calmag_data]

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
        calmag = self.ids.calmag.text

        # Compute factor based on base unit
        base = nut_item['base_unit'][unit]
        factor = volume / base['volume']

        lines = []
        # Calculate each component
        for comp in nut_item['stages'][stage]:
            amt = comp['concentration'][unit] * factor
            lines.append(f"{comp['name']}: {amt:.2f} {comp['unit'][unit]}")

        # Cal-Mag supplement
        cal_item = next((c for c in self.calmag_data if c['product'] == calmag), None)
        if cal_item:
            base2 = cal_item['base_unit'][unit]
            factor2 = volume / base2['volume']
            cal_amt = cal_item['concentration'][unit] * factor2
            lines.append(f"{cal_item['product']}: {cal_amt:.2f} {cal_item['unit']}")

        # Plant category adjustments
        cat_adj = self.plant_cat_data.get(plant_cat, {}).get('recommended_adjustments', {})
        stage_adj = cat_adj.get(stage, {})
        for comp in nut_item['stages'][stage]:
            adj = stage_adj.get(comp['name'], 0)
            if adj:
                lines.append(f"Adjustment {comp['name']}: {adj}")

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
        app = App.get_running_app()
        log_path = os.path.join(app.user_data_dir, 'schedule_log.json')
        os.makedirs(app.user_data_dir, exist_ok=True)
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
            except Exception as e:
                self.results_text += f"\nFailed to read log file: {e}"
                data = []
        else:
            data = []
        data.append(entry)
        try:
            with open(log_path, 'w', encoding='utf-8') as fh:
                json.dump(data, fh, indent=2)
        except Exception as e:
            self.results_text += f"\nFailed to write log file: {e}"


class ScheduleLogScreen(Screen):
    log_entries = ListProperty([])
    status_text = StringProperty('')

    def on_pre_enter(self):
        self.load_log()

    def load_log(self):
        app = App.get_running_app()
        log_path = os.path.join(app.user_data_dir, 'schedule_log.json')
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
            except Exception as e:
                self.status_text = f"Failed to read log: {e}"
                data = []
        else:
            data = []
        self.log_entries = [
            f"{e['date']} - {e['plant_category']} {e['stage']} {e['volume']} {e['unit']}"
            for e in data
        ]

    def clear_log(self):
        app = App.get_running_app()
        log_path = os.path.join(app.user_data_dir, 'schedule_log.json')
        try:
            if os.path.exists(log_path):
                os.remove(log_path)
        except Exception as e:
            self.status_text = f"Failed to clear log: {e}"
        self.load_log()

    def export_log(self):
        app = App.get_running_app()
        log_path = os.path.join(app.user_data_dir, 'schedule_log.json')
        if os.path.exists(log_path):
            export_path = os.path.join(app.user_data_dir, 'schedule_log_export.json')
            try:
                shutil.copy(log_path, export_path)
            except Exception as e:
                self.status_text = f"Failed to export log: {e}"
        else:
            self.status_text = 'No log file to export.'

class ProblemSearchScreen(Screen):
    problems = []

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

        self.ids.problem_plant.values = sorted(plants)
        self.ids.problem_stage.values = sorted(stages)
        self.ids.problem_medium.values = sorted(media)
        self.ids.problem_system.values = ['-- All Systems --'] + sorted(systems)
        if not self.ids.problem_system.text:
            self.ids.problem_system.text = '-- All Systems --'

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

        matches = []
        for prob in self.problems:
            if plant and plant not in prob.get('applicablePlants', []):
                continue
            if stage and stage not in prob.get('growthStages', []):
                continue
            if medium and medium not in prob.get('growMedia', []):
                continue
            if system and system not in ('--', '-- All Systems --') \
                    and system not in prob.get('hydroponicSystems', []):
                continue
            matches.append(prob)

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
        app = App.get_running_app()
        base_dir = getattr(app, 'user_data_dir', os.path.dirname(__file__))
        shelves_path = os.path.join(base_dir, 'shelves.json')
        if os.path.exists(shelves_path):
            try:
                with open(shelves_path, 'r') as fh:
                    self.shelves = json.load(fh)
            except (json.JSONDecodeError, OSError):
                self.shelves = []
        else:
            self.shelves = []

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
        app = App.get_running_app()
        base_dir = getattr(app, 'user_data_dir', os.path.dirname(__file__))
        shelves_path = os.path.join(base_dir, 'shelves.json')
        os.makedirs(base_dir, exist_ok=True)
        try:
            with open(shelves_path, 'w') as fh:
                json.dump(self.shelves, fh)
        except OSError as e:
            print(f"Error saving shelves: {e}")

    def on_leave(self):
        self.save_shelves()

# Kivy UI definition
kv = '''
ScreenManager:
    MenuScreen:
    NutrientCalculatorScreen:
    ProblemSearchScreen:
    ShelfLayoutScreen:


<MenuScreen>:
    name: 'menu'
    BoxLayout:
        orientation: 'vertical'
        spacing: 10
        padding: 20
        Label:
            text: 'Garden Pip Tools'
            font_size: '24sp'
        Button:
            text: '🌿 Nutrient Calculator'
            on_release: app.sm.current = 'nutrient_calc'
        Button:
            text: '🔍 Hydroponic Problem Search'
            on_release: app.sm.current = 'problem_search'
        Button:

            text: '\U0001F4DA Shelf Layout'
            on_release: app.sm.current = 'shelf_layout'


<NutrientCalculatorScreen>:
    name: 'nutrient_calc'
    BoxLayout:
        orientation: 'vertical'
        ScrollView:
            GridLayout:
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                padding: 10
                spacing: 10
                Spinner:
                    id: manufacturer
                    text: 'Select Manufacturer'
                    values: root.manufacturers
                    on_text: root.on_manufacturer_select(self.text)
                Spinner:
                    id: series
                    text: 'Select Series'
                    values: root.series
                Spinner:
                    id: stage
                    text: 'Select Stage'
                    values: root.stages
                Spinner:
                    id: plant_category
                    text: 'Select Plant Category'
                    values: root.plant_categories
                Spinner:
                    id: unit
                    text: 'metric'
                    values: root.units
                TextInput:
                    id: volume
                    hint_text: 'Enter volume'
                    input_filter: 'float'
                Spinner:
                    id: calmag
                    text: 'Select Cal-Mag'
                    values: root.cal_mag_supplements
                Button:
                    text: 'Calculate'
                    size_hint_y: None
                    height: 40
                    on_release: root.calculate()
                Label:
                    id: results
                    text: root.results_text
                    size_hint_y: None
                    height: self.texture_size[1]
        Button:
            text: '← Back to menu'
            size_hint_y: None
            height: 40
            on_release: app.sm.current = 'menu'

<ShelfLayoutScreen>:
    name: 'shelf_layout'
    BoxLayout:
        orientation: 'vertical'
        FloatLayout:
            id: layout
            size_hint_y: 0.9
            canvas.before:
                Color:
                    rgba: 0.9, 0.9, 0.9, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
                Color:
                    rgba: 0, 0, 0, 1
                Rectangle:
                    pos: self.x, self.y + self.height * 0.33
                    size: self.width, 2
                Rectangle:
                    pos: self.x, self.y + self.height * 0.66
                    size: self.width, 2
        BoxLayout:
            size_hint_y: 0.1
            Button:
                text: 'Add Plant'
                on_release: root.add_plant_widget()
            Button:
                text: '← Back to menu'
                on_release: app.sm.current = 'menu'

<ProblemSearchScreen>:
    name: 'problem_search'
    BoxLayout:
        orientation: 'vertical'
        ScrollView:
            GridLayout:
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                padding: 10
                spacing: 10
                Spinner:
                    id: problem_plant
                    text: 'Select Plant'
                    values: []
                Spinner:
                    id: problem_stage
                    text: 'Select Growth Stage'
                    values: []
                Spinner:
                    id: problem_medium
                    text: 'Select Grow Medium'
                    values: []
                Spinner:
                    id: problem_system
                    text: '-- All Systems --'
                    values: ['--']
                TextInput:
                    id: problem_description
                    hint_text: 'Describe the issue...'
                Button:
                    text: 'Search'
                    size_hint_y: None
                    height: 40
                    on_release: root.search()
                Label:
                    id: problem_results
                    text: ''
                    size_hint_y: None
                    height: self.texture_size[1]
        Button:
            text: '← Back to menu'
            size_hint_y: None
            height: 40
            on_release: app.sm.current = 'menu'

<ScheduleLogScreen>:
    name: 'schedule_log'
    BoxLayout:
        orientation: 'vertical'
        Label:
            id: log_status
            text: root.status_text
            size_hint_y: None
            height: self.texture_size[1]
        RecycleView:
            id: log_list
            viewclass: 'Label'
            data: [{'text': e} for e in root.log_entries]
        BoxLayout:
            size_hint_y: None
            height: 40
            Button:
                text: 'Refresh'
                on_release: root.load_log()
            Button:
                text: 'Export'
                on_release: root.export_log()
            Button:
                text: 'Clear'
                on_release: root.clear_log()
            Button:
                text: '← Back to menu'
                on_release: app.sm.current = 'menu'
'''

class GardenPipApp(App):
    def build(self):
        self.sm = Builder.load_string(kv)
        return self.sm

if __name__ == '__main__':
    GardenPipApp().run()
