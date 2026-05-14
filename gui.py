import json
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from datetime import date as Date
import calendar as cal_mod
from PIL import Image, ImageTk
from wallpaper_generator import WallpaperGenerator

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")


def monday_of(d):
    return d - timedelta(days=d.weekday())


def load_config():
    defaults = {
        "title": "",
        "left_pane_mode": "per_week",
        "weeks": "",
        "left_col_content": "",
        "right_pane_mode": "calendar",
        "right_col_content": "",
        "bottom_mode": "none",
        "bottom_content": "",
    }
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
        if "right_col_mode" in data and "bottom_mode" not in data:
            data["bottom_mode"]    = data.pop("right_col_mode", "none")
            data["bottom_content"] = data.pop("right_col_content", "")
        defaults.update(data)
    return defaults


def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)


# ── Monday picker ─────────────────────────────────────────────────────────────

class MondayPicker(tk.Toplevel):
    def __init__(self, parent, initial=None, callback=None):
        super().__init__(parent)
        self.title("Pick a Monday")
        self.resizable(False, False)
        self.grab_set()
        self.callback = callback

        if initial is None:
            initial = monday_of(Date.today())
        if isinstance(initial, datetime):
            initial = initial.date()
        if initial.weekday() != 0:
            initial = monday_of(initial)

        self.selected      = initial
        self.current_month = initial.replace(day=1)
        self._build()
        self._draw()

    def _build(self):
        nav = tk.Frame(self)
        nav.pack(fill="x", padx=10, pady=6)
        tk.Button(nav, text="◀", command=self._prev).pack(side="left")
        self.month_lbl = tk.Label(nav, width=16, font=("Arial", 11, "bold"))
        self.month_lbl.pack(side="left", expand=True)
        tk.Button(nav, text="▶", command=self._next).pack(side="right")

        self.grid_f = tk.Frame(self, padx=10)
        self.grid_f.pack()
        for c, d in enumerate(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]):
            fg = "#1e40af" if c == 0 else "#888"
            tk.Label(self.grid_f, text=d, width=4, font=("Arial", 9, "bold"), fg=fg).grid(row=0, column=c, pady=(0, 4))

        tk.Button(self, text="Select", width=12, command=self._confirm).pack(pady=8)

    def _draw(self):
        for w in self.grid_f.grid_slaves():
            if int(w.grid_info()["row"]) > 0:
                w.destroy()
        self.month_lbl.config(text=self.current_month.strftime("%B %Y"))

        y, m  = self.current_month.year, self.current_month.month
        first = Date(y, m, 1)
        start_col = first.weekday()
        days  = cal_mod.monthrange(y, m)[1]

        row, col = 1, start_col
        for n in range(1, days + 1):
            d   = Date(y, m, n)
            mon = d.weekday() == 0
            sel = d == self.selected
            bg  = "#2563eb" if sel else ("#dbeafe" if mon else "#f3f4f6")
            fg  = "white"   if sel else ("#1e40af" if mon else "#bbb")
            btn = tk.Button(
                self.grid_f, text=str(n), width=3,
                bg=bg, fg=fg, relief="flat", bd=0,
                state="normal" if mon else "disabled",
                command=lambda d=d: self._pick(d),
            )
            btn.grid(row=row, column=col, padx=1, pady=1, ipady=3)
            col += 1
            if col > 6:
                col = 0
                row += 1

    def _pick(self, d):
        self.selected = d
        self._draw()

    def _prev(self):
        m, y = self.current_month.month - 1, self.current_month.year
        if m < 1: m, y = 12, y - 1
        self.current_month = Date(y, m, 1)
        self._draw()

    def _next(self):
        m, y = self.current_month.month + 1, self.current_month.year
        if m > 12: m, y = 1, y + 1
        self.current_month = Date(y, m, 1)
        self._draw()

    def _confirm(self):
        if self.callback:
            self.callback(self.selected)
        self.destroy()


