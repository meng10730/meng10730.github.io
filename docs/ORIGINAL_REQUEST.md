# Original User Request

## Initial Request — 2026-06-25T09:00:33+08:00

為唐門山莊 Astro 網站實作全域的 Keystatic GitHub 編輯模式、本機文章選擇性互動匯入 CLI 工具，以及工作流 Git 自動同步預檢。

Working directory: c:\workspace\個人網站架設
Integrity mode: development

## Requirements

### R1. Keystatic 全域 GitHub 儲存配置 (Global GitHub Mode)
修改 keystatic.config.ts 中配置，將 storage 的 kind 設為 'github'，repo 設為 'meng10730/meng10730.github.io'。確保無論本地開發環境（localhost）還是線上 GitHub Pages，都統一使用 GitHub 帳號 OAuth 授權來編輯 and 寫回文章。

### R2. 互動式文章匯入系統 (Interactive Import Tool)
1. 建立 Node.js 交互式指令列腳本 scripts/import-novel.js 與本機批次檔 一鍵匯入.bat。
2. 掃描外部小說目錄中所有尚未登記在 sync-config.json 中的 Markdown 文章，展示包含序號的選單。
3. 讓莊主輸入序號進行選擇，並依次引導輸入網站文章標題（Title）、網址別名（Slug，預設為檔案檔名但去除敏感字元）、以及所屬分類（如 novels, worldview, characters, factions, guoxue，建議提供預設對應值）。
4. 完成後將配置寫入 sync-config.json，並自動執行首次單向同步（外部 -> 本地），生成 YAML Frontmatter 並在網站 src/content/ 對應目錄中產生檔案。

### R3. 同步警告機制優化 (Non-blocking Warnings)
修改 scripts/sync-novels.js 邏輯。當掃描發現外部工作區有未在對照表登記的新 Markdown 檔案時，在終端機中僅顯示黃色警告日誌提示「有新文章可執行一鍵匯入」，但不再強制中斷執行，允許已登記的文章正常進行雙向同步與備份。

### R4. 啟動與同步的自動 Git 拉取防禦 (Auto Git Pull)
修改 開啟編輯器.bat 與 一鍵同步.bat。在背景執行同步或開啟 CMS 前，前置加入自動執行 git pull --rebase，以自動獲取線上 GitHub 的最新修改，若出現拉取衝突則優雅中斷並引導，以防止本地與線上分支分叉。

## Acceptance Criteria

### Astro 建置與 CMS 配置
- [ ] 執行 npm run build 能正常完成全站 83 個網頁建置（退出代碼 0）。
- [ ] keystatic.config.ts 配置中儲存模式為 'github' 且指向 'meng10730/meng10730.github.io'。

### 文章匯入與同步功能
- [ ] 執行 一鍵匯入.bat 能展示外部目錄中尚未登記的文章清單與序號。
- [ ] 選定檔案並輸入參數後，新文章配置正確追加寫入 sync-config.json。
- [ ] 匯入後能自動觸發同步，在專案中正確寫入 Markdown 並自動賦值 schema 所需必填欄位（例如 title 賦值給 name）。
- [ ] scripts/sync-novels.js 在發現未登記檔案時，僅印出警告，其餘檔案雙向同步與滾動備份（最多 3 次）照常流暢執行。

### 工作流整合與衝突防禦
- [ ] 執行 一鍵同步.bat 或 開啟編輯器.bat 前，能自動在背景先調用 git pull --rebase 獲取線上最新編輯。
