# Deployment Guide

## Pre-Deployment Checklist

- [ ] Python 3.10+ installed
- [ ] Pillow installed: `pip install -r requirements.txt`
- [ ] `config.json` created by running the GUI at least once
- [ ] Task Scheduler task created (if using automated updates)

## Steps

### 1. Install Python & Pillow

Download Python from [python.org](https://www.python.org/downloads/) and install it with **"Add to PATH"** checked.

Then install Pillow system-wide (no virtual environment needed):

```bash
pip install -r requirements.txt
```

### 2. Verify

```bash
python gui.py          # GUI should open
python update_wallpaper.py  # should apply the wallpaper (requires config.json)
```

### 3. Configure

Run the GUI, set up your schedule, then click **Save & Apply**. This creates `config.json`.

### 4. Task Scheduler (automated daily updates)

1. `Win+R` → `taskschd.msc`
2. Create Basic Task:
   - Trigger: Daily at your preferred time (e.g. 7:00 AM) or At logon
   - Action: Start a program → select `run_wallpaper.bat`
   - Start in: full path to the project folder
3. Test it: right-click the task → Run

### 5. Desktop shortcut for the GUI

Right-click `run_gui.bat` → Send to → Desktop (create shortcut).

---

## Batch file paths

The `.bat` files use `py` (Windows Python Launcher). If `py` is not recognised on your machine, open the file and replace:

```batch
py "gui.py"
```

with:

```batch
"C:\path\to\your\python.exe" "gui.py"
```

Find your Python path with:
```bash
python -c "import sys; print(sys.executable)"
```

---

## Troubleshooting

### Task Scheduler exits with error

1. Open Task Scheduler → History tab → find the failed run → read the error
2. Make sure **Start in** is set to the project folder (not the .bat file's folder)
3. Try running `run_wallpaper.bat` manually first to confirm it works

### Wallpaper not changing

Run `python update_wallpaper.py` in a terminal to see any printed errors.  
Common causes: missing `config.json`, bad date format in weeks, or Windows font files missing.

### Python version issues

Check your version:
```bash
python --version
```

If you have multiple Pythons, target a specific one:
```bash
py -3.13 -m pip install -r requirements.txt
```

---

## Uninstall

1. Delete the Task Scheduler task
2. Remove desktop shortcuts
3. Delete the project folder
