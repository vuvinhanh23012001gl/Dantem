import numpy as np
import pytest
from app.engines.model_AI.model_yolo_obb import (
    normalize_obb,
    inspect_stamp_alignment,
)


def test_normalize_obb():
    # Trường hợp 1: w >= h, góc đã chuẩn
    x, y, w, h, theta = normalize_obb(100, 100, 50, 30, 0.1)
    assert w == 50
    assert h == 30
    assert -np.pi / 2 <= theta < np.pi / 2

    # Trường hợp 2: w < h, phải hoán đổi và xoay 90 độ
    x, y, w, h, theta = normalize_obb(100, 100, 30, 50, 0.0)
    assert w == 50
    assert h == 30
    assert -np.pi / 2 <= theta < np.pi / 2


def test_inspect_stamp_alignment_perfect():
    # Khung kích thước 100x60 tại tâm (200, 200), góc 0
    frame_obb = (200.0, 200.0, 100.0, 60.0, 0.0)
    # Tem kích thước 40x20 tại cùng tâm (200, 200), góc 0
    stamp_obb = (200.0, 200.0, 40.0, 20.0, 0.0)
    # 4 đỉnh của tem: từ (180, 190) đến (220, 210)
    stamp_corners = np.array([
        [180.0, 190.0],
        [220.0, 190.0],
        [220.0, 210.0],
        [180.0, 210.0],
    ], dtype=np.float32)

    tolerances = {
        "max_du": 10.0,
        "max_dv": 10.0,
        "max_deg": 3.0,
        "margin": 5.0,
    }

    result = inspect_stamp_alignment(frame_obb, stamp_obb, stamp_corners, tolerances)
    assert result["status"] == "OK"
    assert result["metrics"]["du"] == 0.0
    assert result["metrics"]["dv"] == 0.0
    assert result["metrics"]["delta_angle_deg"] == 0.0
    assert result["metrics"]["is_contained"] is True


def test_inspect_stamp_alignment_exceed_du():
    frame_obb = (200.0, 200.0, 100.0, 60.0, 0.0)
    # Lệch ngang dx = 15 px (vượt ngưỡng max_du = 10 px)
    stamp_obb = (215.0, 200.0, 40.0, 20.0, 0.0)
    stamp_corners = np.array([
        [195.0, 190.0],
        [235.0, 190.0],
        [235.0, 210.0],
        [195.0, 210.0],
    ], dtype=np.float32)

    tolerances = {
        "max_du": 10.0,
        "max_dv": 10.0,
        "max_deg": 3.0,
        "margin": 5.0,
    }

    result = inspect_stamp_alignment(frame_obb, stamp_obb, stamp_corners, tolerances)
    assert result["status"] == "NG"
    assert result["details"]["pass_position_u"] is False
    assert result["details"]["pass_position_v"] is True


def test_inspect_stamp_alignment_exceed_angle():
    frame_obb = (200.0, 200.0, 100.0, 60.0, 0.0)
    # Lệch góc 5 độ (vượt ngưỡng max_deg = 3.0 độ)
    stamp_obb = (200.0, 200.0, 40.0, 20.0, np.radians(5.0))
    stamp_corners = np.array([
        [180.0, 190.0],
        [220.0, 190.0],
        [220.0, 210.0],
        [180.0, 210.0],
    ], dtype=np.float32)

    tolerances = {
        "max_du": 10.0,
        "max_dv": 10.0,
        "max_deg": 3.0,
        "margin": 5.0,
    }

    result = inspect_stamp_alignment(frame_obb, stamp_obb, stamp_corners, tolerances)
    assert result["status"] == "NG"
    assert result["details"]["pass_rotation"] is False


def test_inspect_stamp_alignment_rotated_frame():
    # Khung xoay 45 độ: theta = pi/4
    # Khi khung xoay 45 độ, độ lệch ngang thực tế du dọc theo trục dài của khung
    theta_f = np.pi / 4.0
    frame_obb = (200.0, 200.0, 100.0, 60.0, theta_f)

    # Dịch chuyển 10*sqrt(2) px theo hướng 45 độ (tức dx = 10, dy = 10)
    # Trong hệ tọa độ cục bộ của khung: du = 10*cos(45) + 10*sin(45) = 14.14, dv = 0
    stamp_obb = (210.0, 210.0, 40.0, 20.0, theta_f)
    stamp_corners = np.array([
        [190.0, 200.0],
        [230.0, 200.0],
        [230.0, 220.0],
        [190.0, 220.0],
    ], dtype=np.float32)

    tolerances = {
        "max_du": 10.0,  # du = 14.14 > 10 -> NG
        "max_dv": 10.0,
        "max_deg": 3.0,
        "margin": 5.0,
    }

    result = inspect_stamp_alignment(frame_obb, stamp_obb, stamp_corners, tolerances)
    assert result["status"] == "NG"
    assert result["metrics"]["du"] == pytest.approx(14.14, abs=0.1)
    assert result["metrics"]["dv"] == pytest.approx(0.0, abs=0.1)
    assert result["details"]["pass_position_u"] is False
    assert result["details"]["pass_position_v"] is True


def test_inspect_stamp_alignment_containment_violation():
    frame_obb = (200.0, 200.0, 100.0, 60.0, 0.0)
    # Tem dịch sang sát biên phải: x=240, đỉnh xEnd=260 (vượt quá half_w - margin = 50 - 5 = 45 -> x=245)
    stamp_obb = (235.0, 200.0, 40.0, 20.0, 0.0)
    stamp_corners = np.array([
        [215.0, 190.0],
        [255.0, 190.0],  # 255 - 200 = 55 > 45 -> chạm viền/tràn mép
        [255.0, 210.0],
        [215.0, 210.0],
    ], dtype=np.float32)

    tolerances = {
        "max_du": 50.0,
        "max_dv": 50.0,
        "max_deg": 5.0,
        "margin": 5.0,
    }

    result = inspect_stamp_alignment(frame_obb, stamp_obb, stamp_corners, tolerances)
    assert result["status"] == "NG"
    assert result["metrics"]["is_contained"] is False
    assert result["details"]["pass_containment"] is False
