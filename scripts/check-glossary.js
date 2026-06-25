import fs from 'fs';
import path from 'path';

const CONTENT_DIR = path.resolve('src/content');
const PUBLIC_IMAGES_DIR = path.resolve('public/images');
const TRASH_DIR = path.resolve('trash/images');

// 常用中文停用詞，避免誤判
const STOPWORDS = new Set([
  '自己', '大家', '我們', '你們', '他們', '這個', '那個', '什麼', '怎麼',
  '莊稼', '弟子', '豪傑', '朝廷', '武林', '江湖', '山莊', '正派', '反派',
  '徒弟', '師傅', '掌門', '大師', '長老', '弟子', '門派', '武功', '修仙',
  '天下', '世人', '百姓', '朝野', '邊疆', '塞外', '中原', '神州', '天地',
  '乾坤', '陰陽', '五行', '八卦', '長空', '萬物', '眾生', '天尊', '仙人',
  '凡人', '修士', '妖魔', '鬼怪', '英雄', '好漢', '豪客', '閣下', '前輩',
  '晚輩', '師徒', '同門', '散修', '護法', '堂主', '莊主', '公子', '姑娘'
]);

// 1. 取得已登記的關鍵字與別名
function getRegisteredKeywords() {
  const keywords = new Set();
  const collections = ['characters', 'worldview', 'factions'];

  collections.forEach(col => {
    const dir = path.join(CONTENT_DIR, col);
    if (!fs.existsSync(dir)) return;

    const files = fs.readdirSync(dir).filter(f => f.endsWith('.md'));
    files.forEach(file => {
      const content = fs.readFileSync(path.join(dir, file), 'utf-8');
      
      // 簡單提取 YAML Frontmatter 中的 name, title, alias
      const frontmatterMatch = content.match(/^---([\s\S]*?)---/);
      if (frontmatterMatch) {
        const yaml = frontmatterMatch[1];
        
        // 匹配 name
        const nameMatch = yaml.match(/name:\s*["']?([^"'\r\n]+)["']?/);
        if (nameMatch) keywords.add(nameMatch[1].trim());

        // 匹配 title
        const titleMatch = yaml.match(/title:\s*["']?([^"'\r\n]+)["']?/);
        if (titleMatch) keywords.add(titleMatch[1].trim());

        // 匹配 alias 列表 (支援 array 或 單一值)
        const aliasMatch = yaml.match(/alias:\s*\[([^\]]*)\]/);
        if (aliasMatch) {
          aliasMatch[1].split(',').forEach(a => {
            const clean = a.replace(/["']/g, '').trim();
            if (clean) keywords.add(clean);
          });
        }
      }
    });
  });

  return keywords;
}

// 2. 載入 AI 封殺詞庫
function getAntiAiKeywords() {
  const words = new Set(['法則', '天道', '洗白', '齏粉', '倒吸一口涼氣', '嘴角勾起', '弧度', '天道法則']);
  const dictPath = path.resolve('anti-ai-dictionary.md');
  
  if (fs.existsSync(dictPath)) {
    const content = fs.readFileSync(dictPath, 'utf-8');
    // 假設 anti-ai-dictionary.md 是以 bullet 方式列出詞彙
    const matches = content.match(/-?\s*["']?([\u4e00-\u9fa5]{2,10})["']?/g);
    if (matches) {
      matches.forEach(m => {
        const clean = m.replace(/[-\s"']/g, '').trim();
        if (clean && clean.length >= 2) words.add(clean);
      });
    }
  }
  return words;
}

// 3. 掃描未登記與文風詞彙
function scanContent(registered, antiAi) {
  const novelsDir = path.join(CONTENT_DIR, 'novels');
  const guoxueDir = path.join(CONTENT_DIR, 'guoxue');
  const targets = [novelsDir, guoxueDir];

  // 比對稱謂前後的 2~3 個字 (如 "不夜侯莊主" 或 "姑娘煙蘿")
  const patterns = [
    /([\u4e00-\u9fa5]{2,3})(?:莊主|前輩|姑娘|公子|大師|師兄|師姐|師弟|師妹|長老)/g,
    /(?:莊主|前輩|姑娘|公子|大師|師兄|師姐|師弟|師妹|長老)([\u4e00-\u9fa5]{2,3})/g
  ];

  console.log('\x1b[36m=== 開始掃描小說正文設定與文風 ===\x1b[0m');

  targets.forEach(dir => {
    if (!fs.existsSync(dir)) return;

    const files = fs.readdirSync(dir).filter(f => f.endsWith('.md'));
    files.forEach(file => {
      const filePath = path.join(dir, file);
      let content = fs.readFileSync(filePath, 'utf-8');
      
      // 去除 Frontmatter
      content = content.replace(/^---[\s\S]*?---/, '');
      // 去除 HTML 與 MDX 註解
      content = content.replace(/<!--[\s\S]*?-->/g, '');
      content = content.replace(/\{\/\*[\s\S]*?\*\/\}/g, '');
      // 去除 Markdown 程式碼區塊
      content = content.replace(/```[\s\S]*?```/g, '');

      const baseName = path.basename(filePath);

      // 檢測 AI 封殺詞
      antiAi.forEach(word => {
        if (content.includes(word)) {
          console.warn(`\x1b[33m⚠️ [文風警示] 檔案 ${baseName} 中發現 AI 敏感詞彙：「${word}」\x1b[0m`);
        }
      });

      // 檢測未登記設定 (稱謂比對)
      patterns.forEach(regex => {
        let match;
        while ((match = regex.exec(content)) !== null) {
          const word = match[1];
          if (word.length >= 2 && !registered.has(word) && !STOPWORDS.has(word)) {
            console.warn(`\x1b[33m⚠️ [設定提醒] 檔案 ${baseName} 中發現疑似未登記條目：「${word}」（鄰近稱謂）\x1b[0m`);
          }
        }
      });
    });
  });
}

// 4. 掃描並清理未引用圖片
function cleanOrphanedImages() {
  if (!fs.existsSync(PUBLIC_IMAGES_DIR)) return;

  const images = fs.readdirSync(PUBLIC_IMAGES_DIR).filter(f => {
    const ext = path.extname(f).toLowerCase();
    return ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'].includes(ext);
  });

  if (images.length === 0) return;

  console.log('\x1b[36m=== 開始掃描未引用媒體資源 ===\x1b[0m');

  // 蒐集全站所有 Markdown 內容
  let allContent = '';
  const scanMarkdownDirs = (dir) => {
    if (!fs.existsSync(dir)) return;
    const items = fs.readdirSync(dir);
    items.forEach(item => {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);
      if (stat.isDirectory()) {
        scanMarkdownDirs(fullPath);
      } else if (stat.isFile() && item.endsWith('.md')) {
        allContent += fs.readFileSync(fullPath, 'utf-8') + '\n';
      }
    });
  };
  
  scanMarkdownDirs(CONTENT_DIR);

  let cleanedCount = 0;

  images.forEach(img => {
    // 檢查全站 Markdown 內文是否包含該圖檔名稱
    const isUsed = allContent.includes(img);
    if (!isUsed) {
      if (!fs.existsSync(TRASH_DIR)) {
        fs.mkdirSync(TRASH_DIR, { recursive: true });
      }

      const oldPath = path.join(PUBLIC_IMAGES_DIR, img);
      const newPath = path.join(TRASH_DIR, img);

      try {
        fs.renameSync(oldPath, newPath);
        console.log(`\x1b[32m🗑️ [媒體清理] 發現未引用圖片「${img}」，已移至 trash/images/ 暫存區\x1b[0m`);
        cleanedCount++;
      } catch (err) {
        console.error(`Failed to move image ${img} to trash:`, err);
      }
    }
  });

  if (cleanedCount === 0) {
    console.log('✅ 未發現任何幽靈媒體資源，排版健全。');
  }
}

// 執行主程式
try {
  const registered = getRegisteredKeywords();
  const antiAi = getAntiAiKeywords();
  scanContent(registered, antiAi);
  cleanOrphanedImages();
} catch (err) {
  console.error('Error during check-glossary execution:', err);
}
