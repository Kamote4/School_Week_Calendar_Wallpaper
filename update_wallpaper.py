"""
Headless script to update the wallpaper based on the saved schedule config.
This script is intended to be run by a scheduled task.
"""

import json
import os
from datetime import datetime
from wallpaper_generator import WallpaperGenerator


def main():
    config_path = "config.json"
    if not os.path.exists(config_path):
        print("Configuration file not found. Please run the GUI to create one.")
        return

    with open(config_path, "r") as f:
        config = json.load(f)

    title = config.get("title")
    weeks_data_str = config.get("weeks")
    right_col_mode = config.get("right_col_mode", "checklist")
    right_col_content = config.get("right_col_content", "")

    if not title or not weeks_data_str:
        print("Invalid configuration data.")
        return

    weeks_data = []
    for line in weeks_data_str.strip().split("\n"):
        if line:
            try:
                label, date_str = line.split(",")
                date = datetime.strptime(date_str.strip(), "%Y-%m-%d")
                weeks_data.append((label.strip(), date))
            except ValueError:
                print(f"Skipping invalid line in config: {line}")

    if weeks_data:
        generator = WallpaperGenerator()
        generator.generate_schedule_wallpaper(
            title, weeks_data, right_col_mode, right_col_content
        )
        print("Wallpaper updated successfully.")
    else:
        print("No valid week data found in config.")


if __name__ == "__main__":
    main()
