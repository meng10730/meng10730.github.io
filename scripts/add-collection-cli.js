import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import readline from 'readline';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PROJECT_ROOT = path.join(__dirname, '..');
const CONFIG_TS_PATH = path.join(PROJECT_ROOT, 'src', 'content', 'config.ts');
const KEYSTATIC_CONFIG_PATH = path.join(PROJECT_ROOT, 'keystatic.config.ts');
const TYPE_ASTRO_PATH = path.join(PROJECT_ROOT, 'src', 'pages', 'shanzhuang', '[type].astro');
const SLUG_ASTRO_PATH = path.join(PROJECT_ROOT, 'src', 'pages', 'shanzhuang', '[type]', '[slug].astro');
const IMPORT_CLI_PATH = path.join(PROJECT_ROOT, 'scripts', 'import-novels-cli.js');

const RESERVED_WORDS = [
  'novels', 'characters', 'worldview', 'factions', 'guoxue', 'items', 'techniques', 'bestiary',
  'blog', 'works', 'api', 'keystatic', 'posts', 'public', 'src', 'pages', 'layouts', 'components'
];

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});
const question = (query) => new Promise((resolve) => rl.question(query, resolve));

// 備份與還原檔案配置
const filesToBackup = [
  { path: CONFIG_TS_PATH, bak: CONFIG_TS_PATH + '.bak' },
  { path: KEYSTATIC_CONFIG_PATH, bak: KEYSTATIC_CONFIG_PATH + '.bak' },
  { path: TYPE_ASTRO_PATH, bak: TYPE_ASTRO_PATH + '.bak' },
  { path: SLUG_ASTRO_PATH, bak: SLUG_ASTRO_PATH + '.bak' },
  { path: IMPORT_CLI_PATH, bak: IMPORT_CLI_PATH + '.bak' }
];

let globalBackupDirs = []; // 暫存被刪除/移動的目錄快照

function backupFiles() {
  console.log('⌛ 正在自動備份關鍵設定檔案...');
  for (const f of filesToBackup) {
    if (fs.existsSync(f.path)) {
      fs.copyFileSync(f.path, f.bak);
    }
  }
  console.log('✓ 設定檔備份完成。');
}

function restoreFiles() {
  console.log('⚠️ 正在觸發還原機制 (Rollback)...');
  for (const f of filesToBackup) {
    if (fs.existsSync(f.bak)) {
      fs.copyFileSync(f.bak, f.path);
      fs.unlinkSync(f.bak);
    }
  }
  
  // 還原目錄快照
  for (const d of globalBackupDirs) {
    if (fs.existsSync(d.bak)) {
      if (fs.existsSync(d.original)) {
        try {
          if (process.platform === 'win32') {
            execSync(`rmdir /s /q "${d.original}"`, { stdio: 'ignore' });
          } else {
            fs.rmSync(d.original, { recursive: true, force: true });
          }
        } catch (e) {
          // 容錯
        }
      }
      try {
        fs.renameSync(d.bak, d.original);
        console.log(`✓ 已還原目錄: ${d.original}`);
      } catch (e) {
        console.error(`❌ 還原目錄失敗: ${d.original}`, e.message);
      }
    }
  }
  globalBackupDirs = [];
  console.log('✓ 還原完成。');
}

function cleanBackupFiles() {
  for (const f of filesToBackup) {
    if (fs.existsSync(f.bak)) {
      fs.unlinkSync(f.bak);
    }
  }
  
  // 清理目錄快照
  for (const d of globalBackupDirs) {
    if (fs.existsSync(d.bak)) {
      try {
        if (process.platform === 'win32') {
          execSync(`rmdir /s /q "${d.bak}"`, { stdio: 'ignore' });
        } else {
          fs.rmSync(d.bak, { recursive: true, force: true });
        }
      } catch (e) {
        // 容錯
      }
    }
  }
  globalBackupDirs = [];
}

