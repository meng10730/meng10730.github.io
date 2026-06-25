import fs from 'fs';
import path from 'path';
import readline from 'readline';
import fse from 'fs-extra'; // package.json 中已有的 fs-extra

const CONTENT_DIR = path.resolve('src/content');
const BACKUP_DIR = path.resolve('.backup');

function getBackups() {
  if (!fs.existsSync(BACKUP_DIR)) {
    return [];
  }
  return fs.readdirSync(BACKUP_DIR).filter(item => {
    const fullPath = path.join(BACKUP_DIR, item);
    return fs.statSync(fullPath).isDirectory() && (item.startsWith('build-') || item.startsWith('pre-restore-'));
  }).sort((a, b) => b.localeCompare(a)); // 最新備份排在前面
}

function askQuestion(query) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });
  return new Promise(resolve => rl.question(query, ans => {
    rl.close();
    resolve(ans.trim());
  }));
}

async function runRestore() {
  console.log('\x1b[36m=== 唐門山莊歷史備份安全還原工具 ===\x1b[0m');

  const backups = getBackups();
  if (backups.length === 0) {
    console.log('❌ 找不到任何歷史備份目錄。');
    return;
  }

  console.log('\n請選擇您要還原的備份版本：');
  backups.forEach((b, index) => {
    // 簡單解析時間戳記
    const parts = b.split('-');
    const tsStr = parts[parts.length - 1]; // YYYYMMDD_HHMMSS
    let timeLabel = '';
    if (tsStr && tsStr.length === 15) {
      const y = tsStr.substring(0, 4);
      const m = tsStr.substring(4, 6);
      const d = tsStr.substring(6, 8);
      const h = tsStr.substring(9, 11);
      const min = tsStr.substring(11, 13);
      const s = tsStr.substring(13, 15);
      timeLabel = `(${y}/${m}/${d} ${h}:${min}:${s})`;
    }
    const typeLabel = b.startsWith('build-') ? '建置自動備份' : '還原前防震備份';
    console.log(`  [${index + 1}] ${b} ${timeLabel} -- ${typeLabel}`);
  });
  console.log('  [Q] 退出還原');

  const choice = await askQuestion('\n請輸入對應的序號或 Q 退出：');
  if (choice.toLowerCase() === 'q' || !choice) {
    console.log('還原已取消。');
    return;
  }

  const selectedIndex = parseInt(choice, 10) - 1;
  if (isNaN(selectedIndex) || selectedIndex < 0 || selectedIndex >= backups.length) {
    console.log('❌ 無效的選擇，還原中止。');
    return;
  }

  const selectedBackup = backups[selectedIndex];
  const selectedBackupPath = path.join(BACKUP_DIR, selectedBackup);

  console.log(`\n\x1b[33m您選擇了還原版本：「${selectedBackup}」\x1b[0m`);
  
  // 再次防強行覆寫確認
  const confirm = await askQuestion('此操作將覆蓋當前的所有文章與設定！確定要執行？(y/N)：');
  if (confirm.toLowerCase() !== 'y') {
    console.log('還原已取消。');
    return;
  }

  // 1. 強制在覆蓋前對當前 src/content 進行防震臨時備份
  const pad = (n) => String(n).padStart(2, '0');
  const now = new Date();
  const timestamp = `${now.getFullYear()}${pad(now.getMonth()+1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
  const preRestoreDir = path.join(BACKUP_DIR, `pre-restore-${timestamp}`);

  if (fs.existsSync(CONTENT_DIR)) {
    console.log(`\n📦 [防護備份] 正在備份當前 content 至 ${preRestoreDir}...`);
    fse.copySync(CONTENT_DIR, preRestoreDir);
  }

  // 2. 執行拷貝與覆寫還原
  try {
    console.log(`⚡ [還原執行] 正在清理並將 ${selectedBackup} 還原至 src/content/...`);
    // 清空現有目錄，以防殘留檔案
    fse.emptyDirSync(CONTENT_DIR);
    // 複製備份內容
    fse.copySync(selectedBackupPath, CONTENT_DIR);
    console.log('\x1b[32m\n🎉 還原成功！網站內容已恢復至選定之歷史版本！\x1b[0m');
  } catch (err) {
    console.error('\x1b[31m❌ 還原失敗：\x1b[0m', err);
  }
}

runRestore();
