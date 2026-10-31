@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True
set PYTHONIOENCODING=utf-8
echo Starting Industrial OCR ^& Orientation Inspector GUI...
".\.venv\Scripts\python.exe" -m app.main
if %ERRORLEVEL% NEQ 0 pause