// 取得目前已存在的自訂類別列表 (藉由讀取 config.ts 裡的 DEF 標記)
function getCustomCollections() {
  if (!fs.existsSync(CONFIG_TS_PATH)) return [];
  const content = fs.readFileSync(CONFIG_TS_PATH, 'utf-8');
  const customCols = [];
  const matches = content.matchAll(/\/\* BEGIN_COLLECTION_([a-z]+)_DEF \*\//g);
  for (const m of matches) {
    customCols.push(m[1]);
  }
  return Array.from(new Set(customCols));
}

// 格式化代碼
function formatFiles() {
  console.log('⌛ 正在自動格式化代碼...');
  for (const f of filesToBackup) {
    try {
      execSync(`npx prettier --write "${f.path}"`, { stdio: 'ignore' });
    } catch (err) {
      // 容錯跳過
    }
  }
  console.log('✓ 格式化完成。');
}

// 執行 npm run build 校驗編譯
function testBuild() {
  console.log('⌛ 正在執行 npm run build 以確認無編譯或語法錯誤 (此過程約需 10-15 秒)...');
  try {
    execSync('npm run build', { stdio: 'ignore', cwd: PROJECT_ROOT });
    console.log('✓ 全站編譯建置成功！');
  } catch (err) {
    throw new Error('npm run build 執行失敗，請檢查程式碼語法。');
  }
}

// 新增功能 (Create)
async function handleCreate() {
  console.log('\n--- 新增自訂類別 ---');
  let colName = '';
  while (true) {
    const input = await question('請輸入要新增的類別英文名稱 (例如: weapons): ');
    colName = input.trim().toLowerCase();

    if (!colName) {
      console.log('⚠️ 名稱不能為空，請重新輸入。');
      continue;
    }

    if (!/^[a-z]+$/.test(colName)) {
      console.log('⚠️ 類別名稱只能包含小寫英文字母 (a-z)，不允許數字、空格或特殊字元。');
      continue;
    }

    if (RESERVED_WORDS.includes(colName) || getCustomCollections().includes(colName)) {
      console.log(`⚠️ 名稱 "${colName}" 是保留字或已存在類別，不可使用。`);
      continue;
    }

    break;
  }

  const colLabel = (await question(`請輸入此類別的中文名稱標籤 [預設: "${colName}"]: `)).trim() || colName;
  const colSubtitle = (await question(`請輸入前台列表頁的副標題描述 [預設: "自動新增的 ${colLabel} 類別記載"]: `)).trim() || `自動新增的 ${colLabel} 類別記載`;

  // 輪詢自訂欄位
  const customFields = [];
  const fieldReservedWords = ['id', 'slug', 'title', 'name', 'pubDate', 'content', 'description'];
  
  while (true) {
    const addFieldAns = await question('是否要為此類別新增自訂欄位？(y/n) [預設 n]: ');
    if (addFieldAns.trim().toLowerCase() !== 'y') {
      break;
    }
    
    let fieldName = '';
    while (true) {
      const nameInput = await question('請輸入自訂欄位英文名稱 (例如: power): ');
      fieldName = nameInput.trim().toLowerCase();
      
      if (!fieldName) {
        console.log('⚠️ 欄位名稱不能為空。');
        continue;
      }
      
      if (!/^[a-z]+$/.test(fieldName)) {
        console.log('⚠️ 欄位名稱只能包含小寫英文字母 (a-z)，不允許數字、空格或特殊字元。');
        continue;
      }
      
      if (fieldReservedWords.includes(fieldName)) {
        console.log(`⚠️ 欄位名稱 "${fieldName}" 是保留字 (如 title, pubDate, content 等)，不可使用。`);
        continue;
      }
      
      if (customFields.some(f => f.name === fieldName)) {
        console.log(`⚠️ 欄位名稱 "${fieldName}" 已在本次新增清單中，不能重複。`);
        continue;
      }
      
      break;
    }
    
    let fieldType = '';
    while (true) {
      console.log('請選擇欄位類型：');
      console.log('  [1] 文字 (text)');
      console.log('  [2] 超連結 (link)');
      console.log('  [3] 圖片 (image)');
      console.log('  [4] 小說關聯 (novel)');
      const typeAns = await question('請輸入序號 (1-4): ');
      const t = typeAns.trim();
      if (t === '1') { fieldType = 'text'; break; }
      if (t === '2') { fieldType = 'link'; break; }
      if (t === '3') { fieldType = 'image'; break; }
      if (t === '4') { fieldType = 'novel'; break; }
      console.log('⚠️ 選擇無效，請重新輸入。');
    }
    
    const fieldLabel = (await question(`請輸入此欄位的中文名稱標籤 [預設: "${fieldName}"]: `)).trim() || fieldName;
    
    customFields.push({ name: fieldName, type: fieldType, label: fieldLabel });
    console.log(`✓ 已暫存欄位: ${fieldName} (${fieldType}) - ${fieldLabel}`);
  }

  // 備份
  backupFiles();

  let tempDirCreated = false;
  let tempFileCreated = false;
  const targetDir = path.join(PROJECT_ROOT, 'src', 'content', colName);
  const tempFilePath = path.join(targetDir, 'example-temp.md');

  try {
    // 1. 寫入 config.ts
    console.log(`⌛ 正在註冊 Schema 至 config.ts...`);
    let configContent = fs.readFileSync(CONFIG_TS_PATH, 'utf-8');
    
    let customFieldsSchema = '';
    if (customFields.length > 0) {
      customFieldsSchema = customFields.map(f => `    ${f.name}: z.string().optional(),`).join('\n');
    }

    const schemaDef = `/* BEGIN_COLLECTION_${colName}_DEF */
const ${colName} = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    pubDate: z.coerce.date(),
${customFieldsSchema}
  }),
});
/* END_COLLECTION_${colName}_DEF */

// [ADD_NEW_COLLECTION_DEFINITION_HERE]`;

    const schemaExport = `
/* BEGIN_COLLECTION_${colName}_EXPORT */
  ${colName},
/* END_COLLECTION_${colName}_EXPORT */
  // [ADD_NEW_COLLECTION_EXPORT_HERE]`;

    configContent = configContent.replace('// [ADD_NEW_COLLECTION_DEFINITION_HERE]', schemaDef);
    configContent = configContent.replace('  // [ADD_NEW_COLLECTION_EXPORT_HERE]', schemaExport);
    fs.writeFileSync(CONFIG_TS_PATH, configContent, 'utf-8');

    // 2. 寫入 keystatic.config.ts
    console.log(`⌛ 正在註冊後台配置至 keystatic.config.ts...`);
    let keystaticContent = fs.readFileSync(KEYSTATIC_CONFIG_PATH, 'utf-8');
    
    let keystaticFieldsSchema = '';
    if (customFields.length > 0) {
      keystaticFieldsSchema = customFields.map(f => {
        if (f.type === 'image') {
          return `        ${f.name}: fields.image({ label: '${f.label}', directory: 'public/images/${colName}', publicPath: '/images/${colName}' }),`;
        } else {
          return `        ${f.name}: fields.text({ label: '${f.label}' }),`;
        }
      }).join('\n');
    }

    const keystaticDef = `/* BEGIN_COLLECTION_${colName}_KEYSTATIC */
    ${colName}: collection({
      label: '${colLabel} (山莊)',
      slugField: 'title',
      path: 'src/content/${colName}/*',
      format: { contentField: 'content' },
      schema: {
        title: fields.slug({
          name: { label: '名稱' },
          slug: { label: '網址別名 (Slug)', slugify: pinyinSlugify }
        }),
        description: fields.text({ label: '簡介', multiline: true }),
        pubDate: fields.date({ label: '建立日期' }),
${keystaticFieldsSchema}
        content: fields.mdx({ label: '詳細設定內文', extension: 'md' }),
      },
    }),
/* END_COLLECTION_${colName}_KEYSTATIC */
    // [ADD_NEW_COLLECTION_KEYSTATIC_HERE]`;

    keystaticContent = keystaticContent.replace('    // [ADD_NEW_COLLECTION_KEYSTATIC_HERE]', keystaticDef);
    fs.writeFileSync(KEYSTATIC_CONFIG_PATH, keystaticContent, 'utf-8');

    // 3. 寫入 [type].astro
    console.log(`⌛ 正在註冊路由與 RENDER_CONFIG 至 [type].astro...`);
    let typeContent = fs.readFileSync(TYPE_ASTRO_PATH, 'utf-8');
    
    const typePathDef = `/* BEGIN_COLLECTION_${colName}_PATH */
    , { params: { type: '${colName}' }, props: { title: '${colLabel}列表', subtitle: '${colSubtitle}' } }
/* END_COLLECTION_${colName}_PATH */
    // [ADD_NEW_COLLECTION_PATH_HERE]`;
    typeContent = typeContent.replace('    // [ADD_NEW_COLLECTION_PATH_HERE]', typePathDef);

    let renderConfigStr = '';
    if (customFields.length > 0) {
      renderConfigStr = `/* BEGIN_COLLECTION_${colName}_RENDER_CONFIG */
  ${colName}: {
    ${customFields.map(f => `${f.name}: '${f.type}',`).join('\n    ')}
  },
/* END_COLLECTION_${colName}_RENDER_CONFIG */
  // [ADD_NEW_COLLECTION_RENDER_CONFIG_HERE]`;
    } else {
      renderConfigStr = `/* BEGIN_COLLECTION_${colName}_RENDER_CONFIG */
  ${colName}: {},
/* END_COLLECTION_${colName}_RENDER_CONFIG */
  // [ADD_NEW_COLLECTION_RENDER_CONFIG_HERE]`;
    }
    typeContent = typeContent.replace('  // [ADD_NEW_COLLECTION_RENDER_CONFIG_HERE]', renderConfigStr);
    fs.writeFileSync(TYPE_ASTRO_PATH, typeContent, 'utf-8');

    // 4. 寫入 [type]/[slug].astro
    console.log(`⌛ 正在註冊路由與 RENDER_CONFIG 至 [type]/[slug].astro...`);
    let slugContent = fs.readFileSync(SLUG_ASTRO_PATH, 'utf-8');
    
    const slugGetDef = `/* BEGIN_COLLECTION_${colName}_GET */
    const ${colName}Col = await getCollection('${colName}', entry => !entry.id.startsWith('_'));
/* END_COLLECTION_${colName}_GET */
    // [ADD_NEW_COLLECTION_GET_HERE]`;

    const slugMapDef = `/* BEGIN_COLLECTION_${colName}_MAP */
      , ...${colName}Col.map(entry => ({
        params: { type: '${colName}', slug: entry.slug },
        props: { entry, type: '${colName}' }
      }))
/* END_COLLECTION_${colName}_MAP */
      // [ADD_NEW_COLLECTION_MAP_HERE]`;

    slugContent = slugContent.replace('    // [ADD_NEW_COLLECTION_GET_HERE]', slugGetDef);
    slugContent = slugContent.replace('      // [ADD_NEW_COLLECTION_MAP_HERE]', slugMapDef);

    let slugRenderConfigStr = '';
    if (customFields.length > 0) {
      slugRenderConfigStr = `/* BEGIN_COLLECTION_${colName}_RENDER_CONFIG */
  ${colName}: {
    ${customFields.map(f => `${f.name}: '${f.type}',`).join('\n    ')}
  },
/* END_COLLECTION_${colName}_RENDER_CONFIG */
  // [ADD_NEW_COLLECTION_RENDER_CONFIG_HERE]`;
    } else {
      slugRenderConfigStr = `/* BEGIN_COLLECTION_${colName}_RENDER_CONFIG */
  ${colName}: {},
/* END_COLLECTION_${colName}_RENDER_CONFIG */
  // [ADD_NEW_COLLECTION_RENDER_CONFIG_HERE]`;
    }
    slugContent = slugContent.replace('  // [ADD_NEW_COLLECTION_RENDER_CONFIG_HERE]', slugRenderConfigStr);
    fs.writeFileSync(SLUG_ASTRO_PATH, slugContent, 'utf-8');

    // 5. 寫入 import-novels-cli.js
    console.log(`⌛ 正在註冊類別至 import-novels-cli.js...`);
    let importContent = fs.readFileSync(IMPORT_CLI_PATH, 'utf-8');
    
    const cliArrayDef = `/* BEGIN_COLLECTION_${colName}_CLI_ARRAY */
    '${colName}',
/* END_COLLECTION_${colName}_CLI_ARRAY */
    // [ADD_NEW_COLLECTION_CLI_ARRAY_HERE]`;

    const cliLabelDef = `/* BEGIN_COLLECTION_${colName}_CLI_LABEL */
    , ${colName}: '${colLabel} (${colName})'
/* END_COLLECTION_${colName}_CLI_LABEL */
    // [ADD_NEW_COLLECTION_CLI_LABEL_HERE]`;

    importContent = importContent.replace('    // [ADD_NEW_COLLECTION_CLI_ARRAY_HERE]', cliArrayDef);
    importContent = importContent.replace('    // [ADD_NEW_COLLECTION_CLI_LABEL_HERE]', cliLabelDef);
    fs.writeFileSync(IMPORT_CLI_PATH, importContent, 'utf-8');

    // 建立新類別的範例 Markdown 檔案
    console.log(`⌛ 正在建立類別目錄與測試範例文檔...`);
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
      tempDirCreated = true;
    }

    let mdFieldsStr = '';
    customFields.forEach(f => {
      let val = '';
      if (f.type === 'image') {
        val = `public/images/placeholder.jpg`;
      } else if (f.type === 'link') {
        val = `https://example.com`;
      } else if (f.type === 'novel') {
        val = `長生劫`;
      } else {
        val = `測試${f.label}`;
      }
      mdFieldsStr += `${f.name}: "${val}"\n`;
    });

    const todayStr = new Date().toISOString().split('T')[0];
    const mdContent = `---
title: "範例${colLabel}"
description: "這是自動產生的${colLabel}測試文檔"
pubDate: "${todayStr}"
${mdFieldsStr}---

### ${colLabel}介紹

這是自動新增的 ${colLabel} 類別測試設定檔。
`;
    fs.writeFileSync(tempFilePath, mdContent, 'utf-8');
    tempFileCreated = true;
    console.log(`✓ 已建立範例測試檔: src/content/${colName}/example-temp.md`);

    // 格式化代碼
    formatFiles();

    // 驗證編譯
    testBuild();

    // 建置成功，清除備份
    cleanBackupFiles();
    console.log(`\n\x1b[32m🎉 恭喜！新類別 "${colName}" 新增成功，且全站編譯通過！\x1b[0m`);

  } catch (err) {
    console.error('\n❌ 新增自訂類別失敗：', err.message);
    
    // 觸發 Rollback 還原
    restoreFiles();

    // 刪除新產生的臨時檔案
    if (tempFileCreated && fs.existsSync(tempFilePath)) {
      fs.unlinkSync(tempFilePath);
    }
    if (tempDirCreated && fs.existsSync(targetDir)) {
      try {
        fs.rmdirSync(targetDir);
      } catch (e) {
        // ignore
      }
    }
    throw err;
  }
}

