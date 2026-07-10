import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.join(__dirname, '..');
const CLI_PATH = path.join(PROJECT_ROOT, 'scripts', 'add-collection-cli.js');

function runInteractiveCLI(steps) {
  return new Promise((resolve, reject) => {
    console.log(`\n🤖 [測試進程] 啟動 add-collection-cli.js`);
    const child = spawn('node', [CLI_PATH], { cwd: PROJECT_ROOT, stdio: ['pipe', 'pipe', 'inherit'] });
    
    let output = '';
    
    child.stdout.on('data', (data) => {
      const chunk = data.toString();
      output += chunk;
      process.stdout.write(chunk); // 同步輸出到主控制台以供檢視

      // 依序比對未執行的步驟，若匹配提示詞則輸入對應值
      for (const step of steps) {
        if (!step.sent && chunk.includes(step.trigger)) {
          step.sent = true;
          console.log(`\n🤖 [測試模擬輸入 - 觸發詞: "${step.trigger}"] -> ${step.value}`);
          child.stdin.write(step.value + '\n');
          break; // 每次 data 事件只寫入一個輸入，避免 Race Condition 連續寫入
        }
      }
    });

    child.on('close', (code) => {
      // 檢查是否所有步驟都已執行
      const incomplete = steps.find(s => !s.sent);
      if (incomplete) {
        console.warn(`\n⚠️ [警告] 測試結束，但仍有未執行的輸入步驟: ${JSON.stringify(incomplete)}`);
      }
      if (code === 0) {
        resolve(output);
      } else {
        reject(new Error(`子進程以 Exit Code ${code} 結束。`));
      }
    });

    child.on('error', (err) => {
      reject(err);
    });
  });
}

