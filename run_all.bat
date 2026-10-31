@echo off
chcp 65001 > nul
title Khoi Dong He Thong: Inspector Carton & PLC Robot Simulator

echo =======================================================================
echo   KHỞI ĐỘNG CÙNG LÚC: WEB APP INSPECTOR CARTON & PLC ROBOT SIMULATOR
echo =======================================================================
echo.

echo [1/2] Đang khởi động PLC Robot Simulator (TCP Socket 127.0.0.1:2000)...
start "PLC Robot Simulator (PROD4)" ".\.venv\Scripts\python.exe" "app_demorobot\run_simulator.py"

echo Chờ 1.5 giây để Server PLC mở cổng...
timeout /t 2 /nobreak > nul

echo [2/2] Đang khởi động Web App Inspector Carton (Cổng 127.0.0.1:8001)...
start "Inspector Carton Web App" ".\.venv\Scripts\python.exe" "run.py"

echo.
echo =======================================================================
echo  ĐÃ MỞ THÀNH CÔNG CẢ 2 PHẦN MỀM TRÊN 2 CỬA SỔ RIÊNG BIỆT!
echo  - PLC Robot Simulator : TCP Server tại 127.0.0.1:2000
echo  - Giao diện Web App   : http://127.0.0.1:8001
echo =======================================================================
echo.
pause
