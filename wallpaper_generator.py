"""
Core logic for generating and setting the dynamic wallpaper.
"""

from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import os
import ctypes


class WallpaperGenerator:
    def __init__(self):
        self.detect_resolution()
        self.load_fonts()

    def detect_resolution(self):
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()

        primary_width = user32.GetSystemMetrics(0)
        primary_height = user32.GetSystemMetrics(1)

        SM_CXVIRTUALSCREEN = 78
        SM_CYVIRTUALSCREEN = 79
        virtual_w = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
        virtual_h = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)

        if virtual_w > primary_width or virtual_h > primary_height:
            self.WIDTH, self.HEIGHT = virtual_w, virtual_h
        else:
            self.WIDTH, self.HEIGHT = primary_width, primary_height

        # Increase vertical space: scale width moderately but scale height more
        # and add extra padding so right-column content has room.
        scale_factor_width = 1.5
        scale_factor_height = 1.9
        extra_height = 800

        self.WIDTH = int(self.WIDTH * scale_factor_width)
        self.HEIGHT = int(self.HEIGHT * scale_factor_height) + extra_height

    def load_fonts(self):
        base = self.WIDTH / 1920.0

        def _load_font(path, size):
            try:
                return ImageFont.truetype(path, max(8, int(size)))
            except:
                return ImageFont.load_default()

        FONT_REGULAR = "C:/Windows/Fonts/arial.ttf"
        FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"
        FONT_EMOJI = "C:/Windows/Fonts/seguiemj.ttf"

        self.TITLE_FONT = _load_font(FONT_BOLD, 70 * base)
        self.WEEK_FONT = _load_font(FONT_REGULAR, 28 * base)
        self.WEEK_BOLD_FONT = _load_font(FONT_BOLD, 32 * base)
        self.DATE_FONT = _load_font(FONT_REGULAR, 34 * base)
        self.DATE_BOLD_FONT = _load_font(FONT_BOLD, 40 * base)
        self.TODAY_FONT = _load_font(FONT_BOLD, 56 * base)
        self.CUSTOM_TEXT_FONT = _load_font(FONT_EMOJI, 28 * base)

    def _text_size(self, draw, text, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def _wrap_text(self, draw, text, font, max_width):
        if not text:
            return []

        lines = []
        words = text.split(" ")

        current_line = words[0]
        for word in words[1:]:
            if self._text_size(draw, current_line + " " + word, font)[0] <= max_width:
                current_line += " " + word
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)

        return lines

    def generate_schedule_wallpaper(
        self,
        title,
        weeks_data,
        right_col_mode="checklist",
        right_col_content="",
        set_wallpaper=True,
    ):
        base = self.WIDTH / 1920.0
        BACKGROUND_COLOR = (0, 0, 0)
        DEFAULT_TEXT_COLOR = (180, 180, 180)
        WEEK_HIGHLIGHT_COLOR = (230, 230, 230)
        TODAY_COLOR = (255, 255, 255)
        MONTH_ABBR = {
            1: "Jan",
            2: "Feb",
            3: "Mar",
            4: "Apr",
            5: "May",
            6: "Jun",
            7: "Jul",
            8: "Aug",
            9: "Sep",
            10: "Oct",
            11: "Nov",
            12: "Dec",
        }

        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(img)

        now = datetime.now()
        current_week_index = None
        for i, (_, start) in enumerate(weeks_data):
            if start.date() <= now.date() <= (start + timedelta(days=6)).date():
                current_week_index = i
                break

        padding_w = int(0.04 * self.WIDTH)
        padding_h = int(0.04 * self.HEIGHT)
        title_area_h = int(0.14 * self.HEIGHT)
        left_col_w = int(0.52 * self.WIDTH)
        right_col_w = self.WIDTH - left_col_w - 2 * padding_w

        left_x = padding_w
        left_y = padding_h + title_area_h
        right_x = left_x + left_col_w + int(0.02 * self.WIDTH)
        right_y = left_y

        img_tmp = Image.new("RGB", (100, 100))
        drw_tmp = ImageDraw.Draw(img_tmp)
        _, line_h = self._text_size(drw_tmp, "Ay", self.WEEK_FONT)
        line_h = int(line_h * 1.6)

        tw, th = self._text_size(draw, title, self.TITLE_FONT)
        draw.text(
            (self.WIDTH // 2 - tw // 2, padding_h + (title_area_h - th) // 2),
            title,
            fill=WEEK_HIGHLIGHT_COLOR,
            font=self.TITLE_FONT,
        )

        wy = left_y
        for i, (label, start) in enumerate(weeks_data):
            end = start + timedelta(days=4)
            start_str = f"{MONTH_ABBR[start.month]} {start.day:02d}"
            end_str = f"{MONTH_ABBR[end.month]} {end.day:02d}"
            left_text = f"{label}: {start_str} – {end_str}"
            font = self.WEEK_BOLD_FONT if i == current_week_index else self.WEEK_FONT
            color = (
                WEEK_HIGHLIGHT_COLOR if i == current_week_index else DEFAULT_TEXT_COLOR
            )
            draw.text((left_x, wy), left_text, fill=color, font=font)
            wy += line_h

        # --- Right Column: Month view (Sunday-first) ---
        # Render the full month containing "now", with weeks as rows.
        month_label = f"{MONTH_ABBR[now.month]} {now.year}"
        m_w, m_h = self._text_size(draw, month_label, self.DATE_BOLD_FONT)
        mx = right_x + (right_col_w - m_w) // 2
        draw.text(
            (mx, right_y),
            month_label,
            fill=WEEK_HIGHLIGHT_COLOR,
            font=self.DATE_BOLD_FONT,
        )

        # Weekday headers: Sunday first
        weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        col_padding = int(0.02 * self.WIDTH)
        usable_w = right_col_w - 2 * col_padding
        cell_w = usable_w // 7

        wy_top = right_y + m_h + int(0.02 * self.HEIGHT)
        header_th = 0
        for idx, wd in enumerate(weekdays):
            tx = right_x + col_padding + idx * cell_w
            twd, thd = self._text_size(draw, wd, self.DATE_BOLD_FONT)
            draw.text(
                (tx + (cell_w - twd) // 2, wy_top),
                wd,
                fill=DEFAULT_TEXT_COLOR,
                font=self.DATE_BOLD_FONT,
            )
            header_th = max(header_th, thd)

        # Calculate first calendar cell (the Sunday on or before the 1st of the month)
        first_of_month = datetime(now.year, now.month, 1)
        days_to_subtract = (first_of_month.weekday() + 1) % 7
        first_cell = first_of_month - timedelta(days=days_to_subtract)

        # Build calendar rows (max 6 weeks to cover all months)
        num_rows = 6
        row_h = int(header_th * 1.8)
        cal_top = wy_top + int(header_th * 1.6)

        # Build per-row height to add extra padding for the highlighted week
        highlighted_week_row = None
        row_is_highlight_vals = []
        for row in range(num_rows):
            if (
                first_cell + timedelta(days=row * 7)
                <= now
                <= first_cell + timedelta(days=row * 7 + 6)
            ):
                row_is_highlight_vals.append(True)
                highlighted_week_row = row
            else:
                row_is_highlight_vals.append(False)

        extra_padding = max(8, int(row_h * 0.5))
        row_heights = [
            row_h + (extra_padding if is_hl else 0) for is_hl in row_is_highlight_vals
        ]

        # Compute y position for each row
        row_positions = []
        y_cursor = cal_top
        for h in row_heights:
            row_positions.append(y_cursor)
            y_cursor += h

        # Draw each day, centering vertically within its row height
        thd2 = header_th
        for row in range(num_rows):
            for col in range(7):
                dt = first_cell + timedelta(days=row * 7 + col)
                tx = right_x + col_padding + col * cell_w
                day_str = str(dt.day)

                in_current_month = dt.month == now.month
                row_is_highlight = row_is_highlight_vals[row]

                # Choose font and color
                if dt.date() == now.date():
                    fnt = self.TODAY_FONT
                    col_fill = TODAY_COLOR
                elif row_is_highlight:
                    fnt = self.DATE_BOLD_FONT
                    col_fill = (
                        WEEK_HIGHLIGHT_COLOR if in_current_month else (150, 150, 150)
                    )
                else:
                    fnt = self.DATE_FONT
                    col_fill = (
                        WEEK_HIGHLIGHT_COLOR if in_current_month else (120, 120, 120)
                    )

                twd, thd = self._text_size(draw, day_str, fnt)
                # center vertically within the row
                cell_y = row_positions[row] + (row_heights[row] - thd) // 2
                draw.text(
                    (tx + (cell_w - twd) // 2, cell_y), day_str, fill=col_fill, font=fnt
                )
                thd2 = thd

        num_y = row_positions[-1] + row_heights[-1]

        # --- Right Column: Checklist or Custom Text ---
        if right_col_content and "thd2" in locals():
            content_y = num_y + int(thd2 * 2.5)

            # Max width for text wrapping in the right column
            max_text_width = right_col_w - int(
                40 * base
            )  # 20 base for box, 20 for padding

            # Determine bottom limit for right column content so we don't draw off-canvas
            bottom_limit = right_y + (self.HEIGHT - right_y) - int(0.02 * self.HEIGHT)

            original_lines = right_col_content.split("\n")

            stop_drawing = False
            for line in original_lines:
                if stop_drawing:
                    break
                wrapped_lines = self._wrap_text(
                    draw, line, self.CUSTOM_TEXT_FONT, max_text_width
                )

                # Draw all wrapped lines, starting with the first
                for i, wrapped_line in enumerate(wrapped_lines):
                    # For checklist mode, we indent wrapped lines to align them with the first
                    indent = (
                        int(30 * base) if right_col_mode == "checklist" and i > 0 else 0
                    )

                    _, line_h_content = self._text_size(
                        draw, "Ay", self.CUSTOM_TEXT_FONT
                    )
                    line_height = int(line_h_content * 1.6)

                    # If drawing this line would exceed the bottom limit, stop to avoid invisible overflow
                    if content_y + line_height > bottom_limit:
                        stop_drawing = True
                        break

                    draw.text(
                        (right_x + indent, content_y),
                        wrapped_line,
                        fill=DEFAULT_TEXT_COLOR,
                        font=self.CUSTOM_TEXT_FONT,
                    )
                    content_y += line_height

        if set_wallpaper:
            self.save_and_set_wallpaper(img)
        return img

    def generate_custom_wallpaper(
        self, text, font_size=48, h_align="center", v_align="center", set_wallpaper=True
    ):
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        base = self.WIDTH / 1920.0
        try:
            custom_font = ImageFont.truetype(
                "C:/Windows/Fonts/arial.ttf", int(font_size * base)
            )
        except:
            custom_font = ImageFont.load_default()

        lines = text.split("\n")
        total_text_height = 0
        line_heights = []

        for line in lines:
            _, h = self._text_size(draw, line, custom_font)
            line_heights.append(h)
            total_text_height += h

        if v_align == "top":
            y = 0.05 * self.HEIGHT
        elif v_align == "bottom":
            y = self.HEIGHT - total_text_height - (0.05 * self.HEIGHT)
        else:  # center
            y = (self.HEIGHT - total_text_height) / 2

        for i, line in enumerate(lines):
            w, _ = self._text_size(draw, line, custom_font)
            if h_align == "left":
                x = 0.05 * self.WIDTH
            elif h_align == "right":
                x = self.WIDTH - w - (0.05 * self.WIDTH)
            else:  # center
                x = (self.WIDTH - w) / 2

            draw.text((x, y), line, fill=(255, 255, 255), font=custom_font)
            y += line_heights[i]

        if set_wallpaper:
            self.save_and_set_wallpaper(img)
        return img

    def save_and_set_wallpaper(self, img):
        WALLPAPER_PATH = os.path.join(os.getcwd(), "wallpaper.png")
        img.save(WALLPAPER_PATH)
        try:
            ctypes.windll.user32.SystemParametersInfoW(20, 0, WALLPAPER_PATH, 3)
            print(f"Wallpaper set successfully: {WALLPAPER_PATH}")
        except Exception as e:
            print(f"Failed to set wallpaper: {e}")
