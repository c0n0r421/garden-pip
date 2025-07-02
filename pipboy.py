from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import (
    Header,
    Footer,
    Button,
    Static,
    Select,
    Input,
    OptionList,
)
from textual.widgets.option_list import Option

from textual.screen import Screen
import os
from gardenpip.nutrient_logic import load_nutrient_data, calculate_nutrients
from gardenpip.problem_logic import load_problem_data, search_problems
from gardenpip.config_logic import load_configs, save_configs

DATA_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(DATA_DIR, 'pipboy_config.json')


class MenuScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static("Garden PipBoy", id="title")
        yield OptionList(
            Option("Nutrient Calculator", id="calc"),
            Option("Problem Search", id="search"),
            Option("Manage Settings", id="config"),

            Option("Exit", id="exit"),
            id="menu_options",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(OptionList).focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id == "calc":
            self.app.push_screen(NutrientCalculatorScreen())
        elif event.option.id == "search":
            self.app.push_screen(ProblemSearchScreen())
        elif event.option.id == "config":
            self.app.push_screen(ConfigListScreen())
        elif event.option.id == "exit":
            self.app.exit()

class ConfigListScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def __init__(self, callback=None, **kwargs):
        self.callback = callback
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        data = load_configs(CONFIG_PATH)
        opts = [Option(name, id=name) for name in data.keys()] or [Option("<none>", id="none")]
        yield Header(show_clock=False)
        yield Static("Saved Settings", id="title")
        yield OptionList(*opts, id="cfg_list")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(OptionList).focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id != "none" and self.callback:
            self.callback(event.option.id)
        self.app.pop_screen()

class NutrientCalculatorScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        path = os.path.join(DATA_DIR, 'nutrients.json')
        self.data = load_nutrient_data(path)
        self.nutrients = self.data['nutrients']
        self.calmag = self.data['cal_mag_supplements']
        self.plant_cats = list(self.data.get('plant_categories', {}).keys())
        yield Header(show_clock=False)
        yield Static("Nutrient Calculator", id="title")
        yield Vertical(
            Select(options=[(n['manufacturer'], n['manufacturer']) for n in self.nutrients], id="manu", prompt="Manufacturer"),
            Select(options=[], id="series", prompt="Series"),
            Select(options=[], id="stage", prompt="Stage"),
            Select(options=[(c, c) for c in self.plant_cats], id="plant", prompt="Plant"),
            Select(options=[('metric','metric'),('imperial','imperial')], value="metric", id="unit", prompt="Units"),
            Input(placeholder="Volume", id="volume", restrict=r'[0-9.]'),
            Select(options=[(c['product'], c['product']) for c in self.calmag], allow_blank=True, id="calmag", prompt="Cal-Mag"),
            Input(placeholder="Setting name", id="cfgname"),
            Button("Save Setting", id="save_cfg"),
            Button("Load Setting", id="load_cfg"),

            Button("Calculate", id="do_calc"),
            Static(id="results"),
            id="calc_form"
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one('#manu', Select).focus()


    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "manu":
            item = next((d for d in self.nutrients if d['manufacturer'] == event.value), None)
            series = [(item['series'], item['series'])] if item else []
            stages = [(s, s) for s in item['stages'].keys()] if item else []
            self.query_one('#series', Select).options = series
            self.query_one('#stage', Select).options = stages

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "do_calc":
            manu = self.query_one('#manu', Select).value
            series = self.query_one('#series', Select).value
            stage = self.query_one('#stage', Select).value
            plant = self.query_one('#plant', Select).value
            unit = self.query_one('#unit', Select).value
            volume = self.query_one('#volume', Input).value
            calmag = self.query_one('#calmag', Select).value
            try:
                vol = float(volume)
            except ValueError:
                self.query_one('#results', Static).update("Enter valid volume")
                return
            lines = calculate_nutrients(
                {
                    'nutrients': self.nutrients,
                    'cal_mag_supplements': self.calmag,
                    'plant_categories': self.data.get('plant_categories', {})
                },
                manu, series, stage, plant, unit, vol, calmag
            )
            self.query_one('#results', Static).update('\n'.join(lines))
        elif event.button.id == "save_cfg":
            name = self.query_one('#cfgname', Input).value.strip()
            if not name:
                self.query_one('#results', Static).update('Enter a setting name')
                return
            cfg = {
                'manufacturer': self.query_one('#manu', Select).value,
                'series': self.query_one('#series', Select).value,
                'stage': self.query_one('#stage', Select).value,
                'plant': self.query_one('#plant', Select).value,
                'unit': self.query_one('#unit', Select).value,
                'volume': self.query_one('#volume', Input).value,
                'calmag': self.query_one('#calmag', Select).value,
            }
            data = load_configs(CONFIG_PATH)
            data[name] = cfg
            save_configs(CONFIG_PATH, data)
            self.query_one('#results', Static).update(f'Saved setting {name}')
        elif event.button.id == "load_cfg":
            self.app.push_screen(ConfigListScreen(callback=self.apply_config))

    def apply_config(self, cfg_name: str) -> None:
        data = load_configs(CONFIG_PATH)
        cfg = data.get(cfg_name)
        if not cfg:
            return
        manu_select = self.query_one('#manu', Select)
        manu_select.value = cfg.get('manufacturer')
        item = next((d for d in self.nutrients if d['manufacturer'] == manu_select.value), None)
        series_select = self.query_one('#series', Select)
        stage_select = self.query_one('#stage', Select)
        if item:
            series_select.options = [(item['series'], item['series'])]
            stage_select.options = [(s, s) for s in item['stages'].keys()]
        series_select.value = cfg.get('series')
        stage_select.value = cfg.get('stage')
        self.query_one('#plant', Select).value = cfg.get('plant')
        self.query_one('#unit', Select).value = cfg.get('unit')
        self.query_one('#volume', Input).value = str(cfg.get('volume', ''))
        self.query_one('#calmag', Select).value = cfg.get('calmag')
        self.query_one('#cfgname', Input).value = cfg_name
        self.query_one('#results', Static).update(f'Loaded setting {cfg_name}')

class ProblemSearchScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]


    def compose(self) -> ComposeResult:
        path = os.path.join(DATA_DIR, 'hydroponicProblems.json')
        self.problems = load_problem_data(path)
        plants = set(); stages = set(); media = set(); systems = set()
        for prob in self.problems:
            plants.update(prob.get('applicablePlants', []))
            stages.update(prob.get('growthStages', []))
            media.update(prob.get('growMedia', []))
            systems.update(prob.get('hydroponicSystems', []))
        yield Header(show_clock=False)
        yield Static("Problem Search", id="title")
        yield Vertical(
            Select(options=[(p,p) for p in sorted(plants)], allow_blank=True, id="plant", prompt="Plant"),
            Select(options=[(s,s) for s in sorted(stages)], allow_blank=True, id="stage", prompt="Stage"),
            Select(options=[(m,m) for m in sorted(media)], allow_blank=True, id="medium", prompt="Medium"),
            Select(options=[(s,s) for s in sorted(systems)], allow_blank=True, id="system", prompt="System"),
            Button("Search", id="do_search"),
            Static(id="results"),
            id="search_form"
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one('#plant', Select).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "do_search":
            plant = self.query_one('#plant', Select).value or ''
            stage = self.query_one('#stage', Select).value or ''
            medium = self.query_one('#medium', Select).value or ''
            system = self.query_one('#system', Select).value or ''
            matches = search_problems(self.problems, plant=plant, stage=stage, medium=medium, system=system)
            if not matches:
                self.query_one('#results', Static).update('No matches found.')
            else:
                lines = [f"{m['title']}: {m.get('description','')}" for m in matches]
                self.query_one('#results', Static).update('\n\n'.join(lines))

class GardenPipBoyApp(App):
    CSS_PATH = 'pipboy.css'
    TITLE = 'Garden PipBoy'

    def on_mount(self) -> None:
        self.push_screen(MenuScreen())

if __name__ == '__main__':
    GardenPipBoyApp().run()
