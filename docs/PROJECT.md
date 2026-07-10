# Project: 唐門山莊 Astro 專案優化與工作流預檢防禦

## Architecture & Data Flow

```
+-------------------------------------------------------------+
|                                                             |
|                外部小說目錄 (External novels)                |
|                                                             |
+------------------------------+------------------------------+
                               |
                               | R2: scripts/import-novel.js (一鍵匯入.bat)
                               v
                     [ 讀取未登記 Markdown ]
                               |
                               v
                     [ 互動式詢問與消毒 ]
                               |
                               +-----------------------+
                               |                       |
                               v                       v
                    [ sync-config.json ]      [ 首次單向同步 ]
                                                       |
                                                       v
                                            [ src/content/novels/ ]
                                                       |
                                                       v
                                            [ Astro Build (83 頁) ]
```

- **全域儲存配置 (R1)**：將 `keystatic.config.ts` 的 `storage.kind` 切換為 `'github'`。
- **文章匯入與同步 (R2, R3)**：
  - 新增 `scripts/import-novel.js`：掃描外部小說目錄、解析並更新 `sync-config.json`，隨後自動執行單向同步。
  - 新增 `一鍵匯入.bat`：啟動 `import-novel.js`。
  - 優化 `scripts/sync-novels.js`：修正掃描邏輯，遇未登記文章僅印出黃色警告日誌，不中斷同步流程。
- **自動 Git 防禦拉取 (R4)**：
  - 修改 `開啟編輯器.bat` 與 `一鍵同步.bat`：前置執行 `git pull --rebase`，防範分支衝突。

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: Keystatic 儲存配置變更 | 修改 keystatic.config.ts 配置儲存模式為 github | None | DONE |
| 2 | M2: 同步警告機制優化 | 修改 scripts/sync-novels.js，將未登記中斷改為黃色警告 | None | DONE |
| 3 | M3: 互動式文章匯入系統 | 實作 scripts/import-novel.js 與 一鍵匯入.bat | M2 | DONE |
| 4 | M4: Git 自動拉取防禦 | 修改 開啟編輯器.bat 與 一鍵同步.bat，前置執行 git pull --rebase | None | DONE |
| 5 | M5: E2E 測試與驗收 | 執行完整 E2E 測試用例，並通過 Forensic Auditor 審計 | M1, M2, M3, M4 | IN_PROGRESS |

## Interface Contracts & Configurations

### sync-config.json schema
```json
{
  "novels": {
    "filename.md": {
      "title": "文章標題",
      "slug": "url-friendly-slug",
      "category": "novels"
    }
  }
}
```

### import-novel.js cli
- **Inputs**: 外部小說目錄檔案、使用者互動輸入（序號、標題、別名、分類）
- **Outputs**: 更新 `sync-config.json`，並觸發同步將 Markdown 寫入 `src/content/<category>/`，自動帶入 frontmatter (包括 name、slug 等必填欄位)。

## Code Layout
- `keystatic.config.ts` — Keystatic 設定檔
- `sync-config.json` — 同步對照配置表
- `scripts/sync-novels.js` — 小說雙向同步與備份腳本
- `scripts/import-novel.js` — 互動式匯入腳本 (New)
- `src/content/` — Astro Content Collections 目錄
- `開啟編輯器.bat` — 啟動 Keystatic 編輯器批次檔
- `一鍵同步.bat` — 小說同步批次檔
- `一鍵匯入.bat` — 小說匯入批次檔 (New)
