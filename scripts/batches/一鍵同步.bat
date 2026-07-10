@echo off
chcp 65001 > nul

echo ==========================================
echo    Changshengjie Novel Sync System
echo ==========================================
echo [Git] 正在拉取線上最新編輯 (git pull --rebase)...
git pull --rebase
if %errorlevel% neq 0 (
    echo.
    echo ❌ [Git 衝突] 偵測到與線上代碼衝突！
    echo 正在還原本地狀態 (git rebase --abort)...
    git rebase --abort
    echo.
    echo 💡 請手動解決 Git 衝突後，再重新執行此腳本。
    echo.
    pause
    exit /b 1
)
echo [Git] 拉取成功，本地已是最新狀態.
echo.

echo.
echo [Success] 同步線上最新編輯成功！
echo.
pause