# ── Main app ──────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("School Week Wallpaper")
        self.geometry("1100x660")
        self.minsize(900, 560)
        self._build_ui()
        self._load()
        self.after(120, self._draw_placeholder)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self.columnconfigure(0, weight=2)   # controls
        self.columnconfigure(1, weight=3)   # preview
        self.rowconfigure(0, weight=1)

        # ── Controls column ───────────────────────────────────────────────────
        ctrl = tk.Frame(self)
        ctrl.grid(row=0, column=0, sticky="nsew", padx=(6, 3), pady=6)
        ctrl.columnconfigure(0, weight=1)
        ctrl.rowconfigure(1, weight=1)

        # Title
        title_row = tk.Frame(ctrl, pady=6)
        title_row.grid(row=0, column=0, sticky="ew")
        title_row.columnconfigure(1, weight=1)
        tk.Label(title_row, text="Title:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=(0, 6))
        self.title_var = tk.StringVar()
        tk.Entry(title_row, textvariable=self.title_var, font=("Arial", 10)).grid(row=0, column=1, sticky="ew")

        # Vertical paned window — drag sash to resize panes vs bottom content
        vpane = tk.PanedWindow(ctrl, orient="vertical", sashwidth=6, sashrelief="flat",
                               sashpad=2, bg="#cccccc")
        vpane.grid(row=1, column=0, sticky="nsew", pady=(4, 0))

        # Top pane: left + right config panes
        panes = tk.Frame(vpane)
        panes.columnconfigure(0, weight=1)
        panes.columnconfigure(1, weight=1)
        panes.rowconfigure(0, weight=1)
        self._build_left_pane(panes)
        self._build_right_pane(panes)
        vpane.add(panes, stretch="always", minsize=180)

        # Bottom pane: bottom content
        bot_outer = tk.Frame(vpane)
        bot_outer.columnconfigure(0, weight=1)
        bot_outer.rowconfigure(0, weight=1)
        bot = tk.LabelFrame(bot_outer, text="Bottom Content (below calendar)", font=("Arial", 9, "bold"), padx=6, pady=4)
        bot.grid(row=0, column=0, sticky="nsew")
        bot.columnconfigure(0, weight=1)
        bot.rowconfigure(1, weight=1)
        bm = tk.Frame(bot)
        bm.grid(row=0, column=0, sticky="w")
        self.bottom_mode_var = tk.StringVar(value="none")
        for val, lbl in [("none","None"), ("checklist","Checklist"), ("custom","Custom")]:
            tk.Radiobutton(bm, text=lbl, variable=self.bottom_mode_var, value=val,
                           command=self._on_bottom_mode).pack(side="left", padx=4)
        self.bottom_text = tk.Text(bot, state="disabled", bg="#f0f0f0", font=("Arial", 9))
        self.bottom_text.grid(row=1, column=0, sticky="nsew", pady=(3, 0))
        vpane.add(bot_outer, stretch="always", minsize=60)

        # Buttons
        btns = tk.Frame(ctrl, pady=8)
        btns.grid(row=2, column=0)
        tk.Button(btns, text="Preview Wallpaper", width=20, command=self._preview).pack(side="left", padx=6)
        tk.Button(btns, text="Save & Apply",      width=20, command=self._save_apply).pack(side="left", padx=6)

        # ── Preview column ────────────────────────────────────────────────────
        prev_frame = tk.LabelFrame(self, text="Preview", font=("Arial", 10, "bold"), padx=4, pady=4)
        prev_frame.grid(row=0, column=1, sticky="nsew", padx=(3, 6), pady=6)
        prev_frame.columnconfigure(0, weight=1)
        prev_frame.rowconfigure(0, weight=1)

        self.preview_canvas = tk.Canvas(prev_frame, bg="#111111", highlightthickness=0)
        self.preview_canvas.grid(row=0, column=0, sticky="nsew")

    def _draw_placeholder(self):
        cw = self.preview_canvas.winfo_width()
        ch = self.preview_canvas.winfo_height()
        self.preview_canvas.delete("all")
        self.preview_canvas.create_text(
            cw // 2, ch // 2,
            text="Click 'Preview Wallpaper'\nto generate a preview here.",
            fill="#555555", font=("Arial", 11), justify="center",
        )

    def _build_left_pane(self, parent):
        lf = tk.LabelFrame(parent, text="Left Pane", font=("Arial", 9, "bold"), padx=4, pady=4)
        lf.grid(row=0, column=0, sticky="nsew", padx=(0, 3))
        lf.columnconfigure(0, weight=1)
        lf.rowconfigure(1, weight=1)

        lm = tk.Frame(lf)
        lm.grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.left_mode_var = tk.StringVar(value="per_week")
        for val, lbl in [("per_week","Per Week"), ("checklist","Checklist"), ("custom","Custom")]:
            tk.Radiobutton(lm, text=lbl, variable=self.left_mode_var, value=val,
                           command=self._on_left_mode).pack(side="left", padx=3)

        self.left_content = tk.Frame(lf)
        self.left_content.grid(row=1, column=0, sticky="nsew")
        self.left_content.columnconfigure(0, weight=1)
        self.left_content.rowconfigure(0, weight=1)

        self._build_per_week_frame()
        self._build_left_text_frame()

    def _build_per_week_frame(self):
        f = tk.Frame(self.left_content)
        f.columnconfigure(0, weight=1)
        f.rowconfigure(0, weight=1)
        self.per_week_frame = f

        tree_wrap = tk.Frame(f)
        tree_wrap.grid(row=0, column=0, sticky="nsew")
        tree_wrap.columnconfigure(0, weight=1)
        tree_wrap.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_wrap, columns=("Label","Start Date"), show="headings", height=8)
        self.tree.heading("Label",      text="Label")
        self.tree.heading("Start Date", text="Start (Mon)")
        self.tree.column("Label",      width=90)
        self.tree.column("Start Date", width=110)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<Double-1>", self._on_tree_double_click)

        ctrl = tk.Frame(f)
        ctrl.grid(row=1, column=0, sticky="ew", pady=(3, 0))
        tk.Button(ctrl, text="+ Add",          command=self._add_week).pack(side="left", padx=2)
        tk.Button(ctrl, text="− Remove",       command=self._remove_week).pack(side="left", padx=2)
        tk.Button(ctrl, text="Pick Start…",    command=self._pick_start_date).pack(side="left", padx=2)
        tk.Label(ctrl, text="dbl-click to edit", fg="#999", font=("Arial", 8)).pack(side="left", padx=4)

    def _build_left_text_frame(self):
        f = tk.Frame(self.left_content)
        f.columnconfigure(0, weight=1)
        f.rowconfigure(0, weight=1)
        self.left_text_frame = f
        self.left_text = tk.Text(f, font=("Arial", 9))
        self.left_text.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(f, orient="vertical", command=self.left_text.yview)
        self.left_text.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")

    def _build_right_pane(self, parent):
        rf = tk.LabelFrame(parent, text="Right Pane", font=("Arial", 9, "bold"), padx=4, pady=4)
        rf.grid(row=0, column=1, sticky="nsew", padx=(3, 0))
        rf.columnconfigure(0, weight=1)
        rf.rowconfigure(1, weight=1)

        rm = tk.Frame(rf)
        rm.grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.right_mode_var = tk.StringVar(value="calendar")
        for val, lbl in [("calendar","Calendar"), ("custom","Custom")]:
            tk.Radiobutton(rm, text=lbl, variable=self.right_mode_var, value=val,
                           command=self._on_right_mode).pack(side="left", padx=3)

        self.right_content = tk.Frame(rf)
        self.right_content.grid(row=1, column=0, sticky="nsew")
        self.right_content.columnconfigure(0, weight=1)
        self.right_content.rowconfigure(0, weight=1)

        self.right_cal_frame = tk.Frame(self.right_content)
        self.right_cal_frame.columnconfigure(0, weight=1)
        self.right_cal_frame.rowconfigure(0, weight=1)
        tk.Label(
            self.right_cal_frame,
            text="Monthly calendar is\nauto-generated on the wallpaper.",
            fg="#666", font=("Arial", 9), justify="center",
        ).grid(row=0, column=0, pady=20)

        self.right_custom_frame = tk.Frame(self.right_content)
        self.right_custom_frame.columnconfigure(0, weight=1)
        self.right_custom_frame.rowconfigure(0, weight=1)
        self.right_text = tk.Text(self.right_custom_frame, font=("Arial", 9))
        self.right_text.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(self.right_custom_frame, orient="vertical", command=self.right_text.yview)
        self.right_text.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")

    # ── Mode switches ─────────────────────────────────────────────────────────

    def _on_left_mode(self):
        if self.left_mode_var.get() == "per_week":
            self.left_text_frame.grid_remove()
            self.per_week_frame.grid(row=0, column=0, sticky="nsew")
            if not self.tree.get_children():
                self._auto_seed()
        else:
            self.per_week_frame.grid_remove()
            self.left_text_frame.grid(row=0, column=0, sticky="nsew")

    def _on_right_mode(self):
        if self.right_mode_var.get() == "calendar":
            self.right_custom_frame.grid_remove()
            self.right_cal_frame.grid(row=0, column=0, sticky="nsew")
        else:
            self.right_cal_frame.grid_remove()
            self.right_custom_frame.grid(row=0, column=0, sticky="nsew")

    def _on_bottom_mode(self):
        enabled = self.bottom_mode_var.get() != "none"
        self.bottom_text.config(state="normal" if enabled else "disabled",
                                bg="white"       if enabled else "#f0f0f0")

    # ── Per-week controls ─────────────────────────────────────────────────────

    def _auto_seed(self):
        mon = monday_of(Date.today())
        self.tree.insert("", "end", values=("Week 1", mon.strftime("%Y-%m-%d")))

    def _add_week(self):
        children = self.tree.get_children()
        if children:
            last      = self.tree.item(children[-1], "values")
            m         = re.search(r'(\d+)$', last[0])
            new_label = (last[0][:m.start()] + str(int(m.group(1)) + 1)) if m else last[0] + " 2"
            try:
                new_date = datetime.strptime(last[1], "%Y-%m-%d").date() + timedelta(weeks=1)
            except ValueError:
                new_date = monday_of(Date.today())
        else:
            new_label = "Week 1"
            new_date  = monday_of(Date.today())
        self.tree.insert("", "end", values=(new_label, new_date.strftime("%Y-%m-%d")))

    def _remove_week(self):
        for item in self.tree.selection():
            self.tree.delete(item)

    def _pick_start_date(self):
        children = self.tree.get_children()
        try:
            init = datetime.strptime(self.tree.item(children[0], "values")[1], "%Y-%m-%d").date() if children else monday_of(Date.today())
        except ValueError:
            init = monday_of(Date.today())

        def on_picked(d):
            rows = [self.tree.item(c, "values") for c in self.tree.get_children()]
            for c in self.tree.get_children():
                self.tree.delete(c)
            if rows:
                for i, (label, _) in enumerate(rows):
                    self.tree.insert("", "end", values=(label, (d + timedelta(weeks=i)).strftime("%Y-%m-%d")))
            else:
                self.tree.insert("", "end", values=("Week 1", d.strftime("%Y-%m-%d")))

        MondayPicker(self, initial=init, callback=on_picked)

    def _on_tree_double_click(self, event):
        item = self.tree.identify_row(event.y)
        col  = self.tree.identify_column(event.x)
        if not item or not col:
            return
        col_idx = int(col.replace("#", "")) - 1
        values  = list(self.tree.item(item, "values"))

        if col_idx == 1:
            try:
                init = datetime.strptime(values[1], "%Y-%m-%d").date()
            except ValueError:
                init = monday_of(Date.today())

            def on_picked(d, item=item):
                v    = list(self.tree.item(item, "values"))
                v[1] = d.strftime("%Y-%m-%d")
                self.tree.item(item, values=v)

            MondayPicker(self, initial=init, callback=on_picked)
        else:
            bbox = self.tree.bbox(item, col)
            if not bbox:
                return
            x, y, w, h = bbox
            var   = tk.StringVar(value=values[col_idx])
            entry = tk.Entry(self.tree, textvariable=var, font=("Arial", 9))
            entry.place(x=x, y=y, width=w, height=h)
            entry.focus()
            entry.select_range(0, tk.END)

            def save(e=None):
                v          = list(self.tree.item(item, "values"))
                v[col_idx] = var.get()
                self.tree.item(item, values=v)
                entry.destroy()

            entry.bind("<Return>",   save)
            entry.bind("<FocusOut>", save)
            entry.bind("<Escape>",   lambda e: entry.destroy())

    # ── Load / build config ───────────────────────────────────────────────────

    def _load(self):
        cfg = load_config()
        self.title_var.set(cfg.get("title", ""))

        self.left_mode_var.set(cfg.get("left_pane_mode", "per_week"))
        for c in self.tree.get_children():
            self.tree.delete(c)
        for line in cfg.get("weeks", "").strip().split("\n"):
            if line:
                parts = line.split(",", 1)
                if len(parts) == 2:
                    self.tree.insert("", "end", values=(parts[0].strip(), parts[1].strip()))
        self.left_text.delete("1.0", tk.END)
        self.left_text.insert("1.0", cfg.get("left_col_content", ""))

        self.right_mode_var.set(cfg.get("right_pane_mode", "calendar"))
        self.right_text.delete("1.0", tk.END)
        self.right_text.insert("1.0", cfg.get("right_col_content", ""))

        self.bottom_mode_var.set(cfg.get("bottom_mode", "none"))
        self.bottom_text.config(state="normal")
        self.bottom_text.delete("1.0", tk.END)
        self.bottom_text.insert("1.0", cfg.get("bottom_content", ""))

        self._on_left_mode()
        self._on_right_mode()
        self._on_bottom_mode()

    def _build_config(self):
        rows = [
            f"{self.tree.item(i,'values')[0]},{self.tree.item(i,'values')[1]}"
            for i in self.tree.get_children()
        ]
        return {
            "title":             self.title_var.get().strip(),
            "left_pane_mode":    self.left_mode_var.get(),
            "weeks":             "\n".join(rows),
            "left_col_content":  self.left_text.get("1.0", tk.END).strip(),
            "right_pane_mode":   self.right_mode_var.get(),
            "right_col_content": self.right_text.get("1.0", tk.END).strip(),
            "bottom_mode":       self.bottom_mode_var.get(),
            "bottom_content":    self.bottom_text.get("1.0", tk.END).strip()
                                 if self.bottom_mode_var.get() != "none" else "",
        }

    def _parse_weeks(self, cfg):
        weeks = []
        for line in cfg.get("weeks", "").strip().split("\n"):
            if line:
                parts = line.split(",", 1)
                if len(parts) == 2:
                    try:
                        weeks.append((parts[0].strip(), datetime.strptime(parts[1].strip(), "%Y-%m-%d")))
                    except ValueError:
                        pass
        return weeks

    def _validate_and_generate(self, set_wallpaper=False):
        cfg   = self._build_config()
        weeks = self._parse_weeks(cfg) if cfg["left_pane_mode"] == "per_week" else []

        if not cfg["title"]:
            messagebox.showwarning("Missing", "Enter a wallpaper title.")
            return None
        if cfg["left_pane_mode"] == "per_week" and not weeks:
            messagebox.showwarning("No Weeks", "Add at least one week entry.")
            return None

        gen = WallpaperGenerator()
        return gen.generate_schedule_wallpaper(
            title             = cfg["title"],
            weeks_data        = weeks,
            left_pane_mode    = cfg["left_pane_mode"],
            left_col_content  = cfg["left_col_content"],
            right_pane_mode   = cfg["right_pane_mode"],
            right_col_content = cfg["right_col_content"],
            bottom_mode       = cfg["bottom_mode"],
            bottom_content    = cfg["bottom_content"],
            set_wallpaper     = set_wallpaper,
        )

    # ── Actions ───────────────────────────────────────────────────────────────

    def _preview(self):
        try:
            img = self._validate_and_generate(set_wallpaper=False)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        if img is None:
            return

        self.update_idletasks()
        cw = self.preview_canvas.winfo_width()
        ch = self.preview_canvas.winfo_height()
        if cw < 10 or ch < 10:
            cw, ch = 500, 400

        ratio   = min(cw / img.width, ch / img.height)
        preview = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)

        photo = ImageTk.PhotoImage(preview)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(cw // 2, ch // 2, anchor="center", image=photo)
        self.preview_canvas.image = photo   # keep reference

    def _save_apply(self):
        try:
            img = self._validate_and_generate(set_wallpaper=True)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        if img is None:
            return
        save_config(self._build_config())
        messagebox.showinfo("Done", "Config saved and wallpaper applied.")


if __name__ == "__main__":
    App().mainloop()
