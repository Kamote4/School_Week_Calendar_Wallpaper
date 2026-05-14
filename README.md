# School Week Calendar Wallpaper

A Windows desktop app that generates a dynamic wallpaper showing your school/term week schedule alongside a live monthly calendar. Designed to run automatically every day via Windows Task Scheduler — no manual effort after setup.

## Features

- **Per Week schedule** — list your weeks with labels and Monday start dates; the current week is highlighted automatically
- **Left/Right pane modes** — left pane supports Per Week, Checklist, or Custom text; right pane supports Calendar or Custom text
- **Bottom content** — optional Checklist or Custom text below the calendar
- **Monday-only date picker** — popup calendar that only lets you pick Mondays, auto-increments when adding weeks
- **Inline table editing** — double-click any row in the week list to edit label or date
- **Inline preview** — preview the wallpaper inside the GUI without setting it
- **Task Scheduler ready** — headless `update_wallpaper.py` + `run_wallpaper.bat` for automated daily updates
- **No virtual environment needed** — install Pillow system-wide once and you're done

## Requirements

- Windows 10/11
- Python 3.10+ (3.13 recommended) — [python.org](https://www.python.org/downloads/)
- Pillow (`pip install pillow`)

## Installation

```bash
git clone https://github.com/yourusername/School_Week_Calendar_Wallpaper.git
cd School_Week_Calendar_Wallpaper
pip install -r requirements.txt
```

## Usage

### GUI (configure & preview)

```bash
python gui.py
```

Or double-click `run_gui.bat`.

**Workflow:**
1. Enter a wallpaper title
2. Choose **Left Pane** mode — *Per Week*, *Checklist*, or *Custom*
3. In Per Week mode: use **+ Add** to auto-add weeks, **Pick Start…** to set the starting Monday, double-click any row to edit
4. Choose **Right Pane** mode — *Calendar* (auto-generated) or *Custom* text
5. Optionally add **Bottom Content** (below the calendar)
6. Click **Preview Wallpaper** to see it rendered on the right panel
7. Click **Save & Apply** to write `config.json` and set the wallpaper immediately

### Automated (Task Scheduler)

```bash
python update_wallpaper.py
```

Or point Task Scheduler at `run_wallpaper.bat` — reads `config.json` and applies the wallpaper silently.

## Configuration file (`config.json`)

Created and updated by the GUI. Format:

```json
{
    "title": "1st Term 2026",
    "left_pane_mode": "per_week",
    "weeks": "Week 1,2026-05-11\nWeek 2,2026-05-18\nWeek 3,2026-05-25",
    "left_col_content": "",
    "right_pane_mode": "calendar",
    "right_col_content": "",
    "bottom_mode": "none",
    "bottom_content": ""
}
```

`config.json` is gitignored — each machine keeps its own.

## Task Scheduler setup

1. Open Task Scheduler (`Win+R` → `taskschd.msc`)
2. **Create Basic Task**
   - Trigger: Daily, at login, or on a schedule (e.g. 7:00 AM)
   - Action: Start a program → browse to `run_wallpaper.bat`
   - Start in: your project folder path
3. Done — the wallpaper updates silently each trigger

> **Note:** If `py` is not recognised on your machine, open `run_wallpaper.bat` and `run_gui.bat` and replace `py` with the full path to your `python.exe`. Find it with: `python -c "import sys; print(sys.executable)"`

## Project structure

```
School_Week_Calendar_Wallpaper/
├── gui.py                  # Tkinter GUI
├── wallpaper_generator.py  # Rendering engine (Pillow + Windows API)
├── update_wallpaper.py     # Headless script for Task Scheduler
├── run_gui.bat             # Launch GUI
├── run_wallpaper.bat       # Launch headless updater
├── requirements.txt        # Pillow
└── README.md
```

## Troubleshooting

| Issue | Fix |
|---|---|
| `py` not recognised in .bat | Replace `py` with your full `python.exe` path |
| Wallpaper not applying | Run `python update_wallpaper.py` in a terminal and read the output |
| Fonts look wrong / fallback | Ensure `arial.ttf`, `arialbd.ttf`, `seguiemj.ttf` exist in `C:\Windows\Fonts\` |
| Task Scheduler fails | Set "Start in" to the project folder; check History tab for error code |
| Preview looks off | Click Save & Apply — preview scales down, actual wallpaper renders at full resolution |

## License

[Add your license here]