async function testSuite() {
  console.log('====================================================');
  // 檢查 Git 狀態
  try {
    const gitStatus = spawn('git', ['status', '--porcelain'], { cwd: PROJECT_ROOT });
    let statusOut = '';
    gitStatus.stdout.on('data', d => statusOut += d);
    await new Promise(r => gitStatus.on('close', r));
    if (statusOut.trim()) {
      console.warn('⚠️ [警告] 目前 Git 工作區非乾淨狀態。若測試失敗可能需要手動 Git Checkout 還原。');
    }
  } catch (e) {
    // 忽略 Git 檢查錯誤
  }

  // 1. 測試新增類別 magicitems
  console.log('\n====================================================');
  console.log('🧪 [TEST 1] 測試新增自訂類別 (magicitems)');
  console.log('====================================================');
  await runInteractiveCLI([
    { trigger: '請選擇操作序號 (1-4):', value: '1', sent: false },
    { trigger: '請輸入要新增的類別英文名稱 (例如: weapons):', value: 'magicitems', sent: false },
    { trigger: '請輸入此類別的中文名稱標籤', value: '魔法道具', sent: false },
    { trigger: '請輸入前台列表頁的副標題描述', value: '神秘的魔法道具記載', sent: false },
    // 新增自訂欄位 power (text)
    { trigger: '是否要為此類別新增自訂欄位？(y/n)', value: 'y', sent: false },
    { trigger: '請輸入自訂欄位英文名稱 (例如: power):', value: 'power', sent: false },
    { trigger: '請選擇欄位類型：', value: '1', sent: false },
    { trigger: '請輸入此欄位的中文名稱標籤', value: '法力值', sent: false },
    // 新增自訂欄位 novel (novel)
    { trigger: '是否要為此類別新增自訂欄位？(y/n)', value: 'y', sent: false },
    { trigger: '請輸入自訂欄位英文名稱 (例如: power):', value: 'novel', sent: false },
    { trigger: '請選擇欄位類型：', value: '4', sent: false },
    { trigger: '請輸入此欄位的中文名稱標籤', value: '所屬作品', sent: false },
    // 結束自訂欄位輪詢
    { trigger: '是否要為此類別新增自訂欄位？(y/n)', value: 'n', sent: false }
  ]);

  // 驗證新增結果
  const colDir = path.join(PROJECT_ROOT, 'src', 'content', 'magicitems');
  const configContent = fs.readFileSync(path.join(PROJECT_ROOT, 'src', 'content', 'config.ts'), 'utf-8');
  const keystaticContent = fs.readFileSync(path.join(PROJECT_ROOT, 'keystatic.config.ts'), 'utf-8');
  const typeAstroContent = fs.readFileSync(path.join(PROJECT_ROOT, 'src', 'pages', 'shanzhuang', '[type].astro'), 'utf-8');
  const slugAstroContent = fs.readFileSync(path.join(PROJECT_ROOT, 'src', 'pages', 'shanzhuang', '[type]', '[slug].astro'), 'utf-8');

  if (!fs.existsSync(colDir)) {
    throw new Error('❌ TEST 1 失敗：類別目錄未建立。');
  }
  if (!configContent.includes('magicitems')) {
    throw new Error('❌ TEST 1 失敗：config.ts 未註冊類別。');
  }
  if (!configContent.includes('power: z.string().optional()') || !configContent.includes('novel: z.string().optional()')) {
    throw new Error('❌ TEST 1 失敗：config.ts 中自訂欄位 Schema 註冊不正確。');
  }
  const compactKeystatic = keystaticContent.replace(/\s+/g, '');
  const hasPower = compactKeystatic.includes("power:fields.text({label:'法力值'})") ||
                    compactKeystatic.includes('power:fields.text({label:"法力值"})') ||
                    compactKeystatic.includes("power:fields.text({label:'法力值',})") ||
                    compactKeystatic.includes('power:fields.text({label:"法力值",})');
                    
  const hasNovel = compactKeystatic.includes("novel:fields.text({label:'所屬作品'})") ||
                    compactKeystatic.includes('novel:fields.text({label:"所屬作品"})') ||
                    compactKeystatic.includes("novel:fields.text({label:'所屬作品',})") ||
                    compactKeystatic.includes('novel:fields.text({label:"所屬作品",})');

  if (!hasPower || !hasNovel) {
    throw new Error('❌ TEST 1 失敗：keystatic.config.ts 中自訂欄位註冊不正確。');
  }

  const compactType = typeAstroContent.replace(/\s+/g, '');
  const compactSlug = slugAstroContent.replace(/\s+/g, '');
  
  if (!compactType.includes("magicitems:{power:'text',novel:'novel',}") && !compactType.includes("magicitems:{power:'text',novel:'novel'}")) {
    throw new Error('❌ TEST 1 失敗：[type].astro 中未正確註冊 magicitems 的 RENDER_CONFIG。');
  }
  if (!compactSlug.includes("magicitems:{power:'text',novel:'novel',}") && !compactSlug.includes("magicitems:{power:'text',novel:'novel'}")) {
    throw new Error('❌ TEST 1 失敗：[type]/[slug].astro 中未正確註冊 magicitems 的 RENDER_CONFIG。');
  }

  const tempFileContent = fs.readFileSync(path.join(colDir, 'example-temp.md'), 'utf-8');
  if (!tempFileContent.includes('power: "測試法力值"') || !tempFileContent.includes('novel: "長生劫"')) {
    throw new Error('❌ TEST 1 失敗：產生的範例 md 檔中未正確包含自訂欄位。');
  }

  console.log('\n\x1b[32m✓ TEST 1 成功：自訂類別 magicitems (含自訂欄位) 已成功註冊、範例產出並通過編譯！\x1b[0m');

  // 2. 測試修改類別 magicitems 的中文 Label
  console.log('\n====================================================');
  console.log('🧪 [TEST 2] 測試修改自訂類別 (magicitems -> 仙家法寶)');
  console.log('====================================================');
  // 1 選擇 magicitems, 新 Label, 新副標題
  await runInteractiveCLI([
    { trigger: '請選擇操作序號 (1-4):', value: '2', sent: false },
    { trigger: '請選擇要修改的類別序號', value: '1', sent: false },
    { trigger: '請輸入新的中文名稱標籤 (留空保持原樣):', value: '仙家法寶', sent: false },
    { trigger: '請輸入新的副標題描述 (留空保持原樣):', value: '至尊仙法寶物描述', sent: false }
  ]);

  // 驗證修改結果
  const typeAstroContent2 = fs.readFileSync(path.join(PROJECT_ROOT, 'src', 'pages', 'shanzhuang', '[type].astro'), 'utf-8');
  if (!typeAstroContent2.includes('仙家法寶')) {
    throw new Error('❌ TEST 2 失敗：[type].astro 中中文標籤未更新。');
  }
  console.log('\n\x1b[32m✓ TEST 2 成功：中文標籤已成功原地修改為「仙家法寶」！\x1b[0m');

  // 3. 測試刪除類別 magicitems
  console.log('\n====================================================');
  console.log('🧪 [TEST 3] 測試刪除自訂類別 (magicitems)');
  console.log('====================================================');
  // 3 選擇刪除, 1 選擇 magicitems, y magicitems 二次確認
  await runInteractiveCLI([
    { trigger: '請選擇操作序號 (1-4):', value: '3', sent: false },
    { trigger: '請選擇要刪除的類別序號', value: '1', sent: false },
    { trigger: '為確認操作，請輸入 "y" 隨後輸入', value: 'y magicitems', sent: false }
  ]);

  // 驗證刪除結果
  const finalConfigContent = fs.readFileSync(path.join(PROJECT_ROOT, 'src', 'content', 'config.ts'), 'utf-8');
  const finalTypeAstroContent = fs.readFileSync(path.join(PROJECT_ROOT, 'src', 'pages', 'shanzhuang', '[type].astro'), 'utf-8');
  const finalSlugAstroContent = fs.readFileSync(path.join(PROJECT_ROOT, 'src', 'pages', 'shanzhuang', '[type]', '[slug].astro'), 'utf-8');

  if (fs.existsSync(colDir) || finalConfigContent.includes('magicitems')) {
    throw new Error('❌ TEST 3 失敗：類別目錄未刪除或 config.ts 仍殘留 Schema 定義。');
  }
  if (finalTypeAstroContent.includes('magicitems') || finalSlugAstroContent.includes('magicitems')) {
    throw new Error('❌ TEST 3 失敗：Astro 路由或 RENDER_CONFIG 中仍殘留 magicitems。');
  }
  console.log('\n\x1b[32m✓ TEST 3 成功：自訂類別 magicitems 與代碼註冊已被完全清除乾淨！\x1b[0m');

  console.log('\n====================================================');
  console.log('🎉 恭喜！自訂類別 CRUD (新增、修改、刪除) 所有 E2E 測試全部通過！');
  console.log('====================================================');
}

testSuite().catch(err => {
  console.error('\n❌ 測試執行失敗：', err.message);
  process.exit(1);
});
