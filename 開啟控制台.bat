@echo off
chcp 65001 > nul

:: Step 1. Sync Schema
node scripts/gui-helper.js --extract
if %errorlevel% neq 0 (
    echo [ERROR] Failed to extract Keystatic config schema.
    pause
    exit /b 1
)

:: Step 2. Launch GUI (Python will auto-install PySide6 if missing)
python scripts/import_gui.py
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start Tangmen Villa Manager GUI.
    pause
    exit /b 1
)

exit /b 0
