# main.py
#!/usr/bin/env python3
import json, os
from datetime import date
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from gardenpip.schedule_log import log_schedule
from gardenpip.shelf_logic import get_system_layout, save_system_layout

class MenuScreen(Screen):
    pass

class NutrientSelectScreen(Screen):
    def on_kv_post(self, base_widget):
        here = os.path.dirname(__file__)
        with open(os.path.join(here, 'nutrients.json')) as f:
            self.data = json.load(f)
        # Populate main nutrients
        self.ids.manufacturer.values = [m['manufacturer'] for m in self.data['nutrients']]
        self.ids.series.values       = []
        # Populate Cal-Mag supplements (add a “None” option)
        self.ids.calmag.values = ['None'] + [s['product'] for s in self.data['cal_mag_supplements']]
        self.ids.calmag.text   = 'None'

    def on_manufacturer(self, text):
        entry = next((m for m in self.data['nutrients'] if m['manufacturer']==text), None)
        if entry:
            self.ids.series.values = [entry['series']]
            self.ids.series.text   = entry['series']

    def do_next(self):
        app = App.get_running_app()
        app.selected_manufacturer = self.ids.manufacturer.text
        app.selected_series       = self.ids.series.text
        app.selected_calmag       = self.ids.calmag.text
        self.manager.current      = 'nutrient_stage'


class NutrientStageScreen(Screen):
    def on_pre_enter(self):
        app = App.get_running_app()
        here = os.path.dirname(__file__)
        with open(os.path.join(here, 'nutrients.json')) as f:
            data = json.load(f)
        entry = next((m for m in data['nutrients']
                      if m['manufacturer']==app.selected_manufacturer
                      and m['series']==app.selected_series), None)
        if entry:
            stages = list(entry['stages'].keys())
            self.ids.stage.values = stages
            self.ids.stage.text   = stages[0]
        # set up unit spinner & volume default
        self.ids.unit.values   = ['metric', 'imperial']
        self.ids.unit.text     = 'metric'
        self.on_unit(self.ids.unit.text)
        self.ids.result_lbl.text = ''

    def on_unit(self, unit):
        # default volume 1 L or 1 gal
        self.ids.volume.text     = '1'
        self.ids.volume.hint_text = 'Volume (L)' if unit=='metric' else 'Volume (gal)'

    def do_calc(self):
        app  = App.get_running_app()
        man  = app.selected_manufacturer
        ser  = app.selected_series
        stg  = self.ids.stage.text
        unit = self.ids.unit.text
        try:
            vol = float(self.ids.volume.text)
        except ValueError:
            vol = 1.0

        here = os.path.dirname(__file__)
        with open(os.path.join(here, 'nutrients.json')) as f:
            data = json.load(f)

        # main nutrients
        entry = next((m for m in data['nutrients']
                      if m['manufacturer']==man and m['series']==ser), None)
        lines = []
        if entry:
            base_vol = entry['base_unit'][unit]['volume']
            lines.append(f"[b]{man} – {ser} – {stg}[/b]\n")
            for comp in entry['stages'][stg]:
                amt = comp['concentration'][unit] * (vol / base_vol)
                lines.append(f"{comp['name']}: {amt:.1f} {comp['unit'][unit]}")
        # Cal-Mag
        supp = app.selected_calmag
        if supp and supp != 'None':
            supp_entry = next(s for s in data['cal_mag_supplements']
                              if s['product']==supp)
            base_vol_s = supp_entry['base_unit'][unit]['volume']
            conc_s     = supp_entry['concentration'][unit]
            amt_s      = conc_s * (vol / base_vol_s)
            lines.append("\n[b]Supplement[/b]\n")
            lines.append(f"{supp}: {amt_s:.1f} {supp_entry['unit']}")

        self.ids.result_lbl.text = '\n'.join(lines)

        # log the schedule with shelf/tray info
        log_entry = {
            'date': date.today().isoformat(),
            'manufacturer': man,
            'series': ser,
            'stage': stg,
            'plant_category': '',
            'unit': unit,
            'volume': vol,
            'cal_mag': supp if supp != 'None' else None,
            'lines': lines,
        }
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        log_schedule(log_entry, data_dir)


class ShelfLayoutScreen(Screen):
    def on_pre_enter(self):
        self.refresh()

    def refresh(self):
        layout = get_system_layout()
        box = self.ids.shelf_box
        box.clear_widgets()
        if not layout:
            self.add_shelf()
        else:
            for shelf in layout:
                name = shelf.get('name', '')
                label = shelf.get('trays', [{}])[0].get('label', '')
                self._add_row(name, label)

    def _add_row(self, shelf_name='', tray_label=''):
        row = BoxLayout(size_hint_y=None, height=40)
        name_input = TextInput(text=shelf_name)
        tray_input = TextInput(text=tray_label)
        btn = Button(text='Remove', size_hint_x=None, width=80)
        btn.bind(on_press=lambda *_: self.remove_shelf(row))
        row.add_widget(name_input)
        row.add_widget(tray_input)
        row.add_widget(btn)
        self.ids.shelf_box.add_widget(row)

    def add_shelf(self):
        self._add_row()

    def remove_shelf(self, row):
        self.ids.shelf_box.remove_widget(row)

    def save_layout(self):
        data = []
        for row in self.ids.shelf_box.children[::-1]:
            name_input = row.children[2]
            tray_input = row.children[1]
            data.append({'name': name_input.text, 'trays': [{'label': tray_input.text}]})
        save_system_layout('default', data)


class GardenPipApp(App):
    def build(self):
        Window.clearcolor = (0.07, 0.15, 0.07, 1)  # Pip-Boy dark green
        # init storage
        self.selected_manufacturer = ''
        self.selected_series       = ''
        self.selected_calmag       = ''
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(NutrientSelectScreen(name='nutrient_select'))
        sm.add_widget(NutrientStageScreen(name='nutrient_stage'))
        sm.add_widget(ShelfLayoutScreen(name='shelf_layout'))
        return sm

if __name__ == '__main__':
    GardenPipApp().run()

