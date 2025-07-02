# Garden Pip

Garden Pip now offers a text based interface styled like a Fallout Pip-Boy.  The core tools provide a nutrient calculator and a problem search.  Additional features such as shelf layout planning and schedule logging will be added in the future.

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
   pip3 install -r requirements.txt  # installs the Textual framework
   ```
4. Run the application:
   ```bash
   python3 pipboy.py
   ```

The application opens a keyboard navigable interface styled like a Pip-Boy. Use
the arrow keys to move between options and **Enter** to select. Settings for the
nutrient calculator can be saved and loaded from the **Manage Settings** menu.


## Features

- **Nutrient calculator** – Calculate nutrient amounts based on manufacturer, series, growth stage, plant category, units, volume, and Cal-Mag supplement.  Results appear in the interface.
- **Problem search** – *Experimental* placeholder screen for diagnosing issues.  Data is stored in `hydroponicProblems.json` but searching is incomplete.
- **Shelf layout** – *(Planned)* a tool for configuring the physical arrangement of plants on shelving units.
- **Schedule log** – *Experimental* feature that records nutrient calculations; the log viewer is still under development.

## Data files

- `nutrients.json` – Defines nutrient concentrations for various manufacturers, series and growth stages.
- `hydroponicProblems.json` – Contains example problems, symptoms and solutions for diagnosing issues in a hydroponic setup.

## Using the nutrient calculator

1. From the menu choose **Nutrient Calculator**.
2. Select the nutrient manufacturer, series and growth stage.
3. Pick a plant category and unit system, then enter the desired solution volume.
4. Optionally choose a Cal-Mag supplement and press **Calculate**.
5. Use **Save Setting** to store the current selections or **Load Setting** to recall a saved one.
6. The calculated amounts appear below the button and the entry is added to the schedule log.
7. Press **Esc** to return to the main menu at any time.


## Log files

Schedule entries are written to `schedule_log.json` inside Kivy's user data directory (typically `~/.local/share/gardenpip/` on Linux).  The schedule log screen lets you view, export or clear this file.  Logging is experimental and may change in future versions.

