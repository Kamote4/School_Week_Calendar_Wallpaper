"""
Headless script to update the wallpaper from the saved config.
Intended to be run by Windows Task Scheduler via run_wallpaper.bat.
"""

import json
import os
from datetime import datetime
from wallpaper_generator import WallpaperGenerator

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")


def main():
    if not os.path.exists(CONFIG_PATH):
        print("config.json not found. Run the GUI first.")
        return

    with open(CONFIG_PATH, "r") as f:
        cfg = json.load(f)

    title = cfg.get("title", "")
    if not title:
        print("Invalid config: missing title.")
        return

    left_pane_mode   = cfg.get("left_pane_mode", "per_week")
    left_col_content = cfg.get("left_col_content", "")
    right_pane_mode  = cfg.get("right_pane_mode", "calendar")
    right_col_content = cfg.get("right_col_content", "")

    # migrate old format
    bottom_mode    = cfg.get("bottom_mode", cfg.get("right_col_mode", "none"))
    bottom_content = cfg.get("bottom_content", "")
    if not bottom_content and "right_col_content" in cfg and "bottom_content" not in cfg:
        bottom_content = cfg.get("right_col_content", "")

    weeks_data = []
    if left_pane_mode == "per_week":
        for line in cfg.get("weeks", "").strip().split("\n"):
            if line:
                parts = line.split(",", 1)
                if len(parts) == 2:
                    try:
                        label = parts[0].strip()
                        date  = datetime.strptime(parts[1].strip(), "%Y-%m-%d")
                        weeks_data.append((label, date))
                    except ValueError:
                        print(f"Skipping bad week line: {line}")

    gen = WallpaperGenerator()
    gen.generate_schedule_wallpaper(
        title            = title,
        weeks_data       = weeks_data,
        left_pane_mode   = left_pane_mode,
        left_col_content = left_col_content,
        right_pane_mode  = right_pane_mode,
        right_col_content = right_col_content,
        bottom_mode      = bottom_mode,
        bottom_content   = bottom_content,
    )
    print("Wallpaper updated successfully.")


if __name__ == "__main__":
    main()
