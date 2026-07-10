@echo off
chcp 65001 > nul

echo ====================================================
echo            唐 門 山 莊 · 外 部 檔 案 匯 入
echo ====================================================
echo.

node scripts/import-novels-cli.js
if %errorlevel% neq 0 (
    echo.
    echo ❌ [錯誤] 匯入腳本執行失敗！
    echo.
    pause
    exit /b 1
)

echo.
echo [成功] 所有文檔已順利處理並匯入專案。
echo.
pause
