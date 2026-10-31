@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True
set PYTHONIOENCODING=utf-8
echo Generating test images and running OCR ^& Orientation Benchmark...
".\.venv\Scripts\python.exe" generate_test_images.py
".\.venv\Scripts\python.exe" evaluate_benchmark.py
pause
