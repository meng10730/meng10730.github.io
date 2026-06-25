import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const CONFIG_FILE = path.join(__dirname, '..', 'sync-config.json');

if (!fs.existsSync(CONFIG_FILE)) {
  console.error(`[錯誤] 找不到同步設定檔: ${CONFIG_FILE}`);
  console.error(`請先執行: node scripts/init-sync-config.js`);
  process.exit(1);
}

// 載入設定
const config = JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));

// 輔助函數：標準化內容 (統一換行符為 \n，去除行尾空白，去除首尾空白)
function normalizeContent(str) {
  return str.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n').map(line => line.trimEnd()).join('\n').trim();
}

// 輔助函數：解析本地 Markdown，分離 frontmatter 與 content，過濾警語註解
function parseLocalMarkdown(fileContent) {
  const lines = fileContent.split(/\r?\n/);
  let inFrontmatter = false;
  let frontmatterLines = [];
  let contentLines = [];
  let delimiterCount = 0;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.trim() === '---') {
      delimiterCount++;
      if (delimiterCount === 1) {
        inFrontmatter = true;
        continue;
      } else if (delimiterCount === 2) {
        inFrontmatter = false;
        continue;
      }
    }
    
    if (inFrontmatter) {
      frontmatterLines.push(line);
    } else {
      if (
        line.includes('<!-- 此檔案由同步腳本自動產生') || 
        line.includes('請勿在此直接修改 -->') ||
        line.includes('{/* 此檔案由同步腳本自動產生') ||
        line.includes('請勿在此直接修改 */}')
      ) {
        continue;
      }
      contentLines.push(line);
    }
  }
  
  return {
    frontmatter: frontmatterLines.join('\n'),
    content: contentLines.join('\n').trim()
  };
}

// 輔助函數：反向還原網頁連結至 Obsidian 雙括號格式
function restoreObsidianLinks(content, slugToOriginalName) {
  // 1. 還原失效連結
  let restored = content.replace(/<span class="broken-link"[^>]*>(.*?)<\/span>/g, '[[$1]]');
  
  // 2. 還原有效連結：[別名](/shanzhuang/collection/slug#anchor) -> [[原始名稱#anchor|別名]]
  restored = restored.replace(/\[([^\]]+)\]\(\/shanzhuang\/[^/]+\/([^)#?\s]+)(#[^)#?\s]+)?\)/g, (_match, alias, slug, anchor) => {
    const cleanAnchor = anchor ? anchor : '';
    const lowerSlug = slug.toLowerCase();
    const originalName = slugToOriginalName[lowerSlug] || slug;
    
    if (alias === originalName) {
      return `[[${originalName}${cleanAnchor}]]`;
    } else {
      return `[[${originalName}${cleanAnchor}|${alias}]]`;
    }
  });
  
  return restored;
}

// Check unique titles and slugs to prevent overwrite and link mismatch
const titleMap = new Map();
const slugMap = new Map();

for (const [relPath, mapInfo] of Object.entries(config.mappings)) {
  if (mapInfo.title) {
    if (titleMap.has(mapInfo.title)) {
      const prevPath = titleMap.get(mapInfo.title);
      console.error(`\n[Error] Duplicate title mapping detected: "${mapInfo.title}"`);
      console.error(`  - File 1: ${prevPath}`);
      console.error(`  - File 2: ${relPath}`);
      console.error(`To prevent duplicate backlinks, different files must have unique titles!`);
      process.exit(1);
    }
    titleMap.set(mapInfo.title, relPath);
  }
  if (mapInfo.slug) {
    // Regex validation: allow Chinese characters, alphanumeric, dash, and underscore.
    // Disallow spaces, slashes, backslashes, question marks, hashes, and other URL sensitive chars.
    const slugRegex = /^[a-z0-9-_\u4e00-\u9fa5]+$/i;
    if (!slugRegex.test(mapInfo.slug)) {
      console.error(`\n[Error] Invalid slug format detected: "${mapInfo.slug}"`);
      console.error(`  - File path: ${relPath}`);
      console.error(`  - Allowed characters: Chinese characters, alphanumeric, dash (-), underscore (_)`);
      console.error(`  - Reason: Slugs must not contain spaces, slashes, backslashes, or other URL sensitive characters.`);
      process.exit(1);
    }

    const lowerSlug = mapInfo.slug.toLowerCase();
    if (slugMap.has(lowerSlug)) {
      const prevPath = slugMap.get(lowerSlug);
      console.error(`\n[Error] Duplicate slug mapping detected: "${mapInfo.slug}"`);
      console.error(`  - File 1: ${prevPath}`);
      console.error(`  - File 2: ${relPath}`);
      console.error(`To prevent output overwrite, different files must have unique slugs!`);
      process.exit(1);
    }
    slugMap.set(lowerSlug, relPath);
  }
}

const EXTERNAL_WORKSPACE = config.workspacePath;
const SOURCE_DIR = path.join(EXTERNAL_WORKSPACE, '00_世界觀與劇本', '01_Creative_Source');
const TARGET_BASE_DIR = path.join(__dirname, '..', 'src', 'content');

