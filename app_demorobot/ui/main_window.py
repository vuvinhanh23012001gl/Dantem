"""Cửa sổ giao diện chính của ứng dụng PLC Robot Simulator."""

import queue
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from app_demorobot.config.settings import (
    DEFAULT_HOST,
    DEFAULT_MOTION_DELAY_SEC,
    DEFAULT_PORT,
    ERROR_CODES,
    HOME_POSE,
)
from app_demorobot.core.motion_sim import MotionSimulator
from app_demorobot.core.robot_state import RobotState, StateEnum
from app_demorobot.network.tcp_server import PLCTCPServer
from app_demorobot.network.test_client import TestClient
from app_demorobot.ui.theme import (
    BG_CARD,
    BG_CARD_HEADER,
    BG_CONSOLE,
    BG_INPUT,
    BG_MAIN,
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
    FONT_LARGE_STATUS,
    FONT_MONO,
    FONT_NORMAL,
    FONT_SMALL,
    FONT_TITLE,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from app_demorobot.ui.widgets import (
    CommandHistoryTable,
    LogViewerWidget,
    PoseCardWidget,
    TowerLightWidget,
)


class MainWindow:
    """Quản lý toàn bộ giao diện và liên kết các thành phần lõi của ứng dụng giả lập."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PLC Robot Simulator (PROD4) - Giao tiếp Vision TCP Socket")
        self.root.geometry("1260x820")
        self.root.minsize(1050, 720)
        self.root.configure(bg=BG_MAIN)

        # Hàng đợi sự kiện đa luồng
        self.event_queue = queue.Queue()

        # Khởi tạo mô hình nghiệp vụ
        self.robot_state = RobotState(on_change_callback=self._on_state_change)
        self.motion_sim = MotionSimulator(self.robot_state)
        self.tcp_server = PLCTCPServer(
            robot_state=self.robot_state,
            motion_sim=self.motion_sim,
            event_queue=self.event_queue,
            host=DEFAULT_HOST,
            port=DEFAULT_PORT,
        )

        # Test Client tích hợp sẵn
        self.test_client = TestClient(on_response_callback=self._on_test_client_response)

        # Biến giao diện
        self.host_var = tk.StringVar(value=DEFAULT_HOST)
        self.port_var = tk.StringVar(value=str(DEFAULT_PORT))
        self.delay_var = tk.DoubleVar(value=DEFAULT_MOTION_DELAY_SEC)
        self.error_select_var = tk.StringVar(value="E01")
        self.test_status_var = tk.StringVar(value="Client: Chưa kết nối")

        # Tọa độ gửi thử trong Test Client
        self.test_x_var = tk.StringVar(value="450.50")
        self.test_y_var = tk.StringVar(value="-120.25")
        self.test_z_var = tk.StringVar(value="210.00")
        self.test_rx_var = tk.StringVar(value="180.00")
        self.test_ry_var = tk.StringVar(value="0.00")
        self.test_rz_var = tk.StringVar(value="45.00")

        self._build_layout()

        # Bắt đầu vòng lặp quét sự kiện đa luồng
        self.root.after(50, self._poll_events)

        # Đăng ký sự kiện tắt ứng dụng
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Tự động bật server ngay khi mở ứng dụng
        self.root.after(200, self.toggle_server)

    def _build_layout(self) -> None:
        """Xây dựng bố cục 2 cột chính."""
        # 1. Header Bar
        header = tk.Frame(self.root, bg=BG_CARD_HEADER, padx=16, pady=8, bd=1, relief=tk.SOLID)
        header.pack(fill=tk.X, side=tk.TOP)

        app_title = tk.Label(
            header,
            text="🤖 PLC ROBOT CONTROLLER SIMULATOR (PROD4)",
            font=FONT_TITLE,
            fg=TEXT_PRIMARY,
            bg=BG_CARD_HEADER,
        )
        app_title.pack(side=tk.LEFT)

        app_sub = tk.Label(
            header,
            text="Giao tiếp mạng TCP Socket | Cổng chuẩn: 2000 | Định dạng: ASCII + CRLF",
            font=FONT_SMALL,
            fg=TEXT_SECONDARY,
            bg=BG_CARD_HEADER,
        )
        app_sub.pack(side=tk.LEFT, padx=16)

        # 2. Main Content Split (Left & Right)
        content_frame = tk.Frame(self.root, bg=BG_MAIN, padx=8, pady=8)
        content_frame.pack(fill=tk.BOTH, expand=True)

        left_col = tk.Frame(content_frame, bg=BG_MAIN, width=480)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 6))

        right_col = tk.Frame(content_frame, bg=BG_MAIN)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(6, 0))

        # Xây dựng các khối cột trái
        self._build_server_card(left_col)
        self._build_status_card(left_col)
        self._build_pose_card(left_col)
        self._build_hardware_controls_card(left_col)
        self._build_test_client_card(left_col)

        # Xây dựng các khối cột phải
        self._build_history_and_logs(right_col)

    def _build_server_card(self, parent: tk.Widget) -> None:
        """Khối cấu hình và trạng thái TCP Server."""
        card = tk.LabelFrame(parent, text=" 🌐 Cấu hình Mạng & Server TCP ", font=FONT_HEADER, bg=BG_CARD, fg=TEXT_PRIMARY, bd=1, padx=8, pady=6)
        card.pack(fill=tk.X, pady=(0, 6))

        row1 = tk.Frame(card, bg=BG_CARD)
        row1.pack(fill=tk.X, pady=2)

        tk.Label(row1, text="IP Listen:", font=FONT_NORMAL, fg=TEXT_SECONDARY, bg=BG_CARD).pack(side=tk.LEFT)
        self.entry_host = tk.Entry(row1, textvariable=self.host_var, width=13, font=FONT_MONO, bg=BG_INPUT, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY)
        self.entry_host.pack(side=tk.LEFT, padx=(4, 12))

        tk.Label(row1, text="Port:", font=FONT_NORMAL, fg=TEXT_SECONDARY, bg=BG_CARD).pack(side=tk.LEFT)
        self.entry_port = tk.Entry(row1, textvariable=self.port_var, width=6, font=FONT_MONO, bg=BG_INPUT, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY)
        self.entry_port.pack(side=tk.LEFT, padx=(4, 12))

        self.btn_server_toggle = tk.Button(
            row1,
            text="▶ BẬT SERVER",
            font=FONT_BOLD,
            bg=COLOR_GREEN,
            fg="#ffffff",
            activebackground="#059669",
            activeforeground="#ffffff",
            bd=0,
            padx=10,
            pady=3,
            command=self.toggle_server,
        )
        self.btn_server_toggle.pack(side=tk.RIGHT)

        row2 = tk.Frame(card, bg=BG_CARD)
        row2.pack(fill=tk.X, pady=(4, 0))

        self.lbl_server_badge = tk.Label(
            row2,
            text="● SERVER: ĐÃ DỪNG",
            font=FONT_SMALL,
            fg=TEXT_MUTED,
            bg=BG_INPUT,
            padx=8,
            pady=2,
            bd=1,
            relief=tk.SOLID,
        )
        self.lbl_server_badge.pack(side=tk.LEFT)

        self.lbl_clients_badge = tk.Label(
            row2,
            text="Clients: 0",
            font=FONT_SMALL,
            fg=TEXT_SECONDARY,
            bg=BG_CARD,
        )
        self.lbl_clients_badge.pack(side=tk.LEFT, padx=10)

    def _build_status_card(self, parent: tk.Widget) -> None:
        """Khối hiển thị trạng thái Robot và Đèn tháp tín hiệu."""
        card = tk.LabelFrame(parent, text=" ⚡ Trạng thái Hoạt động & Đèn Tháp ", font=FONT_HEADER, bg=BG_CARD, fg=TEXT_PRIMARY, bd=1, padx=8, pady=6)
        card.pack(fill=tk.X, pady=(0, 6))

        frame = tk.Frame(card, bg=BG_CARD)
        frame.pack(fill=tk.BOTH, expand=True)

        # Cột trái trong card: Huy hiệu trạng thái
        left_box = tk.Frame(frame, bg=BG_CARD)
        left_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        tk.Label(left_box, text="Trạng thái Robot:", font=FONT_NORMAL, fg=TEXT_SECONDARY, bg=BG_CARD).pack(anchor="w")

        self.lbl_robot_status = tk.Label(
            left_box,
            text="READY",
            font=FONT_LARGE_STATUS,
            fg=COLOR_GREEN,
            bg=BG_INPUT,
            padx=12,
            pady=8,
            bd=1,
            relief=tk.SOLID,
        )
        self.lbl_robot_status.pack(fill=tk.X, pady=6)

        self.lbl_status_desc = tk.Label(
            left_box,
            text="Robot rảnh rỗi, an toàn. Sẵn sàng nhận lệnh MOV/HOME.",
            font=FONT_SMALL,
            fg=TEXT_SECONDARY,
            bg=BG_CARD,
            wraplength=280,
            justify=tk.LEFT,
        )
        self.lbl_status_desc.pack(anchor="w")

        # Cột phải trong card: Đèn tháp
        self.tower_widget = TowerLightWidget(frame)
        self.tower_widget.pack(side=tk.RIGHT, padx=4)

    def _build_pose_card(self, parent: tk.Widget) -> None:
        """Khối hiển thị tọa độ 6-DOF hiện tại."""
        card = tk.LabelFrame(parent, text=" 📍 Tọa độ 6-DOF Hiện tại (End-Effector) ", font=FONT_HEADER, bg=BG_CARD, fg=TEXT_PRIMARY, bd=1, padx=8, pady=6)
        card.pack(fill=tk.X, pady=(0, 6))

        self.pose_widget = PoseCardWidget(card)
        self.pose_widget.pack(fill=tk.X)
        self.pose_widget.update_pose(self.robot_state.pose)

    def _build_hardware_controls_card(self, parent: tk.Widget) -> None:
        """Khối điều khiển phần cứng PLC (E-Stop, Start, Stop, Reset, Bơm lỗi)."""
        card = tk.LabelFrame(parent, text=" 🎛️ Giả lập Phần cứng & Nút bấm Tủ điện ", font=FONT_HEADER, bg=BG_CARD, fg=TEXT_PRIMARY, bd=1, padx=8, pady=6)
        card.pack(fill=tk.X, pady=(0, 6))

        # Cài đặt thời gian trễ di chuyển
        delay_row = tk.Frame(card, bg=BG_CARD)
        delay_row.pack(fill=tk.X, pady=(0, 6))

        tk.Label(delay_row, text="Thời gian di chuyển (giây):", font=FONT_NORMAL, fg=TEXT_SECONDARY, bg=BG_CARD).pack(side=tk.LEFT)
        delay_spin = ttk.Spinbox(
            delay_row,
            from_=0.1,
            to=10.0,
            increment=0.5,
            textvariable=self.delay_var,
            width=5,
            font=FONT_MONO,
            command=self._on_delay_change,
        )
        delay_spin.pack(side=tk.LEFT, padx=6)
        delay_spin.bind("<Return>", lambda e: self._on_delay_change())

        # Hàng nút bấm vật lý tủ điện
        btn_row = tk.Frame(card, bg=BG_CARD)
        btn_row.pack(fill=tk.X, pady=4)

        # Nút E-STOP nổi bật
        self.btn_estop = tk.Button(
            btn_row,
            text="🛑 E-STOP",
            font=FONT_BOLD,
            bg=COLOR_RED,
            fg="#ffffff",
            activebackground="#b91c1c",
            activeforeground="#ffffff",
            bd=0,
            padx=10,
            pady=4,
            command=self.trigger_estop,
        )
        self.btn_estop.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_start = tk.Button(
            btn_row,
            text="▶ START",
            font=FONT_NORMAL,
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            bd=0,
            padx=8,
            pady=4,
            command=self.trigger_start,
        )
        self.btn_start.pack(side=tk.LEFT, padx=3)

        self.btn_stop = tk.Button(
            btn_row,
            text="⏹ STOP",
            font=FONT_NORMAL,
            bg="#4b5563",
            fg="#ffffff",
            activebackground="#374151",
            activeforeground="#ffffff",
            bd=0,
            padx=8,
            pady=4,
            command=self.trigger_stop,
        )
        self.btn_stop.pack(side=tk.LEFT, padx=3)

        self.btn_reset = tk.Button(
            btn_row,
            text="🔄 RESET",
            font=FONT_NORMAL,
            bg="#059669",
            fg="#ffffff",
            activebackground="#047857",
            activeforeground="#ffffff",
            bd=0,
            padx=8,
            pady=4,
            command=self.trigger_reset,
        )
        self.btn_reset.pack(side=tk.LEFT, padx=3)

        # Bơm mã lỗi giả lập
        err_row = tk.Frame(card, bg=BG_CARD)
        err_row.pack(fill=tk.X, pady=(6, 0))

        tk.Label(err_row, text="Bơm lỗi:", font=FONT_SMALL, fg=TEXT_SECONDARY, bg=BG_CARD).pack(side=tk.LEFT)

        err_combo = ttk.Combobox(
            err_row,
            textvariable=self.error_select_var,
            values=list(ERROR_CODES.keys()),
            width=6,
            state="readonly",
        )
        err_combo.pack(side=tk.LEFT, padx=4)

        btn_inject_err = tk.Button(
            err_row,
            text="⚠ Kích hoạt lỗi",
            font=FONT_SMALL,
            bg="#b45309",
            fg="#ffffff",
            activebackground="#92400e",
            activeforeground="#ffffff",
            bd=0,
            padx=6,
            pady=2,
            command=self.trigger_inject_error,
        )
        btn_inject_err.pack(side=tk.LEFT, padx=4)

    def _build_test_client_card(self, parent: tk.Widget) -> None:
        """Khối Test Client giả lập lệnh từ Vision PC gửi tới PLC."""
        card = tk.LabelFrame(parent, text=" 🧪 Test Client (Gửi thử Lệnh Vision) ", font=FONT_HEADER, bg=BG_CARD, fg=COLOR_CYAN, bd=1, padx=8, pady=6)
        card.pack(fill=tk.X, pady=(0, 4))

        # Trạng thái kết nối Test Client
        row_status = tk.Frame(card, bg=BG_CARD)
        row_status.pack(fill=tk.X, pady=(0, 4))

        self.lbl_test_status = tk.Label(
            row_status,
            textvariable=self.test_status_var,
            font=FONT_SMALL,
            fg=TEXT_SECONDARY,
            bg=BG_CARD,
        )
        self.lbl_test_status.pack(side=tk.LEFT)

        self.btn_test_conn = tk.Button(
            row_status,
            text="Kết nối Test",
            font=FONT_SMALL,
            bg="#374151",
            fg=TEXT_PRIMARY,
            activebackground="#4b5563",
            bd=0,
            padx=6,
            pady=1,
            command=self.toggle_test_client_connection,
        )
        self.btn_test_conn.pack(side=tk.RIGHT)

        # Hàng nhập 6 tọa độ
        grid_pose = tk.Frame(card, bg=BG_CARD)
        grid_pose.pack(fill=tk.X, pady=4)

        coords = [
            ("X:", self.test_x_var, 0, 0),
            ("Y:", self.test_y_var, 0, 2),
            ("Z:", self.test_z_var, 0, 4),
            ("Rx:", self.test_rx_var, 1, 0),
            ("Ry:", self.test_ry_var, 1, 2),
            ("Rz:", self.test_rz_var, 1, 4),
        ]
        for lbl_text, var, r, c in coords:
            tk.Label(grid_pose, text=lbl_text, font=FONT_SMALL, fg=TEXT_SECONDARY, bg=BG_CARD).grid(row=r, column=c, sticky="e", padx=(2, 1))
            entry = tk.Entry(grid_pose, textvariable=var, width=7, font=FONT_MONO, bg=BG_INPUT, fg=TEXT_PRIMARY)
            entry.grid(row=r, column=c+1, padx=(0, 4), pady=2)

        # Các nút gửi lệnh mẫu
        btn_grid = tk.Frame(card, bg=BG_CARD)
        btn_grid.pack(fill=tk.X, pady=(4, 2))

        btn_send_mov = tk.Button(
            btn_grid,
            text="Gửi MOV",
            font=FONT_BOLD,
            bg=COLOR_BLUE,
            fg="#ffffff",
            activebackground="#2563eb",
            bd=0,
            padx=8,
            pady=2,
            command=self.test_send_mov,
        )
        btn_send_mov.pack(side=tk.LEFT, padx=(0, 4))

        for text_lbl, cmd_func in [
            ("HOME", self.test_send_home),
            ("GET_STATUS", self.test_send_get_status),
            ("STOP", self.test_send_stop),
            ("RESET", self.test_send_reset),
        ]:
            b = tk.Button(
                btn_grid,
                text=text_lbl,
                font=FONT_SMALL,
                bg="#374151",
                fg=TEXT_PRIMARY,
                activebackground="#4b5563",
                bd=0,
                padx=6,
                pady=2,
                command=cmd_func,
            )
            b.pack(side=tk.LEFT, padx=2)

    def _build_history_and_logs(self, parent: tk.Widget) -> None:
        """Cột phải: Bảng lịch sử lệnh nhận, bảng lịch sử lệnh gửi, và activity log."""
        paned = tk.PanedWindow(parent, orient=tk.VERTICAL, bg=BG_MAIN, bd=0, sashwidth=4, sashrelief=tk.FLAT)
        paned.pack(fill=tk.BOTH, expand=True)

        # 1. Bảng lệnh nhận và gửi (xếp ngang trong tab hoặc paned con)
        top_split = tk.Frame(paned, bg=BG_MAIN)
        paned.add(top_split, minsize=220)

        # Cột trái top_split: Lệnh Nhận (PC -> PLC)
        left_tbl_frame = tk.Frame(top_split, bg=BG_CARD)
        left_tbl_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 3))

        recv_cols = [
            ("time", "Thời gian", 85),
            ("client", "IP Client", 115),
            ("cmd", "Lệnh Nhận Được", 180),
        ]
        self.recv_table = CommandHistoryTable(left_tbl_frame, "📥 Danh sách Lệnh Nhận (PC -> PLC)", recv_cols)
        self.recv_table.pack(fill=tk.BOTH, expand=True)

        # Cột phải top_split: Lệnh Gửi (PLC -> PC)
        right_tbl_frame = tk.Frame(top_split, bg=BG_CARD)
        right_tbl_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(3, 0))

        sent_cols = [
            ("time", "Thời gian", 85),
            ("client", "Gửi tới IP", 115),
            ("resp", "Phản hồi Gửi đi", 180),
        ]
        self.sent_table = CommandHistoryTable(right_tbl_frame, "📤 Danh sách Lệnh Gửi (PLC -> PC)", sent_cols)
        self.sent_table.pack(fill=tk.BOTH, expand=True)

        # 2. Activity Log chi tiết bên dưới
        log_frame = tk.Frame(paned, bg=BG_CARD)
        paned.add(log_frame, minsize=260)

        self.log_viewer = LogViewerWidget(log_frame)
        self.log_viewer.pack(fill=tk.BOTH, expand=True)

    # ==========================
    # QUẢN LÝ SỰ KIỆN & CẬP NHẬT GIAO DIỆN
    # ==========================

    def _poll_events(self) -> None:
        """Rút cạn hàng đợi sự kiện từ các luồng mạng và cập nhật UI an toàn."""
        try:
            while not self.event_queue.empty():
                evt = self.event_queue.get_nowait()
                evt_type = evt.get("type")

                if evt_type == "LOG":
                    self.log_viewer.append_log(evt["timestamp"], evt["level"], evt["message"])

                elif evt_type == "CMD_RECV":
                    self.recv_table.add_row([evt["timestamp"], evt["client"], evt["command"]])

                elif evt_type == "CMD_SENT":
                    self.sent_table.add_row([evt["timestamp"], evt["client"], evt["response"]])

                elif evt_type == "SERVER_STATUS":
                    self._update_server_ui(evt)

                elif evt_type == "STATE_CHANGE":
                    self._render_state(evt["snapshot"])

        except Exception as e:
            print("Lỗi trong poll events:", e)

        # Tiếp tục chu kỳ lặp lại sau 50ms
        self.root.after(50, self._poll_events)

    def _on_state_change(self, robot_state: RobotState) -> None:
        """Callback từ RobotState (chạy trong luồng worker), đẩy snapshot vào queue."""
        snapshot = robot_state.get_snapshot()
        self.event_queue.put({
            "type": "STATE_CHANGE",
            "snapshot": snapshot,
        })

    def _render_state(self, snap: dict) -> None:
        """Hiển thị dữ liệu trạng thái và đèn tháp trên luồng chính UI."""
        st = snap["state"]
        code = snap.get("error_code")
        status_str = snap.get("status_str", "READY")

        if st == StateEnum.READY.value:
            self.lbl_robot_status.config(text="READY", fg=COLOR_GREEN)
            self.lbl_status_desc.config(text="Robot rảnh rỗi, an toàn. Sẵn sàng nhận lệnh MOV/HOME.")
        elif st == StateEnum.BUSY_MOV.value:
            self.lbl_robot_status.config(text="BUSY (MOV)", fg=COLOR_YELLOW)
            self.lbl_status_desc.config(text=f"Đang di chuyển tới tọa độ đích... Chờ {self.delay_var.get():.1f}s")
        elif st == StateEnum.BUSY_HOME.value:
            self.lbl_robot_status.config(text="BUSY (HOME)", fg=COLOR_YELLOW)
            self.lbl_status_desc.config(text=f"Đang di chuyển về vị trí gốc (Home)... Chờ {self.delay_var.get():.1f}s")
        elif st == StateEnum.STOPPED.value:
            self.lbl_robot_status.config(text="STOPPED", fg="#f97316")
            self.lbl_status_desc.config(text="Đã dừng chuyển động hoàn toàn (Nút STOP / Khóa mềm).")
        elif st == StateEnum.ERROR.value:
            self.lbl_robot_status.config(text=f"ERROR: {code or 'E01'}", fg=COLOR_RED)
            desc = ERROR_CODES.get(code or "E01", "Sự cố không xác định")
            self.lbl_status_desc.config(text=f"SỰ CỐ: {desc}. Cần RESET để phục hồi.")

        # Cập nhật đèn tháp
        self.tower_widget.set_lights(
            green=snap.get("tower_green", True),
            yellow=snap.get("tower_yellow", False),
            red=snap.get("tower_red", False),
            buzzer=snap.get("buzzer", False),
        )

        # Cập nhật tọa độ
        self.pose_widget.update_pose(snap.get("pose", {}))

    def _update_server_ui(self, evt: dict) -> None:
        """Cập nhật huy hiệu trạng thái của TCP Server."""
        running = evt.get("running", False)
        host = evt.get("host", "")
        port = evt.get("port", "")
        client_count = evt.get("client_count", 0)

        if running:
            self.lbl_server_badge.config(
                text=f"● SERVER: ĐANG CHẠY ({host}:{port})",
                fg=COLOR_GREEN,
            )
            self.btn_server_toggle.config(
                text="⏹ DỪNG SERVER",
                bg="#b91c1c",
                activebackground="#991b1b",
            )
            self.entry_host.config(state="disabled")
            self.entry_port.config(state="disabled")
        else:
            self.lbl_server_badge.config(
                text="● SERVER: ĐÃ DỪNG",
                fg=TEXT_MUTED,
            )
            self.btn_server_toggle.config(
                text="▶ BẬT SERVER",
                bg=COLOR_GREEN,
                activebackground="#059669",
            )
            self.entry_host.config(state="normal")
            self.entry_port.config(state="normal")

        self.lbl_clients_badge.config(text=f"Clients: {client_count}")

    # ==========================
    # CÁC HÀNH ĐỘNG ĐIỀU KHIỂN
    # ==========================

    def toggle_server(self) -> None:
        """Bật hoặc tắt TCP Server."""
        if self.tcp_server.is_running():
            self.tcp_server.stop()
        else:
            host = self.host_var.get().strip()
            try:
                port = int(self.port_var.get().strip())
            except ValueError:
                messagebox.showerror("Lỗi Port", "Port kết nối phải là số nguyên (1 - 65535).")
                return

            success, msg = self.tcp_server.start(host, port)
            if not success:
                messagebox.showwarning("Lỗi mở Server", msg)

    def _on_delay_change(self) -> None:
        try:
            val = float(self.delay_var.get())
            self.motion_sim.set_delay(val)
        except ValueError:
            pass

    def trigger_estop(self) -> None:
        """Kích hoạt dừng khẩn cấp E-STOP."""
        self.motion_sim.cancel_motion()
        self.robot_state.set_error("E02")
        self.tcp_server.broadcast_message("ERROR,E02")
        self.log_viewer.append_log(
            self._current_time_str(),
            "ERROR",
            "🚨 NÚT DỪNG KHẨN CẤP E-STOP ĐÃ ĐƯỢC NHẤN! Ngắt toàn bộ truyền động Servo.",
        )

    def trigger_start(self) -> None:
        """Nút Start trên tủ điện: Xóa dừng và sẵn sàng."""
        if self.robot_state.state in (StateEnum.STOPPED, StateEnum.READY):
            self.robot_state.reset()
            self.log_viewer.append_log(self._current_time_str(), "INFO", "Nút START: Robot ở trạng thái READY.")

    def trigger_stop(self) -> None:
        """Nút Stop mềm."""
        self.motion_sim.cancel_motion()
        self.robot_state.set_stopped()
        self.tcp_server.broadcast_message("STOPPED")
        self.log_viewer.append_log(self._current_time_str(), "WARN", "Nút STOP tủ điện: Dừng chuyển động robot.")

    def trigger_reset(self) -> None:
        """Nút Reset tủ điện."""
        self.motion_sim.cancel_motion()
        self.robot_state.reset()
        self.tcp_server.broadcast_message("READY")
        self.log_viewer.append_log(self._current_time_str(), "SUCCESS", "Nút RESET: Đã xóa lỗi. Robot sẵn sàng.")

    def trigger_inject_error(self) -> None:
        """Bơm lỗi tùy chọn để kiểm tra phản ứng của hệ thống."""
        code = self.error_select_var.get().strip()
        desc = ERROR_CODES.get(code, "Lỗi không xác định")
        self.motion_sim.cancel_motion()
        self.robot_state.set_error(code)
        self.tcp_server.broadcast_message(f"ERROR,{code}")
        self.log_viewer.append_log(
            self._current_time_str(),
            "ERROR",
            f"Kích hoạt mô phỏng lỗi phần cứng: {desc}",
        )

    # ==========================
    # CÁC HÀNH ĐỘNG CỦA TEST CLIENT
    # ==========================

    def toggle_test_client_connection(self) -> None:
        if self.test_client.is_connected():
            self.test_client.disconnect()
            self.test_status_var.set("Client: Đã ngắt kết nối")
            self.btn_test_conn.config(text="Kết nối Test")
        else:
            host = self.host_var.get().strip()
            try:
                port = int(self.port_var.get().strip())
            except ValueError:
                port = DEFAULT_PORT

            ok, msg = self.test_client.connect(host, port)
            if ok:
                self.test_status_var.set(f"Client: Đã kết nối ({host}:{port})")
                self.btn_test_conn.config(text="Ngắt kết nối")
            else:
                self.test_status_var.set("Client: Lỗi kết nối")
                messagebox.showerror("Test Client", msg)

    def _ensure_test_connected(self) -> bool:
        if not self.test_client.is_connected():
            self.toggle_test_client_connection()
        return self.test_client.is_connected()

    def test_send_mov(self) -> None:
        if not self._ensure_test_connected():
            return
        try:
            x = float(self.test_x_var.get())
            y = float(self.test_y_var.get())
            z = float(self.test_z_var.get())
            rx = float(self.test_rx_var.get())
            ry = float(self.test_ry_var.get())
            rz = float(self.test_rz_var.get())
        except ValueError:
            messagebox.showerror("Lỗi tọa độ", "Các giá trị tọa độ thử nghiệm phải là số thực.")
            return

        cmd = f"MOV,{x:.2f},{y:.2f},{z:.2f},{rx:.2f},{ry:.2f},{rz:.2f}"
        self.test_client.send_command(cmd)

    def test_send_home(self) -> None:
        if self._ensure_test_connected():
            self.test_client.send_command("HOME")

    def test_send_get_status(self) -> None:
        if self._ensure_test_connected():
            self.test_client.send_command("GET_STATUS")

    def test_send_stop(self) -> None:
        if self._ensure_test_connected():
            self.test_client.send_command("STOP")

    def test_send_reset(self) -> None:
        if self._ensure_test_connected():
            self.test_client.send_command("RESET")

    def _on_test_client_response(self, resp: str) -> None:
        """Callback khi test client nhận được phản hồi từ server."""
        self.test_status_var.set(f"Client nhận: {resp}")

    def _current_time_str(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def on_close(self) -> None:
        """Dọn dẹp tài nguyên khi người dùng tắt ứng dụng."""
        if self.test_client:
            self.test_client.disconnect()
        if self.tcp_server:
            self.tcp_server.stop()
        self.root.destroy()