// 修改功能 (Update)
async function handleUpdate() {
  console.log('\n--- 修改自訂類別 ---');
  const customCols = getCustomCollections();

  if (customCols.length === 0) {
    console.log('⚠️ 目前沒有任何可供修改的自訂類別。');
    return;
  }

  console.log('目前存在的自訂類別：');
  customCols.forEach((col, idx) => {
    console.log(`  [${idx + 1}] ${col}`);
  });

  const ans = await question(`請選擇要修改的類別序號 (1-${customCols.length}): `);
  const idx = parseInt(ans.trim(), 10) - 1;
  if (isNaN(idx) || idx < 0 || idx >= customCols.length) {
    console.log('⚠️ 輸入序號無效。');
    return;
  }

  const colName = customCols[idx];
  console.log(`\n您選擇了修改自訂類別: "${colName}"`);
  
  const colLabel = (await question(`請輸入新的中文名稱標籤 (留空保持原樣): `)).trim();
  const colSubtitle = (await question(`請輸入新的副標題描述 (留空保持原樣): `)).trim();

  if (!colLabel && !colSubtitle) {
    console.log('未做任何變更，操作已取消。');
    return;
  }

  // 備份
  backupFiles();

  try {
    // 1. 修改 keystatic.config.ts 裡的 Label
    if (colLabel) {
      console.log(`⌛ 正在修改 keystatic.config.ts 中的 Label...`);
      let keystaticContent = fs.readFileSync(KEYSTATIC_CONFIG_PATH, 'utf-8');
      const startTag = `/* BEGIN_COLLECTION_${colName}_KEYSTATIC */`;
      const endTag = `/* END_COLLECTION_${colName}_KEYSTATIC */`;
      
      const startIndex = keystaticContent.indexOf(startTag);
      const endIndex = keystaticContent.indexOf(endTag);
      if (startIndex !== -1 && endIndex !== -1) {
        let block = keystaticContent.substring(startIndex, endIndex + endTag.length);
        block = block.replace(/label:\s*['"].*?['"]/, `label: '${colLabel} (山莊)'`);
        
        keystaticContent = keystaticContent.substring(0, startIndex) + block + keystaticContent.substring(endIndex + endTag.length);
        fs.writeFileSync(KEYSTATIC_CONFIG_PATH, keystaticContent, 'utf-8');
      }
    }

    // 2. 修改 [type].astro 裡的 title 與 subtitle
    if (colLabel || colSubtitle) {
      console.log(`⌛ 正在修改 [type].astro 中的標籤與副標題...`);
      let typeContent = fs.readFileSync(TYPE_ASTRO_PATH, 'utf-8');
      const startTag = `/* BEGIN_COLLECTION_${colName}_PATH */`;
      const endTag = `/* END_COLLECTION_${colName}_PATH */`;
      
      const startIndex = typeContent.indexOf(startTag);
      const endIndex = typeContent.indexOf(endTag);
      if (startIndex !== -1 && endIndex !== -1) {
        let block = typeContent.substring(startIndex, endIndex + endTag.length);
        if (colLabel) {
          block = block.replace(/title:\s*['"].*?['"]/, `title: '${colLabel}列表'`);
        }
        if (colSubtitle) {
          block = block.replace(/subtitle:\s*['"].*?['"]/, `subtitle: '${colSubtitle}'`);
        }
        
        typeContent = typeContent.substring(0, startIndex) + block + typeContent.substring(endIndex + endTag.length);
        fs.writeFileSync(TYPE_ASTRO_PATH, typeContent, 'utf-8');
      }
    }

    // 3. 修改 import-novels-cli.js 裡的 Label
    if (colLabel) {
      console.log(`⌛ 正在修改 import-novels-cli.js 中的 Label...`);
      let importContent = fs.readFileSync(IMPORT_CLI_PATH, 'utf-8');
      const startTag = `/* BEGIN_COLLECTION_${colName}_CLI_LABEL */`;
      const endTag = `/* END_COLLECTION_${colName}_CLI_LABEL */`;
      
      const startIndex = importContent.indexOf(startTag);
      const endIndex = importContent.indexOf(endTag);
      if (startIndex !== -1 && endIndex !== -1) {
        let block = importContent.substring(startIndex, endIndex + endTag.length);
        block = block.replace(new RegExp(`,\\s*${colName}:\\s*['"].*?['"]`), `, ${colName}: '${colLabel} (${colName})'`);
        
        importContent = importContent.substring(0, startIndex) + block + importContent.substring(endIndex + endTag.length);
        fs.writeFileSync(IMPORT_CLI_PATH, importContent, 'utf-8');
      }
    }

    // 格式化與建置驗證
    formatFiles();
    testBuild();

    // 成功，清除備份
    cleanBackupFiles();
    console.log(`\n\x1b[32m🎉 恭喜！自訂類別 "${colName}" 修改完成，且全站編譯通過！\x1b[0m`);

  } catch (err) {
    console.error('\n❌ 修改自訂類別失敗：', err.message);
    restoreFiles();
    throw err;
  }
}

// 刪除功能 (Delete)
async function handleDelete() {
  console.log('\n--- 刪除自訂類別 ---');
  const customCols = getCustomCollections();

  if (customCols.length === 0) {
    console.log('⚠️ 目前沒有任何可供刪除的自訂類別。');
    return;
  }

  console.log('目前存在的自訂類別：');
  customCols.forEach((col, idx) => {
    console.log(`  [${idx + 1}] ${col}`);
  });

  const ans = await question(`請選擇要刪除的類別序號 (1-${customCols.length}): `);
  const idx = parseInt(ans.trim(), 10) - 1;
  if (isNaN(idx) || idx < 0 || idx >= customCols.length) {
    console.log('⚠️ 輸入序號無效。');
    return;
  }

  const colName = customCols[idx];
  console.log(`\n\x1b[31m🔥 [警告] 您將徹底刪除類別 "${colName}" 及其底下的所有文章與設定！\x1b[0m`);
  
  // 防呆確認
  const confirmCode = await question(`為確認操作，請輸入 "y" 隨後輸入 "${colName}"：`);
  if (confirmCode.trim() !== `y ${colName}`) {
    console.log('⚠️ 防呆校驗不匹配，操作已取消。');
    return;
  }

  // 備份設定檔
  backupFiles();

  // 目錄毫秒級備份快照
  const contentDir = path.join(PROJECT_ROOT, 'src', 'content', colName);
  const imageDir = path.join(PROJECT_ROOT, 'public', 'images', colName);
  const timestamp = Date.now();
  const contentDirBak = path.join(PROJECT_ROOT, 'src', 'content', `.${colName}_${timestamp}_tmp_bak`);
  const imageDirBak = path.join(PROJECT_ROOT, 'public', 'images', `.${colName}_${timestamp}_tmp_bak`);

  if (fs.existsSync(contentDir)) {
    fs.renameSync(contentDir, contentDirBak);
    globalBackupDirs.push({ original: contentDir, bak: contentDirBak });
  }
  if (fs.existsSync(imageDir)) {
    fs.renameSync(imageDir, imageDirBak);
    globalBackupDirs.push({ original: imageDir, bak: imageDirBak });
  }

  try {
    // 徹底清除代碼配置：正則刪除所有 BEGIN 到 END 區間
    const cleanFiles = [
      CONFIG_TS_PATH,
      KEYSTATIC_CONFIG_PATH,
      TYPE_ASTRO_PATH,
      SLUG_ASTRO_PATH,
      IMPORT_CLI_PATH
    ];

    for (const filePath of cleanFiles) {
      if (fs.existsSync(filePath)) {
        console.log(`⌛ 正在清除檔案 "${path.basename(filePath)}" 中的註冊代碼...`);
        let content = fs.readFileSync(filePath, 'utf-8');
        
        // 使用正則匹配，清除包含 BEGIN_COLLECTION_{colName} 到 END_COLLECTION_{colName} 及其可能附帶的尾隨逗號和換行
        const regex = new RegExp(`\\/\\* BEGIN_COLLECTION_${colName}_[A-Z_]+ \\*\\/[\\s\\S]*?\\/\\* END_COLLECTION_${colName}_[A-Z_]+ \\*\\/,?\\r?\\n?`, 'g');
        content = content.replace(regex, '');
        fs.writeFileSync(filePath, content, 'utf-8');
      }
    }

    // 格式化代碼
    formatFiles();

    // 驗證編譯
    testBuild();

    // 成功，清除備份（包括實體快照目錄）
    cleanBackupFiles();
    console.log(`\n\x1b[32m🎉 恭喜！自訂類別 "${colName}" 及其註冊代碼已徹底刪除，且全站編譯通過！\x1b[0m`);

  } catch (err) {
    console.error('\n❌ 刪除自訂類別失敗：', err.message);
    
    // 還原備份
    restoreFiles();
    throw err;
  }
}

async function main() {
  console.log('====================================================');
  console.log('🏰 唐門山莊 - 自訂類別整合維護系統 (CRUD)');
  console.log('====================================================');
  console.log('  [1] 新增自訂類別 (Create)');
  console.log('  [2] 修改自訂類別 (Update)');
  console.log('  [3] 刪除自訂類別 (Delete)');
  console.log('  [4] 退出系統');
  
  const choice = await question('請選擇操作序號 (1-4): ');
  
  switch (choice.trim()) {
    case '1':
      await handleCreate();
      break;
    case '2':
      await handleUpdate();
      break;
    case '3':
      await handleDelete();
      break;
    default:
      console.log('退出系統。');
      break;
  }
  
  rl.close();
}

main().catch(err => {
  console.error('❌ 系統異常:', err);
  if (rl) rl.close();
  process.exit(1);
});
