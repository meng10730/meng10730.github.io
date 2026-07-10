@echo off
title Tangmen Shanzhuang Backup Restore Tool
cd /d "%~dp0"

echo ===================================================
echo Starting Tangmen Shanzhuang Backup Restore Tool...
echo ===================================================
node scripts/restore-backup.js

echo.
echo ===================================================
echo Process finished. Press any key to exit.
echo ===================================================
pause
