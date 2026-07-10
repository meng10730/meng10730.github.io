@echo off
chcp 65001 > nul
title 唐門山莊 網站管理終端

:MENU
cls
echo ====================================================
echo             唐 門 山 莊 網 站 管 理 終 端
echo ====================================================
echo.
echo   [1] 🧪 啟動本地測試 (測試音效與排版)
echo.
echo   [2] 📝 開啟後台編輯 (寫作與修改條目)
echo.
echo   [3] 📥 同步線上編輯 (拉取最新文章)
echo.
echo   [4] 📥 選擇外部匯入 (原生對話框多選與歸檔)
echo.
echo   [5] 🚀 一鍵發布上線 (自動打包並上傳)
echo.
echo   [6] 🛠️  管理自訂類別 (新增、修改、刪除類別)
echo.
echo   [7] ⚙️  網頁進階維護 (環境修復與還原)
echo.
echo   [8] ❌ 退出終端
echo.
echo ====================================================
set /p opt="請輸入選項序號 [1-8]: "

if "%opt%"=="1" goto DEV_TEST
if "%opt%"=="2" goto OPEN_CMS
if "%opt%"=="3" goto SYNC_NOVEL
if "%opt%"=="4" goto IMPORT_NOVEL
if "%opt%"=="5" goto PUBLISH_SITE
if "%opt%"=="6" goto MANAGE_COLLECTION
if "%opt%"=="7" goto ADVANCED_MAINTAIN
if "%opt%"=="8" goto EXIT_BATCH

echo ❌ 選項無效，請重新選擇！
pause
goto MENU

:DEV_TEST
echo.
echo ----------------------------------------------------
echo   正在拉取線上最新編輯 (git pull --rebase)...
echo ----------------------------------------------------
git pull --rebase
if %errorlevel% neq 0 (
    echo.
    echo ❌ [Git 衝突] 偵測到與線上代碼衝突！已自動取消。
    echo 💡 請在主選單「進階維護」中修復，或手動排解。
    pause
    goto MENU
)
echo [Git] 拉取成功！正在啟動本地測試網頁 (http://localhost:4321)...
echo 💡 提示：測試完畢後，請在此視窗按下 Ctrl+C 鍵並輸入 Y 來關閉服務。
start http://localhost:4321
npm run dev
pause
goto MENU

:OPEN_CMS
echo.
echo ----------------------------------------------------
echo   正在開啟 Keystatic 文章編輯器...
echo ----------------------------------------------------
call 開啟編輯器.bat
goto MENU

:SYNC_NOVEL
echo.
echo ----------------------------------------------------
echo   正在同步線上編輯 (拉取 GitHub 最新狀態)...
echo ----------------------------------------------------
call 一鍵同步.bat
goto MENU

:IMPORT_NOVEL
echo.
echo ----------------------------------------------------
echo   正在彈出選擇檔案對話框...
echo ----------------------------------------------------
call 一鍵匯入.bat
goto MENU

:PUBLISH_SITE
echo.
echo ----------------------------------------------------
echo   正在打包建置並發布網站上線...
echo ----------------------------------------------------
call 一鍵發布.bat
goto MENU

:MANAGE_COLLECTION
echo.
echo ----------------------------------------------------
echo   正在載入自訂類別整合維護管理工具...
echo ----------------------------------------------------
node scripts/add-collection-cli.js
goto MENU

:ADVANCED_MAINTAIN
cls
echo ====================================================
echo             網 頁 進 階 維 護 與 環 境 還 原
echo ====================================================
echo.
echo   [1] 還原開發環境 (修復 Keystatic 開發設定)
echo.
echo   [2] 還原歷史備份 (復原舊版小說內容)
echo.
echo   [3] 返回主選單
echo.
echo ====================================================
set /p subopt="請輸入選項序號 [1-3]: "

if "%subopt%"=="1" goto FIX_DEV_ENV
if "%subopt%"=="2" goto RESTORE_BACKUP
if "%subopt%"=="3" goto MENU

echo ❌ 選項無效，請重新選擇！
pause
goto ADVANCED_MAINTAIN

:FIX_DEV_ENV
echo.
echo 正在還原 src/pages/keystatic/[...params].astro 檔案...
call 還原開發環境.bat
goto ADVANCED_MAINTAIN

:RESTORE_BACKUP
echo.
echo 正在載入歷史備份還原工具...
call 還原歷史備份.bat
goto ADVANCED_MAINTAIN

:EXIT_BATCH
echo.
echo 唐門山莊 · 祝您寫作愉快，再見！
timeout /t 1 > nul
exit /b 0
