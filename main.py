import json
import os
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ListProperty, StringProperty

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

class ProblemSearchScreen(Screen):
    def search(self):
        # TODO: load and filter your hydroponic problems data here
        self.ids.problem_results.text = 'Search functionality coming soon.'

# Kivy UI definition
kv = '''
ScreenManager:
    MenuScreen:
    NutrientCalculatorScreen:
    ProblemSearchScreen:

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

<NutrientCalculatorScreen>:
    name: 'nutrient_calc'
    manufacturer: manufacturer
    series: series
    stage: stage
    plant_category: plant_category
    unit: unit
    volume: volume
    calmag: calmag
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
'''

class GardenPipApp(App):
    def build(self):
        self.sm = Builder.load_string(kv)
        return self.sm

if __name__ == '__main__':
    GardenPipApp().run()
