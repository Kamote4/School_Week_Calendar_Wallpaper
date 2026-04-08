# School Week Calendar Wallpaper — Agent Instructions

## Project Overview

A Python desktop application that generates dynamic desktop wallpapers displaying school/term schedules with a weekly calendar view and customizable right-column content. Supports both interactive GUI mode and automated scheduled updates via Windows Task Scheduler.

**Key Capabilities**:
- Schedule wallpaper: displays week labels, date ranges, and a calendar grid for the current week
- Custom text wallpaper: render arbitrary text with alignment and font size controls
- Live preview in GUI before setting wallpaper
- Automated scheduled updates via Windows Task Scheduler
- Persistent configuration (JSON-based)

---

## Architecture & Key Files

| File | Purpose | Key Responsibility |
|------|---------|-------------------|
| **gui.py** | Interactive Tkinter GUI | Mode switching, input forms, live preview, config save/load |
| **wallpaper_generator.py** | Core rendering engine | Resolution detection, font loading, image generation, Windows wallpaper API integration |
| **update_wallpaper.py** | Headless scheduler script | Reads config.json, generates wallpaper (no GUI, designed for Task Scheduler) |
| **config.json** | Configuration storage | Title, week data (label + Monday dates), right column mode, custom content |
| **run_wallpaper.bat** | Windows batch launcher | Sets working directory, calls Python 3.13 to run update_wallpaper.py |

**Architecture Pattern**: Separation of concerns
- GUI layer (user input) → WallpaperGenerator (rendering) → Windows API (system integration)
- Configuration layer enables both interactive and headless workflows

---

## Technology Stack

- **Language**: Python 3.13+
- **GUI**: Tkinter (tkinter, tkinter.ttk)
- **Image Generation**: Pillow (PIL) — drawing, font rendering, image manipulation
- **System Integration**: ctypes (Windows API calls for DPI detection, wallpaper setting)
- **Configuration**: JSON serialization
- **Fonts**: Arial, Arial Bold, Segoe UI Emoji (Windows system fonts)
- **Dependencies**: No external packages required (stdlib + Pillow)

---

## Important Conventions

### Date & Week Format
- **Date Format**: `YYYY-MM-DD` in config.json; GUI accepts "Label, YYYY-MM-DD" pairs
- **Week Definition**: Monday = week start; the date field stores the Monday of that week
- **Calendar Display**: Always shows 7 days (Monday through Sunday)

### Visual Design
- **Colors**: Black background (0, 0, 0), light gray text (180, 180, 180), white highlights
- **Font Sizing**: Scales proportionally: base = `WIDTH / 1920.0` (1920×1080 is the baseline resolution)
- **Layout**: Responsive to multi-monitor setups (detects, applies 1.5× scaling + 400px extra height)
- **Right Column Modes**: 
  - `"checklist"` — indented wrapping text on a transparent background
  - `"custom_text"` — arbitrary user-provided text

### Common Patterns
- **Responsive Design**: All measurements scale relative to screen width and height
- **Font Fallback**: If TrueType font unavailable, falls back to default system font
- **Configuration Persistence**: Always save config.json after user changes via GUI
- **Error Handling**: Invalid date lines skipped silently; errors logged to error.log during GUI crashes

---

## How to Run

### Interactive Mode (GUI)
```bash
python gui.py
```
- Opens Tkinter window with mode selector (Schedule / Custom Text)
- Load existing config.json or start with defaults
- Preview live rendering before saving
- Save configuration or generate + set wallpaper immediately

### Automated Mode (Scheduled)
```bash
python update_wallpaper.py
```
or via batch wrapper:
```bash
run_wallpaper.bat
```
- Reads config.json
- Generates wallpaper without GUI
- Sets wallpaper via Windows API
- **Designed for Windows Task Scheduler integration**

### Windows Task Scheduler Integration
- Schedule `run_wallpaper.bat` to run at intervals (e.g., weekly at Monday 8:00 AM)
- Batch file ensures correct working directory and Python 3.13 executable path
- Returns silently on success; check system logs for errors

---

## Development Guidance

### When Modifying GUI (gui.py)
- Use `tkinter.ttk` for consistent cross-platform L&F
- Always call `config_manager.save_to_json()` after user changes
- Call `wallpaper_generator.generate_*()` methods for preview or final output
- Propagate validation errors to user via message dialogs

### When Modifying Rendering (wallpaper_generator.py)
- All coordinate calculations must be resolution-aware (multiply by scale factors)
- Test on multiple monitor configurations if possible (scaling is 1.5× for high-DPI)
- Font paths are Windows-specific (`arial.ttf`, `arialbd.ttf`, `seguiemj.ttf`)
- Wallpaper dimensions always match detected monitor resolution

### When Adding New Features
- **New config fields**: Update config.json schema and add GUI controls + validation
- **New wallpaper mode**: Add `generate_*_wallpaper()` method; ensure resolution-aware
- **New fonts**: Update font loading logic in `WallpaperGenerator.__init__()` for fallback
- **Breaking changes**: Test both GUI and scheduled workflows

---

## Common Development Tasks

### Add a New Configuration Option
1. Identify field name and storage in config.json
2. Add input control in gui.py (tkinter widget)
3. Hook control to `config_manager`
4. Pass value to `wallpaper_generator.generate_*()` methods
5. Test with both GUI and `update_wallpaper.py`

### Fix a Rendering Bug
1. Reproduce via `python gui.py` preview
2. Identify scaling or color issue in `wallpaper_generator.py`
3. Adjust coordinate calculations or color tuples
4. Test on different screen resolutions if possible

### Add Wallpaper Mode
1. Create new `generate_*_wallpaper()` method in `WallpaperGenerator`
2. Add mode selection to GUI in gui.py
3. Connect GUI input controls to method parameters
4. Update config.json schema if needed
5. Ensure headless execution via `update_wallpaper.py`

---

## Key Entry Point Functions

| Function | Module | Purpose |
|----------|--------|---------|
| `WallpaperApp()` | gui.py | Main GUI application entry point |
| `WallpaperGenerator.generate_schedule_wallpaper()` | wallpaper_generator.py | Renders schedule with current week highlighting |
| `WallpaperGenerator.generate_custom_wallpaper()` | wallpaper_generator.py | Renders centered/aligned custom text |
| `WallpaperGenerator.save_and_set_wallpaper()` | wallpaper_generator.py | Saves PNG and applies via Windows API |
| `update_wallpaper.py` (main) | update_wallpaper.py | Automated scheduled entry point |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Wallpaper not applying via Task Scheduler | Verify Python 3.13 path in run_wallpaper.bat; check Task Scheduler logs |
| Fonts appear distorted or unavailable | Ensure Windows system fonts (arial.ttf, etc.) are present; check font fallback logic |
| Preview looks different than final wallpaper | Check DPI scaling and multi-monitor setup; compare scale factors in preview vs. generation |
| Config.json reset to defaults | Check file permissions; verify JSON is valid (no syntax errors) |

---

## Tips for AI Agents

- **Always preserve config.json schema** when adding new features
- **Test both workflows**: GUI mode (`python gui.py`) and automated mode (`python update_wallpaper.py`)
- **Coordinate calculations are critical**: All measurements scale with `WIDTH / 1920.0`
- **Windows API calls are brittle**: System parameters IDs (e.g., `20` for wallpaper) are fixed; verify before changes
- **Date validation is lenient**: Invalid weeks are skipped; consider adding stricter validation if needed
