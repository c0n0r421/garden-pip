# Garden Pip

Garden Pip is a Kivy-based application providing tools for managing a small-scale hydroponic setup.  It currently includes a nutrient calculator and a basic problem search interface.  Additional features such as shelf layout planning and schedule logging will be added in the future.

## Running on Raspberry Pi

1. Ensure Python 3 and `pip` are installed:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip
   ```
2. Clone this repository on your Raspberry Pi:
   ```bash
   git clone <repository url>
   cd garden-pip
   ```
3. Install the required Python packages:
   ```bash
   pip3 install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python3 main.py
   ```

The application opens a simple GUI window where the tools are accessible.

## Features

- **Nutrient calculator** – Calculate nutrient amounts based on manufacturer, series, growth stage, plant category, units, volume, and Cal-Mag supplement.  Results appear in the interface.
- **Problem search** – A placeholder screen intended to search issues in hydroponic systems.  Data is stored in `hydroponicProblems.json` and will be searchable in upcoming versions.
- **Shelf layout** – *(Planned)* a tool for configuring the physical arrangement of plants on shelving units.
- **Schedule log** – *(Planned)* a log of tasks such as feeding or cleaning events to help track plant care.

## Data files

- `nutrients.json` – Defines nutrient concentrations for various manufacturers, series and growth stages.
- `hydroponicProblems.json` – Contains example problems, symptoms and solutions for diagnosing issues in a hydroponic setup.

