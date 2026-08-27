@echo off
chcp 65001 > nul

echo ==========================================
echo    長生劫古典典故字庫一鍵同步系統
echo ==========================================
echo 正在讀取小說工作區典故字庫並同步至網站...
echo.

node scripts/sync-classical-dict.js

if %errorlevel% neq 0 (
    echo.
    echo ❌ 同步過程中發生錯誤，請檢查上方日誌。
    echo.
    pause
    exit /b 1
)

echo.
echo 正在執行 Astro 靜態頁面建置驗證...
npm run build

if %errorlevel% neq 0 (
    echo.
    echo ❌ 建置驗證失敗，請檢查資料結構。
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ [Success] 古典典故字庫同步與建置完成！
echo.
pause