// 內建忽略清單 (預設忽略系統與暫存檔)
const IGNORE_PATTERNS = [
  /^\..*/,            // 隱藏檔案或資料夾 (如 .git, .obsidian)
  /^~.*/,             // 暫存檔 (如 ~WordTemp)
  /desktop\.ini/i,
  /thumbs\.db/i
];

function shouldIgnore(fileName) {
  return IGNORE_PATTERNS.some(pattern => pattern.test(fileName));
}

// 遞迴取得外部工作區所有 Markdown 檔案的相對路徑
function scanMarkdownFiles(dir, baseDir = dir) {
  let results = [];
  if (!fs.existsSync(dir)) return results;
  
  const list = fs.readdirSync(dir);
  list.forEach(file => {
    if (shouldIgnore(file)) return;
    
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat && stat.isDirectory()) {
      results = results.concat(scanMarkdownFiles(fullPath, baseDir));
    } else if (file.endsWith('.md')) {
      const relativePath = path.relative(baseDir, fullPath).replace(/\\/g, '/');
      results.push(relativePath);
    }
  });
  return results;
}

// 將 JavaScript 物件轉換為 YAML Frontmatter 字串
function toYAML(obj) {
  let lines = ['---'];
  for (const [key, value] of Object.entries(obj)) {
    if (key === 'collection' || key === 'slug') continue; // 這些不用放入 frontmatter
    
    if (Array.isArray(value)) {
      if (value.length === 0) {
        lines.push(`${key}: []`);
      } else {
        lines.push(`${key}:`);
        value.forEach(item => {
          lines.push(`  - ${JSON.stringify(item)}`);
        });
      }
    } else if (value instanceof Date) {
      lines.push(`${key}: ${value.toISOString().split('T')[0]}`);
    } else if (typeof value === 'object' && value !== null) {
      lines.push(`${key}:`);
      for (const [subKey, subValue] of Object.entries(value)) {
        lines.push(`  ${subKey}: ${JSON.stringify(subValue)}`);
      }
    } else {
      lines.push(`${key}: ${JSON.stringify(value)}`);
    }
  }
  lines.push('---');
  return lines.join('\n');
}

