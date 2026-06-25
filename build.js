import { build } from 'astro';
import fs from 'fs-extra';
import path from 'path';
import { execSync } from 'child_process';

process.on('uncaughtException', (err) => {
  console.error('--- BUILD SYSTEM UNCAUGHT EXCEPTION ---');
  console.error(err);
});
process.on('unhandledRejection', (reason) => {
  console.error('--- BUILD SYSTEM UNHANDLED REJECTION ---');
  console.error(reason);
});

const pathPageFile = path.resolve('src/pages/keystatic/[...params].astro');
let pageFileBackup = null;
const pathApi = path.resolve('src/pages/api/keystatic');
const pathApiTemp = path.resolve('temp-keystatic-api');

// 輔助函式：中英文與數字之間自動加空格 (Pangu 規格)
function panguFormat(text) {
  let frontmatter = '';
  let body = text;
  const fmMatch = text.match(/^---([\s\S]*?)---/);
  if (fmMatch) {
    frontmatter = fmMatch[0];
    body = text.substring(frontmatter.length);
  }

  // 保護 Markdown 程式碼區塊不被格式化
  const parts = body.split(/(```[\s\S]*?```)/g);
  const formattedParts = parts.map(part => {
    if (part.startsWith('```')) return part;
    
    let temp = part;
    // 補全中英文/數字邊界的空格
    temp = temp.replace(/([\u4e00-\u9fa5])([a-zA-Z0-9])/g, '$1 $2');
    temp = temp.replace(/([a-zA-Z0-9])([\u4e00-\u9fa5])/g, '$1 $2');
    return temp;
  });

  return frontmatter + formattedParts.join('');
}

// 輔助腳本：對 src/content 下的所有 Markdown 進行空格補全
async function formatAllMarkdownSpaces() {
  const contentDir = path.resolve('src/content');
  if (!await fs.pathExists(contentDir)) return;

  const processDir = async (dir) => {
    const items = await fs.readdir(dir);
    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = await fs.statSync(fullPath);
      if (stat.isDirectory()) {
        await processDir(fullPath);
      } else if (stat.isFile() && item.endsWith('.md')) {
        const raw = await fs.readFile(fullPath, 'utf8');
        const formatted = panguFormat(raw);
        if (raw !== formatted) {
          await fs.writeFile(fullPath, formatted, 'utf8');
        }
      }
    }
  };

  await processDir(contentDir);
  console.log('✅ Markdown 中英文/數字空格排版自動格式化完成。');
}

// 輔助腳本：滾動備份，保留最新 5 次
async function performBuildBackup() {
  const pad = (n) => String(n).padStart(2, '0');
  const now = new Date();
  const timestamp = `${now.getFullYear()}${pad(now.getMonth()+1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
  const backupDir = path.resolve('.backup');
  const backupSubDir = path.join(backupDir, `build-${timestamp}`);
  const contentDir = path.resolve('src/content');

  // 1. 強制確保 .backup/ 寫入 .gitignore 進行安全隔離
  const gitignorePath = path.resolve('.gitignore');
  if (await fs.pathExists(gitignorePath)) {
    let gitignore = await fs.readFile(gitignorePath, 'utf8');
    if (!gitignore.includes('.backup/')) {
      await fs.appendFile(gitignorePath, '\n# local backups & trash\n.backup/\ntrash/\n');
    }
  }

  // 2. 備份當前 content
  if (await fs.pathExists(contentDir)) {
    await fs.copy(contentDir, backupSubDir);
    console.log(`📦 [備份系統] 已自動備份當前文章與設定至 ${backupSubDir}`);
  }

  // 3. 滾動限制 (保留最新 5 次)
  if (await fs.pathExists(backupDir)) {
    const list = (await fs.readdir(backupDir))
      .filter(item => item.startsWith('build-') || item.startsWith('pre-restore-'))
      .sort((a, b) => b.localeCompare(a)); // 最新在最前
    
    if (list.length > 5) {
      for (let i = 5; i < list.length; i++) {
        await fs.remove(path.join(backupDir, list[i]));
        console.log(`🧹 [清理備份] 已自動刪除過期備份：${list[i]}`);
      }
    }
  }
}

async function run() {
  console.log('--- Preparing build (disabling dev-only routes) ---');
  
  // 1. 執行自動防禦備份
  try {
    await performBuildBackup();
  } catch (err) {
    console.error('⚠️ [備份系統] 備份失敗：', err);
  }

  // 2. 執行中英文自動加空格排版優化
  try {
    await formatAllMarkdownSpaces();
  } catch (err) {
    console.error('⚠️ [排版系統] 空格格式化失敗：', err);
  }

  // 3. 執行正文未登記條目、文風與幽靈資源清理檢測
  try {
    execSync('node scripts/check-glossary.js', { stdio: 'inherit' });
  } catch (err) {
    // 僅作為非阻塞警告，不中斷建置
  }

  if (await fs.pathExists(pathPageFile)) {
    pageFileBackup = await fs.readFile(pathPageFile, 'utf8');
    const productionContent = `---
import { KeystaticApp } from '../../components/KeystaticApp.tsx';

export const prerender = true;

export function getStaticPaths() {
  return [
    { params: { params: undefined } },
  ];
}
---
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>莊主後台 | 唐門山莊</title>
  <script is:inline>
    (function() {
      var params = new URLSearchParams(window.location.search);
      var redirectUrl = params.get('redirect');
      if (redirectUrl) {
        window.history.replaceState(null, '', redirectUrl);
      }
    })();
  </script>
</head>
<body>
  <KeystaticApp client:only="react" />
</body>
</html>
`;
    await fs.writeFile(pathPageFile, productionContent, 'utf8');
    console.log('Configured keystatic page for static pre-rendering');
  }
  if (await fs.pathExists(pathApi)) {
    await fs.move(pathApi, pathApiTemp, { overwrite: true });
    console.log('Disabled keystatic API folder');
  }

  let buildError = null;
  try {
    console.log('--- Running Astro Build (Programmatic) ---');
    // 強制注入 build 參數，確保 config 判定為生產建置
    if (!process.argv.includes('build')) {
      process.argv.push('build');
    }
    await build({});
  } catch (err) {
    buildError = err;
  } finally {
    console.log('--- Cleaning up (restoring dev-only routes) ---');
    if (pageFileBackup !== null) {
      await fs.writeFile(pathPageFile, pageFileBackup, 'utf8');
      console.log('Restored keystatic page file content');
    }
    if (await fs.pathExists(pathApiTemp)) {
      await fs.move(pathApiTemp, pathApi, { overwrite: true });
      console.log('Restored keystatic API folder');
    }
  }

  if (buildError) {
    console.error('Build failed with error:');
    console.error(buildError);
    process.exit(1);
  } else {
    console.log('Build completed successfully!');
  }
}
run();
