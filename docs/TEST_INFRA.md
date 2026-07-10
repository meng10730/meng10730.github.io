# E2E Test Infra: 唐門山莊 Astro 專案優化

## Test Philosophy
- 採用 opaque-box / black-box 的系統集成測試，不依賴 Astro 與 Keystatic 內部私有 API，而以終端輸出、檔案異動、指令 exit code 作為主要判定標準。
- 測試覆蓋四大層級 (Tier 1 - Tier 4)。

## Feature Inventory & Test Coverage

| # | Feature | Target | Tier 1 (Feature) | Tier 2 (Boundary) | Tier 3 (Cross-Feature) | Tier 4 (Workload) |
|---|---------|--------|:----------------:|:-----------------:|:----------------------:|:-----------------:|
| 1 | R1: Keystatic 全域 GitHub 儲存配置 | `keystatic.config.ts` | 驗證 kind 欄位值為 'github' | 驗證 repo 欄位值為 'meng10730/meng10730.github.io' | 與 Astro Build 整合測試 | 本地與線上建置與配置完整性驗證 |
| 2 | R2: 互動式文章匯入系統 | `scripts/import-novel.js` | 驗證匯入功能正常更新 `sync-config.json` | 驗證 Slug 敏感字元去除與重複處理 | 匯入新文章後，驗證自動觸發同步，產生 YAML Frontmatter | 執行完整匯入與同步流程，確保 Astro 順利建置 |
| 3 | R3: 同步警告機制優化 | `scripts/sync-novels.js` | 驗證未登記檔案僅印出黃色警告日誌 | 驗證同步不中斷，已登記檔案順利完成同步與滾動備份 | 與 R2 匯入後同步功能交互驗證 | 完整同步流程與多次雙向同步不遺漏資料 |
| 4 | R4: 啟動與同步的自動 Git 拉取防禦 | 批次檔 (`一鍵同步.bat`, `開啟編輯器.bat`) | 驗證執行前有調用 `git pull --rebase` | 驗證 rebase 衝突時能優雅中斷 | 與同步、編輯器開啟指令整合 | 模擬完整拉取防禦，避免本地與遠端分支分叉 |

## Test Architecture
- **E2E 測試執行指令**：`node scripts/test-e2e.js`
- **測試框架**：獨立 Node.js 輕量測試跑跑器，負責模擬使用者輸入、修改環境變數、執行命令並捕捉 stdout/stderr、驗證檔案結構與 exit code。

### 測試案例統計與門檻
- Tier 1: 5 個基本功能測試案例
- Tier 2: 5 個邊界與錯誤輸入測試案例
- Tier 3: 4 個跨功能組合測試案例
- Tier 4: 2 個真實工作流應用情境測試案例
- **總計最低要求：16 個測試案例**
