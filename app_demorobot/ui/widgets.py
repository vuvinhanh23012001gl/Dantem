"""Các widget giao diện tùy biến cho Robot PLC Simulator."""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Tuple
from app_demorobot.ui.theme import (
    BG_CARD,
    BG_CONSOLE,
    BG_INPUT,
    BORDER_COLOR,
    COLOR_BLUE,
    COLOR_CYAN,
    COLOR_GREEN,
    COLOR_PURPLE,
    COLOR_RED,
    COLOR_YELLOW,
    FONT_BOLD,
    FONT_COORDINATE,
    FONT_HEADER,
    FONT_MONO,
    FONT_NORMAL,
    FONT_SMALL,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class TowerLightWidget(tk.Frame):
    """Đèn tháp tín hiệu 3 tầng (Đỏ, Vàng, Xanh) kèm còi cảnh báo mô phỏng phần cứng PLC."""

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_CARD, **kwargs)
        
        self.canvas = tk.Canvas(
            self,
            width=68,
            height=130,
            bg=BG_CARD,
            highlightthickness=0,
        )
        self.canvas.pack(side=tk.TOP, pady=2)

        # Trạng thái ban đầu
        self.green_on = True
        self.yellow_on = False
        self.red_on = False
        self.buzzer_on = False

        self._draw_tower()

    def set_lights(self, green: bool, yellow: bool, red: bool, buzzer: bool = False) -> None:
        """Cập nhật trạng thái sáng của các tầng đèn và còi."""
        self.green_on = green
        self.yellow_on = yellow
        self.red_on = red
        self.buzzer_on = buzzer
        self._draw_tower()

    def _draw_tower(self) -> None:
        self.canvas.delete("all")
        cx = 34  # Tâm trục X

        # Thân tháp / Hộp chứa
        self.canvas.create_rectangle(cx - 15, 8, cx + 15, 96, fill="#2c313c", outline=BORDER_COLOR, width=2)

        # Chân tháp
        self.canvas.create_rectangle(cx - 4, 96, cx + 4, 116, fill="#4b5563", outline="")
        self.canvas.create_rectangle(cx - 16, 116, cx + 16, 124, fill="#374151", outline="")

        # 1. Đèn ĐỎ (Top)
        red_fill = COLOR_RED if self.red_on else "#3d1818"
        red_outline = "#ff8a8a" if self.red_on else "#2b1010"
        self.canvas.create_oval(cx - 11, 12, cx + 11, 34, fill=red_fill, outline=red_outline, width=1.5)
        if self.red_on:
            self.canvas.create_oval(cx - 5, 16, cx + 1, 22, fill="#ffffff", outline="")

        # 2. Đèn VÀNG (Middle)
        yel_fill = COLOR_YELLOW if self.yellow_on else "#3d2e13"
        yel_outline = "#ffd470" if self.yellow_on else "#2d200b"
        self.canvas.create_oval(cx - 11, 40, cx + 11, 62, fill=yel_fill, outline=yel_outline, width=1.5)
        if self.yellow_on:
            self.canvas.create_oval(cx - 5, 44, cx + 1, 50, fill="#ffffff", outline="")

        # 3. Đèn XANH (Bottom)
        grn_fill = COLOR_GREEN if self.green_on else "#122e20"
        grn_outline = "#6ee7b7" if self.green_on else "#0c2116"
        self.canvas.create_oval(cx - 11, 68, cx + 11, 90, fill=grn_fill, outline=grn_outline, width=1.5)
        if self.green_on:
            self.canvas.create_oval(cx - 5, 72, cx + 1, 78, fill="#ffffff", outline="")

        # Biểu tượng Còi (Buzzer)
        buzzer_color = COLOR_RED if self.buzzer_on else TEXT_MUTED
        self.canvas.create_text(
            cx, 122,
            text="🔊 BEEP" if self.buzzer_on else "🔇 OFF",
            fill=buzzer_color,
            font=("Segoe UI", 7, "bold"),
        )


