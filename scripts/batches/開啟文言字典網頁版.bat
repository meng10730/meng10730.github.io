@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title 文言字典網頁版 - 雙軌寫作大師
echo =================================================================
echo        古典文言字典檢索系統 - 網頁版一鍵啟動器 (Astro 整合版)
echo =================================================================
echo 正在後台啟動文言字典 API 服務 (連接本機 SQLite 資料庫)...
start /min "文言字典API" python "%~dp0scripts\dict_server.py"

echo 正在開啟瀏覽器前往字典網頁版 (http://localhost:4321/dictionary)...
start "" "http://localhost:4321/dictionary"

echo 正在啟動個人網站 Astro 開發伺服器...
echo 請保持此視窗開啟以維持網站運作。
echo =================================================================
npm run dev
pause
