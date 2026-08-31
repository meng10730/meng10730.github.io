@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo [INFO] Launching Tangmen Preview Editor...
python scripts/preview_editor_ui.py
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start preview editor.
    pause
    exit /b 1
)

pause
exit /b 0


