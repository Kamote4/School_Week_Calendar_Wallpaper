import tkinter as tk
from tkinter import ttk, messagebox
from wallpaper_generator import WallpaperGenerator
from datetime import datetime
import json
import os
from PIL import Image, ImageTk
import traceback


from tkinter import font as tkfont


class WallpaperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dynamic Wallpaper Generator")
        self.root.geometry("1200x800")
        self.generator = WallpaperGenerator()
        self.config_path = "config.json"

        # Set a larger default font
        self.default_font = tkfont.nametofont("TkDefaultFont")
        self.default_font.configure(size=11)
        self.root.option_add("*Font", self.default_font)

        self.create_widgets()
        self.load_config()

    def create_widgets(self):
        # --- Main Layout ---
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_frame = ttk.LabelFrame(main_frame, text="Preview")
        right_frame.pack(side="right", fill="both", expand=True)

        # --- Left Frame Content ---
        # Mode selection
        mode_frame = ttk.LabelFrame(left_frame, text="Mode")
        mode_frame.pack(padx=10, pady=10, fill="x")

        self.mode = tk.StringVar(value="month")

        schedule_rb = ttk.Radiobutton(
            mode_frame,
            text="Schedule",
            variable=self.mode,
            value="schedule",
            command=self.switch_mode,
        )
        schedule_rb.pack(anchor="w", padx=10, pady=5)

        custom_rb = ttk.Radiobutton(
            mode_frame,
            text="Custom",
            variable=self.mode,
            value="custom",
            command=self.switch_mode,
        )
        custom_rb.pack(anchor="w", padx=10, pady=5)

        month_rb = ttk.Radiobutton(
            mode_frame,
            text="Month",
            variable=self.mode,
            value="month",
            command=self.switch_mode,
        )
        month_rb.pack(anchor="w", padx=10, pady=5)

        # --- Frames for different modes ---
        self.schedule_frame = ttk.Frame(left_frame)
        self.custom_frame = ttk.Frame(left_frame)

        # --- Schedule Mode Widgets ---
        title_label = ttk.Label(self.schedule_frame, text="Title:")
        title_label.pack(padx=10, pady=5, anchor="w")
        self.title_entry = ttk.Entry(self.schedule_frame, width=40)
        self.title_entry.pack(padx=10, pady=5, fill="x")
        self.title_entry.insert(0, "1st Term '25 - '26")

        weeks_label = ttk.Label(self.schedule_frame, text="Weeks (Label, YYYY-MM-DD):")
        weeks_label.pack(padx=10, pady=5, anchor="w")

        weeks_desc = ttk.Label(
            self.schedule_frame,
            text=(
                "Each date represents the Monday (start) of that week. "
                "(Right preview shows a full month view starting Sunday.)"
            ),
        )
        weeks_desc.pack(padx=10, pady=(0, 5), anchor="w")

        weeks_frame = ttk.Frame(self.schedule_frame)
        weeks_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.weeks_text = tk.Text(weeks_frame, height=10, width=40, wrap="word")
        self.weeks_text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            weeks_frame, orient="vertical", command=self.weeks_text.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.weeks_text.config(yscrollcommand=scrollbar.set)

        # --- Custom Mode Widgets ---
        custom_controls_frame = ttk.Frame(self.custom_frame)
        custom_controls_frame.pack(padx=10, pady=5, fill="x")

        # Font Size
        size_label = ttk.Label(custom_controls_frame, text="Font Size:")
        size_label.pack(side="left", padx=(0, 5))
        self.font_size = tk.IntVar(value=48)
        size_spinbox = ttk.Spinbox(
            custom_controls_frame,
            from_=10,
            to=200,
            textvariable=self.font_size,
            width=5,
        )
        size_spinbox.pack(side="left")

        # Horizontal Alignment
        align_label = ttk.Label(custom_controls_frame, text="H-Align:")
        align_label.pack(side="left", padx=(20, 5))
        self.h_alignment = tk.StringVar(value="center")
        h_align_menu = ttk.OptionMenu(
            custom_controls_frame, self.h_alignment, "center", "left", "center", "right"
        )
        h_align_menu.pack(side="left")

        # Vertical Alignment
        v_align_label = ttk.Label(custom_controls_frame, text="V-Align:")
        v_align_label.pack(side="left", padx=(20, 5))
        self.v_alignment = tk.StringVar(value="center")
        v_align_menu = ttk.OptionMenu(
            custom_controls_frame, self.v_alignment, "center", "top", "center", "bottom"
        )
        v_align_menu.pack(side="left")

        custom_label = ttk.Label(self.custom_frame, text="Enter custom text:")
        custom_label.pack(padx=10, pady=5)

        custom_frame_inner = ttk.Frame(self.custom_frame)
        custom_frame_inner.pack(padx=10, pady=5, fill="both", expand=True)

        self.custom_text = tk.Text(custom_frame_inner, height=5, width=40, wrap="word")
        self.custom_text.pack(side="left", fill="both", expand=True)

        custom_scrollbar = ttk.Scrollbar(
            custom_frame_inner, orient="vertical", command=self.custom_text.yview
        )
        custom_scrollbar.pack(side="right", fill="y")
        self.custom_text.config(yscrollcommand=custom_scrollbar.set)

        # --- Action Buttons ---
        action_frame = ttk.Frame(left_frame)
        action_frame.pack(pady=20, fill="x")

        self.preview_button = ttk.Button(
            action_frame, text="Update Preview", command=self.update_preview
        )
        self.preview_button.pack(side="left", padx=5)

        self.save_button = ttk.Button(
            action_frame, text="Save Schedule", command=self.save_config
        )
        self.save_button.pack(side="left", padx=5)

        generate_button = ttk.Button(
            action_frame,
            text="Generate and Set",
            command=self.generate_wallpaper,
        )
        generate_button.pack(side="right", padx=5)

        # --- Right Frame Content (Preview) ---
        self.preview_label = ttk.Label(right_frame)
        self.preview_label.pack(fill="both", expand=True)
        right_frame.bind("<Configure>", self.on_preview_resize)

        # --- Right Column Content ---
        self.right_col_frame = ttk.LabelFrame(
            self.schedule_frame, text="Right Column Content"
        )
        self.right_col_frame.pack(padx=10, pady=10, fill="x")

        self.right_col_mode = tk.StringVar(value="checklist")
        checklist_rb = ttk.Radiobutton(
            self.right_col_frame,
            text="Checklist",
            variable=self.right_col_mode,
            value="checklist",
        )
        checklist_rb.pack(anchor="w", padx=10, pady=5)

        custom_text_rb = ttk.Radiobutton(
            self.right_col_frame,
            text="Custom Text",
            variable=self.right_col_mode,
            value="custom_text",
        )
        custom_text_rb.pack(anchor="w", padx=10, pady=5)

        right_col_text_frame = ttk.Frame(self.right_col_frame)
        right_col_text_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.right_col_text = tk.Text(
            right_col_text_frame, height=5, width=40, wrap="word"
        )
        self.right_col_text.pack(side="left", fill="both", expand=True)

        right_col_scrollbar = ttk.Scrollbar(
            right_col_text_frame, orient="vertical", command=self.right_col_text.yview
        )
        right_col_scrollbar.pack(side="right", fill="y")
        self.right_col_text.config(yscrollcommand=right_col_scrollbar.set)

        # Initial mode view
        self.switch_mode()

    def switch_mode(self):
        if self.mode.get() in ("schedule", "month"):
            self.custom_frame.pack_forget()
            self.schedule_frame.pack(padx=10, pady=10, fill="x")
            self.right_col_frame.pack(padx=10, pady=10, fill="x")
            self.save_button.pack(side="left", padx=5)
        else:
            self.schedule_frame.pack_forget()
            self.right_col_frame.pack_forget()
            self.custom_frame.pack(padx=10, pady=10, fill="x")
            self.save_button.pack_forget()

    def get_wallpaper_image(self, set_wallpaper=False):
        """Generates and returns the wallpaper image without setting it."""
        mode = self.mode.get()
        img = None
        if mode in ("schedule", "month"):
            title = self.title_entry.get()
            weeks_data_str = self.weeks_text.get("1.0", tk.END).strip()
            weeks_data = []
            for line in weeks_data_str.split("\n"):
                if line:
                    try:
                        label, date_str = line.split(",")
                        date = datetime.strptime(date_str.strip(), "%Y-%m-%d")
                        weeks_data.append((label.strip(), date))
                    except ValueError:
                        print(f"Skipping invalid line: {line}")

            if title and weeks_data:
                right_col_content = self.right_col_text.get("1.0", tk.END).strip()
                img = self.generator.generate_schedule_wallpaper(
                    title,
                    weeks_data,
                    right_col_mode=self.right_col_mode.get(),
                    right_col_content=right_col_content,
                    set_wallpaper=set_wallpaper,
                )
            else:
                print("Title or weeks data is empty. Nothing to generate.")
        else:
            custom_text = self.custom_text.get("1.0", tk.END).strip()
            if custom_text:
                img = self.generator.generate_custom_wallpaper(
                    custom_text,
                    font_size=self.font_size.get(),
                    h_align=self.h_alignment.get(),
                    v_align=self.v_alignment.get(),
                    set_wallpaper=set_wallpaper,
                )
            else:
                print("Custom text is empty. Nothing to generate.")
        return img

    def update_preview(self):
        img = self.get_wallpaper_image(set_wallpaper=False)
        if img:
            # Resize for preview
            preview_w = self.preview_label.winfo_width()
            preview_h = self.preview_label.winfo_height()

            if preview_w < 2 or preview_h < 2:  # window not ready
                self.root.after(100, self.update_preview)
                return

            img.thumbnail((preview_w - 10, preview_h - 10), Image.Resampling.LANCZOS)

            self.photo_image = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.photo_image)
            self.preview_label.image = self.photo_image  # Keep a reference

    def on_preview_resize(self, event=None):
        # This is a simple way to trigger a preview update on resize
        # A more sophisticated approach might use a debounce timer
        self.update_preview()

    def generate_wallpaper(self):
        self.get_wallpaper_image(set_wallpaper=True)

    def save_config(self):
        config = {
            "title": self.title_entry.get(),
            "weeks": self.weeks_text.get("1.0", tk.END).strip(),
            "right_col_mode": self.right_col_mode.get(),
            "right_col_content": self.right_col_text.get("1.0", tk.END).strip(),
        }
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=4)
        messagebox.showinfo("Success", "Schedule configuration saved!")

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                config = json.load(f)
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, config.get("title", ""))
            self.weeks_text.delete("1.0", tk.END)
            self.weeks_text.insert("1.0", config.get("weeks", ""))
            self.right_col_mode.set(config.get("right_col_mode", "checklist"))
            self.right_col_text.delete("1.0", tk.END)
            self.right_col_text.insert("1.0", config.get("right_col_content", ""))
        else:
            # Load default weeks if no config file
            default_weeks = [
                ("Week 1", datetime(2025, 8, 11)),
                ("Week 2", datetime(2025, 8, 18)),
                ("Week 3", datetime(2025, 8, 25)),
                ("Week 4", datetime(2025, 9, 1)),
                ("Week 5", datetime(2025, 9, 8)),
                ("Week 6", datetime(2025, 9, 15)),
                ("Week 7", datetime(2025, 9, 22)),
                ("Week 8", datetime(2025, 9, 29)),
                ("Week 9", datetime(2025, 10, 6)),
                ("Week 10", datetime(2025, 10, 13)),
                ("Week 11", datetime(2025, 10, 20)),
                ("Week 12", datetime(2025, 10, 27)),
                ("Week 13", datetime(2025, 11, 3)),
                ("Week 14", datetime(2025, 11, 10)),
            ]
            for label, date in default_weeks:
                self.weeks_text.insert(
                    tk.END, f"{label}, {date.strftime('%Y-%m-%d')}\n"
                )


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = WallpaperApp(root)
        root.mainloop()
    except Exception as e:
        with open("error.log", "w") as f:
            f.write(f"An error occurred:\n{e}\n")
            f.write(traceback.format_exc())
