"""
Core logic for generating and setting the dynamic wallpaper.
"""

from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import os
import ctypes

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _hex_to_rgb(hex_color):
    h = str(hex_color).strip().lstrip("#")
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    if len(h) != 6:
        return (180, 180, 180)
    try:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except ValueError:
        return (180, 180, 180)


class WallpaperGenerator:
    def __init__(self):
        self.detect_resolution()
        self.load_fonts()

    def detect_resolution(self):
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        pw = user32.GetSystemMetrics(0)
        ph = user32.GetSystemMetrics(1)
        vw = user32.GetSystemMetrics(78)
        vh = user32.GetSystemMetrics(79)
        self.WIDTH, self.HEIGHT = (vw, vh) if (vw > pw or vh > ph) else (pw, ph)
        self.WIDTH  = int(self.WIDTH  * 1.5)
        self.HEIGHT = int(self.HEIGHT * 1.9) + 800

    def load_fonts(self):
        base = self.WIDTH / 1920.0

        def _f(path, size):
            try:
                return ImageFont.truetype(path, max(8, int(size)))
            except Exception:
                return ImageFont.load_default()

        self.TITLE_FONT       = _f("C:/Windows/Fonts/arialbd.ttf", 70 * base)
        self.WEEK_FONT        = _f("C:/Windows/Fonts/arial.ttf",   28 * base)
        self.WEEK_BOLD_FONT   = _f("C:/Windows/Fonts/arialbd.ttf", 32 * base)
        self.DATE_FONT        = _f("C:/Windows/Fonts/arial.ttf",   34 * base)
        self.DATE_BOLD_FONT   = _f("C:/Windows/Fonts/arialbd.ttf", 40 * base)
        self.TODAY_FONT       = _f("C:/Windows/Fonts/arialbd.ttf", 56 * base)
        self.CUSTOM_TEXT_FONT = _f("C:/Windows/Fonts/seguiemj.ttf", 28 * base)

    def _text_size(self, draw, text, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def _wrap_text(self, draw, text, font, max_width):
        if not text:
            return []
        words = text.split(" ")
        current, lines = words[0], []
        for word in words[1:]:
            if self._text_size(draw, current + " " + word, font)[0] <= max_width:
                current += " " + word
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines

    def _render_text_block(self, draw, content, x, y, max_width, mode="custom", bottom_limit=None, base=1.0):
        if not content:
            return y
        if bottom_limit is None:
            bottom_limit = self.HEIGHT
        _, lh = self._text_size(draw, "Ay", self.CUSTOM_TEXT_FONT)
        line_height = int(lh * 1.6)
        for line in content.split("\n"):
            for i, wl in enumerate(self._wrap_text(draw, line, self.CUSTOM_TEXT_FONT, max_width)):
                indent = int(30 * base) if mode == "todo" and i > 0 else 0
                if y + line_height > bottom_limit:
                    return y
                draw.text((x + indent, y), wl, fill=(180, 180, 180), font=self.CUSTOM_TEXT_FONT)
                y += line_height
        return y

    def generate_schedule_wallpaper(
        self,
        title,
        weeks_data=None,
        left_pane_mode="per_week",
        left_col_content="",
        right_pane_mode="calendar",
        right_col_content="",
        bottom_mode="none",
        bottom_content="",
        todo_items=None,        # list of (label, date, color_hex)
        set_wallpaper=True,
    ):
        base = self.WIDTH / 1920.0
        BG     = (0, 0, 0)
        DIM    = (180, 180, 180)
        BRIGHT = (230, 230, 230)
        WHITE  = (255, 255, 255)
        MONTH_ABBR = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                      7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

        img  = Image.new("RGB", (self.WIDTH, self.HEIGHT), BG)
        draw = ImageDraw.Draw(img)
        now  = datetime.now()

        pad_w        = int(0.04 * self.WIDTH)
        pad_h        = int(0.04 * self.HEIGHT)
        title_area_h = int(0.14 * self.HEIGHT)
        left_col_w   = int(0.52 * self.WIDTH)
        right_col_w  = self.WIDTH - left_col_w - 2 * pad_w
        left_x       = pad_w
        left_y       = pad_h + title_area_h
        right_x      = left_x + left_col_w + int(0.02 * self.WIDTH)
        right_y      = left_y

        # Build date→color map from todo items (used by calendar)
        date_colors = {}
        for _, due, color_hex in (todo_items or []):
            if isinstance(due, datetime):
                due = due.date()
            try:
                date_colors[due] = _hex_to_rgb(color_hex)
            except Exception:
                pass

        # Measure week line height once
        tmp = ImageDraw.Draw(Image.new("RGB", (100, 100)))
        _, lh = self._text_size(tmp, "Ay", self.WEEK_FONT)
        line_h = int(lh * 1.6)

        # ── Title ──────────────────────────────────────────────────────────────
        tw, th = self._text_size(draw, title, self.TITLE_FONT)
        draw.text(
            (self.WIDTH // 2 - tw // 2, pad_h + (title_area_h - th) // 2),
            title, fill=BRIGHT, font=self.TITLE_FONT,
        )

        # ── Left column ────────────────────────────────────────────────────────
        if left_pane_mode == "per_week" and weeks_data:
            cur_week = None
            for i, (_, start) in enumerate(weeks_data):
                if start.date() <= now.date() <= (start + timedelta(days=6)).date():
                    cur_week = i
                    break
            wy = left_y
            for i, (label, start) in enumerate(weeks_data):
                end  = start + timedelta(days=4)
                s    = f"{MONTH_ABBR[start.month]} {start.day:02d}"
                e    = f"{MONTH_ABBR[end.month]} {end.day:02d}"
                text = f"{label}: {s} – {e}"
                font  = self.WEEK_BOLD_FONT if i == cur_week else self.WEEK_FONT
                color = BRIGHT if i == cur_week else DIM
                draw.text((left_x, wy), text, fill=color, font=font)
                wy += line_h

        elif left_pane_mode == "todo":
            draw.text((left_x, left_y), "To do:", fill=BRIGHT, font=self.WEEK_BOLD_FONT)
            _, title_h = self._text_size(draw, "To do:", self.WEEK_BOLD_FONT)
            cy = left_y + int(title_h * 1.8)

            today = now.date()

            # Column x-positions with explicit inter-column gaps
            col_gap    = int(20 * base)
            task_col_w = int(left_col_w * 0.46)
            date_col_w = int(left_col_w * 0.18)
            dl_col_w   = int(left_col_w * 0.18)
            col1_x = left_x
            col2_x = col1_x + task_col_w + col_gap
            col3_x = col2_x + date_col_w + col_gap
            col4_x = col3_x + dl_col_w   + col_gap

            # Header row
            _, hdr_h = self._text_size(draw, "Ay", self.WEEK_BOLD_FONT)
            draw.text((col1_x, cy), "Task",      fill=BRIGHT, font=self.WEEK_BOLD_FONT)
            draw.text((col2_x, cy), "Due Date",  fill=BRIGHT, font=self.WEEK_BOLD_FONT)
            draw.text((col3_x, cy), "Days Left", fill=BRIGHT, font=self.WEEK_BOLD_FONT)
            draw.text((col4_x, cy), "Color",     fill=BRIGHT, font=self.WEEK_BOLD_FONT)
            cy += int(hdr_h * 1.4)

            # Separator under header
            sep_right = col4_x + int(80 * base)
            draw.line([(col1_x, cy - int(hdr_h * 0.2)), (sep_right, cy - int(hdr_h * 0.2))],
                      fill=(90, 90, 90), width=max(1, int(base)))

            # Data rows
            for label, due, color_hex in (todo_items or []):
                if cy >= self.HEIGHT - pad_h:
                    break
                if isinstance(due, datetime):
                    due = due.date()
                days = (due - today).days
                if days > 0:
                    days_str = f"{days}d left"
                elif days == 0:
                    days_str = "today"
                else:
                    days_str = f"{abs(days)}d ago"
                due_str = f"{MONTH_ABBR[due.month]} {due.day:02d}"

                try:
                    sq_color = _hex_to_rgb(color_hex)
                except Exception:
                    sq_color = DIM

                # Truncate label to fit task column
                label_drawn = label
                max_lw = task_col_w - int(4 * base)
                while label_drawn and self._text_size(draw, label_drawn, self.WEEK_FONT)[0] > max_lw:
                    label_drawn = label_drawn[:-1]
                if label_drawn != label:
                    label_drawn = label_drawn.rstrip() + "…"

                _, row_h = self._text_size(draw, "Ay", self.WEEK_FONT)
                draw.text((col1_x, cy), label_drawn, fill=DIM, font=self.WEEK_FONT)
                draw.text((col2_x, cy), due_str,     fill=DIM, font=self.WEEK_FONT)
                draw.text((col3_x, cy), days_str,    fill=DIM, font=self.WEEK_FONT)

                sq_sz = max(8, int(row_h * 0.75))
                sq_y  = cy + (row_h - sq_sz) // 2
                draw.rectangle([col4_x, sq_y, col4_x + sq_sz, sq_y + sq_sz], fill=sq_color)

                cy += line_h

        elif left_pane_mode in ("custom",):
            self._render_text_block(
                draw, left_col_content, left_x, left_y, left_col_w,
                mode=left_pane_mode, bottom_limit=self.HEIGHT - pad_h, base=base,
            )

        # ── Right column ───────────────────────────────────────────────────────
        if right_pane_mode == "calendar":
            month_label = f"{MONTH_ABBR[now.month]} {now.year}"
            m_w, m_h = self._text_size(draw, month_label, self.DATE_BOLD_FONT)
            draw.text((right_x + (right_col_w - m_w) // 2, right_y), month_label, fill=BRIGHT, font=self.DATE_BOLD_FONT)

            weekdays  = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            col_pad   = int(0.02 * self.WIDTH)
            cell_w    = (right_col_w - 2 * col_pad) // 7
            wy_top    = right_y + m_h + int(0.02 * self.HEIGHT)
            header_th = 0

            for idx, wd in enumerate(weekdays):
                tx = right_x + col_pad + idx * cell_w
                twd, thd = self._text_size(draw, wd, self.DATE_BOLD_FONT)
                draw.text((tx + (cell_w - twd) // 2, wy_top), wd, fill=DIM, font=self.DATE_BOLD_FONT)
                header_th = max(header_th, thd)

            first_of_month   = datetime(now.year, now.month, 1)
            days_to_subtract = (first_of_month.weekday() + 1) % 7
            first_cell       = first_of_month - timedelta(days=days_to_subtract)
            num_rows         = 6
            row_h            = int(header_th * 1.8)
            cal_top          = wy_top + int(header_th * 1.6)
            extra_pad        = max(8, int(row_h * 0.5))

            row_highlights = [
                first_cell + timedelta(days=r * 7) <= now <= first_cell + timedelta(days=r * 7 + 6)
                for r in range(num_rows)
            ]
            row_heights = [row_h + (extra_pad if hl else 0) for hl in row_highlights]
            row_y, cursor = [], cal_top
            for h in row_heights:
                row_y.append(cursor)
                cursor += h

            thd2 = header_th
            for row in range(num_rows):
                for col in range(7):
                    dt       = first_cell + timedelta(days=row * 7 + col)
                    tx       = right_x + col_pad + col * cell_w
                    day_str  = str(dt.day)
                    in_month = dt.month == now.month
                    hl       = row_highlights[row]

                    # Font
                    if dt.date() == now.date():
                        fnt = self.TODAY_FONT
                    elif hl:
                        fnt = self.DATE_BOLD_FONT
                    else:
                        fnt = self.DATE_FONT

                    # Color — task color overrides everything
                    task_color = date_colors.get(dt.date())
                    if task_color:
                        fill = task_color
                    elif dt.date() == now.date():
                        fill = WHITE
                    elif hl:
                        fill = BRIGHT if in_month else (150, 150, 150)
                    else:
                        fill = BRIGHT if in_month else (120, 120, 120)

                    twd, thd = self._text_size(draw, day_str, fnt)
                    cell_cy  = row_y[row] + (row_heights[row] - thd) // 2
                    draw.text((tx + (cell_w - twd) // 2, cell_cy), day_str, fill=fill, font=fnt)
                    thd2 = thd

            if bottom_mode != "none" and bottom_content:
                num_y     = row_y[-1] + row_heights[-1]
                content_y = num_y + int(thd2 * 2.5)
                b_limit   = right_y + (self.HEIGHT - right_y) - int(0.02 * self.HEIGHT)
                self._render_text_block(
                    draw, bottom_content, right_x, content_y,
                    right_col_w - int(40 * base),
                    mode=bottom_mode, bottom_limit=b_limit, base=base,
                )

        elif right_pane_mode == "custom":
            self._render_text_block(
                draw, right_col_content, right_x, right_y, right_col_w,
                mode="custom", bottom_limit=self.HEIGHT - pad_h, base=base,
            )

        if set_wallpaper:
            self.save_and_set_wallpaper(img)
        return img

    def generate_custom_wallpaper(
        self, text, font_size=48, h_align="center", v_align="center", set_wallpaper=True
    ):
        img  = Image.new("RGB", (self.WIDTH, self.HEIGHT), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        base = self.WIDTH / 1920.0
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(font_size * base))
        except Exception:
            font = ImageFont.load_default()

        lines        = text.split("\n")
        line_heights = []
        for line in lines:
            _, h = self._text_size(draw, line, font)
            line_heights.append(h)
        total_h = sum(line_heights)

        y = (0.05 * self.HEIGHT if v_align == "top"
             else self.HEIGHT - total_h - 0.05 * self.HEIGHT if v_align == "bottom"
             else (self.HEIGHT - total_h) / 2)

        for i, line in enumerate(lines):
            w, _ = self._text_size(draw, line, font)
            x = (0.05 * self.WIDTH if h_align == "left"
                 else self.WIDTH - w - 0.05 * self.WIDTH if h_align == "right"
                 else (self.WIDTH - w) / 2)
            draw.text((x, y), line, fill=(255, 255, 255), font=font)
            y += line_heights[i]

        if set_wallpaper:
            self.save_and_set_wallpaper(img)
        return img

    def save_and_set_wallpaper(self, img):
        path = os.path.join(SCRIPT_DIR, "wallpaper.png")
        img.save(path)
        try:
            ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
            print(f"Wallpaper set: {path}")
        except Exception as e:
            print(f"Failed to set wallpaper: {e}")
