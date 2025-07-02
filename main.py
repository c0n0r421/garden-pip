# gardenpip_app.py

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
import json

# Set retro Pip-Boy like colors
Window.clearcolor = (0.07, 0.15, 0.07, 1)  # dark green background


class SplashScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        layout.add_widget(Label(text='[b]Garden Pip Tools[/b]', markup=True, font_size=32, color=(0.4, 1, 0.4, 1)))

        nutrient_btn = Button(text='🌿 Nutrient Calculator', size_hint=(1, 0.2), background_color=(0, 0.6, 0, 1))
        nutrient_btn.bind(on_press=lambda x: self.manager.current = 'nutrients')
        layout.add_widget(nutrient_btn)

        self.add_widget(layout)


class NutrientCalculatorScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.data = self.load_nutrient_data()

        self.manufacturer_spinner = Spinner(text='Select Manufacturer', values=list(self.data.keys()))
        self.manufacturer_spinner.bind(text=self.update_series_spinner)

        self.series_spinner = Spinner(text='Select Series')
        self.stage_spinner = Spinner(text='Select Stage')
        self.unit_spinner = Spinner(text='Select Unit', values=['metric', 'imperial'])
        self.volume_input = TextInput(hint_text='Enter volume', multiline=False, input_filter='float')

        self.result_label = Label(text='Results will appear here.', halign='left', valign='top')
        self.result_label.bind(size=self.result_label.setter('text_size'))

        calc_btn = Button(text='Calculate', background_color=(0, 0.5, 0, 1))
        calc_btn.bind(on_press=self.calculate)

        self.layout.add_widget(self.manufacturer_spinner)
        self.layout.add_widget(self.series_spinner)
        self.layout.add_widget(self.stage_spinner)
        self.layout.add_widget(self.unit_spinner)
        self.layout.add_widget(self.volume_input)
        self.layout.add_widget(calc_btn)
        self.layout.add_widget(self.result_label)

        self.add_widget(self.layout)

    def load_nutrient_data(self):
        with open('nutrients.json') as f:
            raw = json.load(f)
        data = {}
        for n in raw['nutrients']:
            data.setdefault(n['manufacturer'], {})[n['series']] = n
        return data

    def update_series_spinner(self, spinner, text):
        series_list = list(self.data[text].keys())
        self.series_spinner.values = series_list
        self.series_spinner.text = series_list[0]
        self.update_stage_spinner()

    def update_stage_spinner(self):
        manufacturer = self.manufacturer_spinner.text
        series = self.series_spinner.text
        if manufacturer in self.data and series in self.data[manufacturer]:
            stages = list(self.data[manufacturer][series]['stages'].keys())
            self.stage_spinner.values = stages
            self.stage_spinner.text = stages[0]

    def calculate(self, instance):
        try:
            manufacturer = self.manufacturer_spinner.text
            series = self.series_spinner.text
            stage = self.stage_spinner.text
            unit = self.unit_spinner.text
            volume = float(self.volume_input.text)

            base_data = self.data[manufacturer][series]
            stage_data = base_data['stages'][stage]
            base_volume = base_data['base_unit'][unit]['volume']

            result_text = f'[b]Results for {manufacturer} - {series} ({stage})[/b]\n\n'
            for nutrient in stage_data:
                name = nutrient['name']
                amount = nutrient['concentration'][unit] * volume / base_volume
                unit_label = nutrient['unit'][unit]
                result_text += f'{name}: {amount:.2f} {unit_label}\n'

            self.result_label.text = result_text
        except Exception as e:
            self.result_label.text = f'Error: {str(e)}'


class GardenPipApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(SplashScreen(name='splash'))
        sm.add_widget(NutrientCalculatorScreen(name='nutrients'))
        return sm


if __name__ == '__main__':
    GardenPipApp().run()