class PoseCardWidget(tk.Frame):
    """Khung hiển thị trực quan thông số tọa độ 6-DOF (X, Y, Z, Rx, Ry, Rz)."""

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_CARD, **kwargs)
        self.labels: Dict[str, tk.Label] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        axes = [
            ("X", "mm", 0, 0),
            ("Y", "mm", 0, 1),
            ("Z", "mm", 0, 2),
            ("Rx", "°", 1, 0),
            ("Ry", "°", 1, 1),
            ("Rz", "°", 1, 2),
        ]

        self.grid_columnconfigure((0, 1, 2), weight=1)

        for name, unit, r, c in axes:
            card = tk.Frame(self, bg=BG_INPUT, bd=1, relief=tk.SOLID, padx=6, pady=4)
            card.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")

            title_lbl = tk.Label(
                card,
                text=f"{name} ({unit})",
                font=FONT_SMALL,
                fg=TEXT_SECONDARY,
                bg=BG_INPUT,
            )
            title_lbl.pack(anchor="w")

            val_lbl = tk.Label(
                card,
                text="0.00",
                font=FONT_COORDINATE,
                fg=COLOR_CYAN,
                bg=BG_INPUT,
            )
            val_lbl.pack(anchor="e")
            self.labels[name.lower()] = val_lbl

    def update_pose(self, pose: Dict[str, float]) -> None:
        """Cập nhật số liệu hiển thị trên các trục."""
        for key in ["x", "y", "z", "rx", "ry", "rz"]:
            if key in pose and key in self.labels:
                val = float(pose[key])
                self.labels[key].config(text=f"{val:.2f}")


class LogViewerWidget(tk.Frame):
    """Khung hiển thị System Activity Log với màu sắc và bộ lọc."""

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_CARD, **kwargs)
        
        self.auto_scroll_var = tk.BooleanVar(value=True)
        self._build_ui()

    def _build_ui(self) -> None:
        # Thanh công cụ Log
        top_bar = tk.Frame(self, bg=BG_CARD)
        top_bar.pack(fill=tk.X, padx=4, pady=(2, 4))

        title = tk.Label(top_bar, text="Hoạt động hệ thống (Activity Log)", font=FONT_HEADER, fg=TEXT_PRIMARY, bg=BG_CARD)
        title.pack(side=tk.LEFT)

        clear_btn = tk.Button(
            top_bar,
            text="🗑️ Xóa Log",
            font=FONT_SMALL,
            bg="#374151",
            fg=TEXT_PRIMARY,
            activebackground="#4b5563",
            activeforeground="#ffffff",
            bd=0,
            padx=8,
            pady=2,
            command=self.clear,
        )
        clear_btn.pack(side=tk.RIGHT)

        auto_chk = tk.Checkbutton(
            top_bar,
            text="Tự cuộn",
            variable=self.auto_scroll_var,
            font=FONT_SMALL,
            fg=TEXT_SECONDARY,
            bg=BG_CARD,
            selectcolor=BG_INPUT,
            activebackground=BG_CARD,
        )
        auto_chk.pack(side=tk.RIGHT, padx=6)

        # Khung văn bản Log
        text_frame = tk.Frame(self, bg=BG_CONSOLE, bd=1, relief=tk.SOLID)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        self.text_widget = tk.Text(
            text_frame,
            bg=BG_CONSOLE,
            fg=TEXT_PRIMARY,
            font=FONT_MONO,
            wrap=tk.WORD,
            bd=0,
            highlightthickness=0,
            padx=8,
            pady=6,
        )
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Định nghĩa các tags màu
        self.text_widget.tag_configure("TS", foreground=TEXT_MUTED)
        self.text_widget.tag_configure("INFO", foreground="#60a5fa")     # Xanh dương
        self.text_widget.tag_configure("SUCCESS", foreground=COLOR_GREEN) # Xanh lá
        self.text_widget.tag_configure("WARN", foreground=COLOR_YELLOW)   # Vàng
        self.text_widget.tag_configure("ERROR", foreground=COLOR_RED)     # Đỏ
        self.text_widget.tag_configure("CMD_IN", foreground=COLOR_PURPLE) # Tím
        self.text_widget.tag_configure("CMD_OUT", foreground="#38bdf8")   # Xanh sáng

        self.text_widget.config(state=tk.DISABLED)

    def append_log(self, timestamp: str, level: str, message: str) -> None:
        """Thêm một dòng log có định dạng màu sắc."""
        self.text_widget.config(state=tk.NORMAL)
        
        # Thêm timestamp
        self.text_widget.insert(tk.END, f"[{timestamp}] ", "TS")
        
        # Thêm Level tag
        lvl = level.upper()
        tag = lvl if lvl in ["INFO", "SUCCESS", "WARN", "ERROR", "CMD_IN", "CMD_OUT"] else "INFO"
        self.text_widget.insert(tk.END, f"[{lvl}] ", tag)
        
        # Thêm nội dung
        self.text_widget.insert(tk.END, f"{message}\n", tag)

        if self.auto_scroll_var.get():
            self.text_widget.see(tk.END)

        self.text_widget.config(state=tk.DISABLED)

    def clear(self) -> None:
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.config(state=tk.DISABLED)


