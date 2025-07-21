# main.py
#!/usr/bin/env python3

import json
import os
import datetime as dt
from datetime import date

from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from gardenpip.schedule_log import log_schedule
from gardenpip.shelf_logic import get_system_layout, save_system_layout
from gardenpip.config_logic import load_configs, save_configs, get_screensaver_timeout

from gardenpip.db import (
    ShelfSystem,
    Shelf,
    Tray,
    add_nutrient_log,
    delete_nutrient_log,
    get_session,
    search_nutrient_logs,
    update_nutrient_log,
)

class MenuScreen(Screen):
    pass


class ScreensaverOverlay(Widget):
    """Simple black widget used as a screensaver overlay."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(0, 0, 0, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, *args) -> None:
        self.rect.pos = self.pos
        self.rect.size = self.size

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


class NutrientLogScreen(Screen):
    def on_kv_post(self, base_widget):
        here = os.path.dirname(__file__)
        db_path = os.path.join(here, "gardenpip.db")
        self.session = get_session(db_path)
        self.refresh_logs()

    def refresh_logs(self, query: str | None = None) -> None:
        logs = search_nutrient_logs(self.session, query)
        self.ids.log_list.data = [
            {
                "text": f"{log.date.date()} | Tray {log.tray_id} pH {log.ph} ppm {log.ppm} - {log.notes}",
                "on_press": lambda log_id=log.id: self.edit_log(log_id),
            }
            for log in logs
        ]

    def on_search(self, text: str) -> None:
        self.refresh_logs(text)

    def add_log(self) -> None:
        tray = self.session.query(Tray).first()
        if not tray:
            system = ShelfSystem(name="Default")
            shelf = Shelf(label="S1", system=system)
            tray = Tray(label="T1", shelf=shelf)
            self.session.add(system)
            self.session.commit()
        add_nutrient_log(self.session, tray.id, ph=6.0, ppm=1000, notes="New entry")
        self.refresh_logs()

    def edit_log(self, log_id: int) -> None:
        update_nutrient_log(self.session, log_id, notes="edited")
        self.refresh_logs()

    def delete_log(self, log_id: int) -> None:
        delete_nutrient_log(self.session, log_id)
        self.refresh_logs()


class GardenPipApp(App):
    def build(self):
        Window.clearcolor = (0.07, 0.15, 0.07, 1)  # Pip-Boy dark green

        # load configuration
        here = os.path.dirname(__file__)
        self.config_path = os.path.join(here, "config.json")
        self.config = load_configs(self.config_path)
        self.screensaver_timeout = get_screensaver_timeout(self.config)
        if "screensaver_timeout" not in self.config:
            save_configs(self.config_path, self.config)

        # idle timer and overlay
        self.last_interaction = dt.datetime.now()
        Window.bind(on_touch_down=self._on_activity, on_key_down=self._on_activity)
        Clock.schedule_interval(self._check_idle, 1)

        self.selected_manufacturer = ''
        self.selected_series = ''
        self.selected_calmag = ''

        root = FloatLayout()
        sm = ScreenManager()
        self.screen_manager = sm
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(NutrientSelectScreen(name='nutrient_select'))
        sm.add_widget(NutrientStageScreen(name='nutrient_stage'))
        sm.add_widget(NutrientLogScreen(name='nutrient_log'))
        sm.add_widget(ShelfLayoutScreen(name='shelf_layout'))

        root.add_widget(sm)
        self.screensaver = ScreensaverOverlay(size_hint=(1, 1), opacity=0)
        root.add_widget(self.screensaver)
        return root

    # ── idle timer helpers ────────────────────────────────────────────

    def _on_activity(self, *args):
        """Reset idle timer on any user input."""
        self.last_interaction = dt.datetime.now()
        if self.screensaver.opacity > 0:
            self.screensaver.opacity = 0
        return False

    def _check_idle(self, *_dt):
        if self.screensaver_timeout <= 0:
            return
        if (
            self.screensaver.opacity == 0
            and (dt.datetime.now() - self.last_interaction).total_seconds()
            >= self.screensaver_timeout
        ):
            self.screensaver.opacity = 1

if __name__ == '__main__':
    GardenPipApp().run()

