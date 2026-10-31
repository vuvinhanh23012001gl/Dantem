#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Entry point để khởi động ứng dụng PLC Robot Simulator."""

import os
import sys
import tkinter as tk

# Đảm bảo thư mục gốc dự án được thêm vào sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from app_demorobot.ui.main_window import MainWindow


def main():
    root = tk.Tk()
    
    # Cho phép hiển thị sắc nét trên màn hình High-DPI Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