class CommandHistoryTable(tk.Frame):
    """Bảng hiển thị danh sách các lệnh nhận được hoặc đã gửi."""

    def __init__(self, parent: tk.Widget, title: str, columns: List[Tuple[str, str, int]], **kwargs):
        super().__init__(parent, bg=BG_CARD, **kwargs)
        self.columns_info = columns
        self.title_text = title
        self._build_ui()

    def _build_ui(self) -> None:
        top_bar = tk.Frame(self, bg=BG_CARD)
        top_bar.pack(fill=tk.X, padx=4, pady=(2, 4))

        title_lbl = tk.Label(top_bar, text=self.title_text, font=FONT_HEADER, fg=TEXT_PRIMARY, bg=BG_CARD)
        title_lbl.pack(side=tk.LEFT)

        clear_btn = tk.Button(
            top_bar,
            text="Xóa danh sách",
            font=FONT_SMALL,
            bg="#374151",
            fg=TEXT_PRIMARY,
            activebackground="#4b5563",
            activeforeground="#ffffff",
            bd=0,
            padx=6,
            pady=1,
            command=self.clear,
        )
        clear_btn.pack(side=tk.RIGHT)

        # Style Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Custom.Treeview",
            background=BG_INPUT,
            foreground=TEXT_PRIMARY,
            fieldbackground=BG_INPUT,
            font=FONT_SMALL,
            rowheight=22,
        )
        style.configure(
            "Custom.Treeview.Heading",
            background="#2c313c",
            foreground=TEXT_PRIMARY,
            font=FONT_BOLD,
            relief="flat",
        )
        style.map(
            "Custom.Treeview",
            background=[("selected", "#3b82f6")],
            foreground=[("selected", "#ffffff")],
        )

        col_ids = [col[0] for col in self.columns_info]
        self.tree = ttk.Treeview(
            self,
            columns=col_ids,
            show="headings",
            style="Custom.Treeview",
            selectmode="browse",
        )

        for col_id, col_name, width in self.columns_info:
            self.tree.heading(col_id, text=col_name)
            self.tree.column(col_id, width=width, anchor="w")

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def add_row(self, values: List[str]) -> None:
        """Chèn bản ghi mới lên đầu danh sách."""
        self.tree.insert("", 0, values=values)
        # Giới hạn số dòng lưu trữ tối đa (200 dòng)
        children = self.tree.get_children()
        if len(children) > 200:
            for item in children[200:]:
                self.tree.delete(item)

    def clear(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
