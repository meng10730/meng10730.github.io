import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const EXTERNAL_WORKSPACE = 'C:\\workspace\\長生劫_小說工作區';
const SOURCE_DIR = path.join(EXTERNAL_WORKSPACE, '00_世界觀與劇本', '01_Creative_Source');
const CONFIG_FILE = path.join(__dirname, '..', 'sync-config.json');

// 遞迴遍歷目錄下的所有 markdown 檔案，取得相對路徑
function getMarkdownFiles(dir, baseDir = dir) {
  let results = [];
  const list = fs.readdirSync(dir);
  list.forEach(file => {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat && stat.isDirectory()) {
      results = results.concat(getMarkdownFiles(fullPath, baseDir));
    } else if (file.endsWith('.md') && !file.startsWith('.') && !file.startsWith('_')) {
      const relativePath = path.relative(baseDir, fullPath).replace(/\\/g, '/');
      results.push({
        relativePath,
        fileName: path.basename(file, '.md'),
        dirName: path.basename(dir)
      });
    }
  });
  return results;
}

function init() {
  if (!fs.existsSync(SOURCE_DIR)) {
    console.error(`[錯誤] 找不到小說工作區的原始目錄: ${SOURCE_DIR}`);
    process.exit(1);
  }

  console.log(`正在掃描目錄: ${SOURCE_DIR}...`);
  const files = getMarkdownFiles(SOURCE_DIR);
  console.log(`掃描到 ${files.length} 個 Markdown 檔案。`);

  const mappings = {};

  files.forEach(file => {
    // 依據子目錄決定 Astro Collection
    let collection = 'worldview';
    let category = '';

    if (file.relativePath.startsWith('01_機制與世界觀')) {
      collection = 'worldview';
      category = '世界觀';
    } else if (file.relativePath.startsWith('02_勢力與組織')) {
      collection = 'factions';
      category = '勢力';
    } else if (file.relativePath.startsWith('03_角色檔案庫')) {
      collection = 'characters';
      category = '人物';
    } else if (file.relativePath.startsWith('04_劇情大綱與腳本')) {
      collection = 'novels';
      category = '大綱與劇本';
    } else {
      collection = 'worldview';
      category = '其他';
    }

    // 處理 Slug：去除開頭的序號、底線與類型前綴
    let cleanSlug = file.fileName
      .replace(/^\d+_/g, '') // 去除開頭序號
      .replace(/^(角色|機制|世界觀|大綱|劇本|幕後勢力|世界勢力|地下勢力|世俗勢力|中立勢力)_/g, '') // 去除類型前綴
      .trim();

    let title = cleanSlug;

    // 依據不同 collection 填寫預設的 Frontmatter mappings
    const mapping = {
      collection,
      slug: cleanSlug,
      title: title
    };

    if (collection === 'worldview' || collection === 'factions') {
      mapping.category = category;
    } else if (collection === 'characters') {
      mapping.alias = [title];
      mapping.affiliation = ''; 
      mapping.novel = '長生劫';
      mapping.tags = [];
    } else if (collection === 'novels') {
      mapping.description = `${title} - 大綱與劇本連載`;
      mapping.genre = ['仙俠', '架空'];
      mapping.status = 'ongoing';
    }

    mappings[file.relativePath] = mapping;
  });

  const configContent = {
    workspacePath: EXTERNAL_WORKSPACE,
    mappings: mappings
  };

  fs.writeFileSync(CONFIG_FILE, JSON.stringify(configContent, null, 2), 'utf8');
  console.log(`[成功] 對照表 sync-config.json 已初始化成功！共計 ${Object.keys(mappings).length} 個檔案。`);
  console.log(`對照表檔案路徑: ${CONFIG_FILE}`);
}

init();