function runSync() {
  console.log(`開始同步任務...`);
  console.log(`外部工作區路徑: ${EXTERNAL_WORKSPACE}`);
  console.log(`掃描原始目錄: ${SOURCE_DIR}...`);

  const externalFiles = scanMarkdownFiles(SOURCE_DIR);
  console.log(`本機工作區掃描到 ${externalFiles.length} 個 Markdown 檔案。`);

  // 1. 嚴格檢查：確認是否有檔案未登記在對照表中
  const missingFiles = [];
  externalFiles.forEach(file => {
    if (!config.mappings[file]) {
      missingFiles.push(file);
    }
  });

  if (missingFiles.length > 0) {
    console.warn(`\x1b[33m⚠️  [警告] 偵測到有 ${missingFiles.length} 篇新文章可執行一鍵匯入 (一鍵匯入.bat)：\x1b[0m`);
    missingFiles.forEach(file => {
      console.warn(`\x1b[33m   - ${file}\x1b[0m`);
    });
  } else {
    console.log(`✓ 檔案登記檢查通過！`);
  }

  // 2. 建立標題/檔名對應表，用以解析雙向連結
  const titleToConfig = {};
  const slugToConfig = {};
  const fileToConfig = {};
  const slugToOriginalName = {};

  for (const [relPath, mapInfo] of Object.entries(config.mappings)) {
    const baseNameNoExt = path.basename(relPath, '.md');
    
    fileToConfig[baseNameNoExt] = mapInfo;
    if (mapInfo.title) titleToConfig[mapInfo.title] = mapInfo;
    if (mapInfo.slug) {
      const lowerSlug = mapInfo.slug.toLowerCase();
      slugToConfig[lowerSlug] = mapInfo;
      slugToOriginalName[lowerSlug] = baseNameNoExt;
    }
  }

  // 3. 處理與複製檔案 (雙向同步機制)
  let syncCount = 0;       // 外部 -> 本地 (覆蓋/同步)
  let writeBackCount = 0;  // 本地 -> 外部 (備份/回寫)
  let skipCount = 0;       // 內容無變更 (跳過)

  externalFiles.forEach(file => {
    const mapInfo = config.mappings[file];
    if (!mapInfo) return; // 跳過未登記的檔案，不執行同步

    if (mapInfo.collection === 'characters' && !mapInfo.name && mapInfo.title) {
      mapInfo.name = mapInfo.title;
    }
    const fullSourcePath = path.join(SOURCE_DIR, file);
    const targetDir = path.join(TARGET_BASE_DIR, mapInfo.collection);
    const targetFilePath = path.join(targetDir, `${mapInfo.slug}.md`);

    let externalContent = fs.existsSync(fullSourcePath) ? fs.readFileSync(fullSourcePath, 'utf8') : '';
    let localContent = fs.existsSync(targetFilePath) ? fs.readFileSync(targetFilePath, 'utf8') : '';

    let shouldSyncLocalToExternal = false;
    let shouldSyncExternalToLocal = false;

    if (localContent && externalContent) {
      // 兩邊都存在，做正文內容還原比對
      const parsedLocal = parseLocalMarkdown(localContent);
      const restoredLocalBody = restoreObsidianLinks(parsedLocal.content, slugToOriginalName);

      if (normalizeContent(restoredLocalBody) !== normalizeContent(externalContent)) {
        // 內容實質不一致，比較檔案修改時間
        const localStat = fs.statSync(targetFilePath);
        const externalStat = fs.statSync(fullSourcePath);

        if (localStat.mtimeMs > externalStat.mtimeMs) {
          shouldSyncLocalToExternal = true;
        } else {
          shouldSyncExternalToLocal = true;
        }
      } else {
        // 內容實質一致，直接跳過，避開 Git 操作產生的假時間戳假同步
        skipCount++;
      }
    } else if (externalContent) {
      // 只有外部有，正常同步到本地
      shouldSyncExternalToLocal = true;
    } else if (localContent) {
      // 只有本地有 (理論上不應發生，除非手動新建，反寫回外部)
      shouldSyncLocalToExternal = true;
    }

    // 執行同步決策
    if (shouldSyncLocalToExternal) {
      const parsedLocal = parseLocalMarkdown(localContent);
      const restoredLocalBody = restoreObsidianLinks(parsedLocal.content, slugToOriginalName);

      // 自動產生時間戳 .bak 備份檔案，防止意外覆寫，並限制最多保留最近 3 次備份
      if (fs.existsSync(fullSourcePath)) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const backupPath = `${fullSourcePath}.${timestamp}.bak`;
        fs.copyFileSync(fullSourcePath, backupPath);

        const dir = path.dirname(fullSourcePath);
        const baseName = path.basename(fullSourcePath);
        const bakFiles = fs.readdirSync(dir)
          .filter(f => f.startsWith(baseName) && f.endsWith('.bak') && f !== baseName)
          .map(f => ({
            name: f,
            path: path.join(dir, f),
            mtime: fs.statSync(path.join(dir, f)).mtimeMs
          }));

        bakFiles.sort((a, b) => a.mtime - b.mtime);

        if (bakFiles.length > 3) {
          const filesToDelete = bakFiles.slice(0, bakFiles.length - 3);
          for (const f of filesToDelete) {
            fs.unlinkSync(f.path);
          }
        }
      }

      fs.writeFileSync(fullSourcePath, restoredLocalBody, 'utf8');
      console.log(`📝 [回寫] 檢測到本地編輯 (Keystatic)，已備份並反寫至外部: ${file}`);
      writeBackCount++;
    } else if (shouldSyncExternalToLocal) {
      let content = externalContent;

      // 2a. 解析雙向連結
      content = content.replace(/\[\[([^\]|#]+)(#[^\]|]+)?(?:\|([^\]]+))?\]\]/g, (match, baseTerm, anchor, aliasPart) => {
        const cleanBaseTerm = baseTerm.replace(/\.md$/i, '').trim();
        const cleanAnchor = anchor ? anchor.trim() : '';
        const cleanAlias = aliasPart ? aliasPart.replace(/^\|/, '').trim() : '';

        let targetMapping = fileToConfig[cleanBaseTerm] || titleToConfig[cleanBaseTerm] || slugToConfig[cleanBaseTerm.toLowerCase()];

        if (targetMapping) {
          const displayTitle = cleanAlias || targetMapping.title || cleanBaseTerm;
          const linkPath = `/shanzhuang/${targetMapping.collection}/${targetMapping.slug}${cleanAnchor}`;
          return `[${displayTitle}](${linkPath})`;
        } else {
          const fallbackText = cleanAlias || cleanBaseTerm;
          console.warn(`⚠️  [警告] 檔案 "${file}" 中的連結 "${match}" 無法在對照表中解析，已降級為失效標籤 "${fallbackText}"。`);
          return `<span class="broken-link" title="此條目暫無詳細設定">${fallbackText}</span>`;
        }
      });

      // 2b. 注入 Frontmatter
      if (!mapInfo.pubDate) {
        const stat = fs.statSync(fullSourcePath);
        mapInfo.pubDate = stat.mtime.toISOString().split('T')[0];
      }
      
      const frontmatter = toYAML(mapInfo);
      const finalFileContent = `${frontmatter}\n\n${content}`;

      // 2c. 寫入專案目標目錄
      if (!fs.existsSync(targetDir)) {
        fs.mkdirSync(targetDir, { recursive: true });
      }
      fs.writeFileSync(targetFilePath, finalFileContent, 'utf8');
      syncCount++;
    }
  });

  console.log(`\n🎉 [成功] 雙向同步完成！`);
  console.log(`   - 外部 -> 本地 (覆蓋/同步): ${syncCount} 個`);
  console.log(`   - 本地 -> 外部 (備份/回寫): ${writeBackCount} 個`);
  console.log(`   - 內容無變更 (跳過): ${skipCount} 個`);
}

runSync();
