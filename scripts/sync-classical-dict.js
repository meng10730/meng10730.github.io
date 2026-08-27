import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SOURCE_DIR = 'C:\\workspace\\長生劫_小說工作區\\00_世界觀與劇本\\01_Creative_Source\\00_古典典故字庫';
const TARGET_DIR = path.resolve(__dirname, '../src/content/dictionary');

if (!fs.existsSync(SOURCE_DIR)) {
  console.error(`❌ 找不到來源字庫目錄: ${SOURCE_DIR}`);
  process.exit(1);
}

if (!fs.existsSync(TARGET_DIR)) {
  fs.mkdirSync(TARGET_DIR, { recursive: true });
}

// 建立 _template.md
const templateContent = `---
title: "單字"
character: "單字"
bopomofo: "ㄅㄧˋ"
pinyin: "bì"
initial: "ㄅ"
radical: "玉部"
strokes: 18
source: "《詩經》"
tags: ["古典典故", "字音考據", "ㄅ_聲母"]
pubDate: 2026-08-27
---

# 典故單字考據：單字

## 1. 基本字音與字義
- 審定注音：
- 部首筆畫：
- 白話本義：

## 2. 古籍出處與經典引文
- 經史子集出處：
`;
fs.writeFileSync(path.join(TARGET_DIR, '_template.md'), templateContent, 'utf8');

console.log('🔄 開始同步《長生劫》古典典故字庫至個人網站...');

const entries = fs.readdirSync(SOURCE_DIR, { withFileTypes: true });
let syncedCount = 0;

for (const entry of entries) {
  if (entry.isDirectory() && entry.name.includes('_聲母')) {
    const initial = entry.name.replace(/_聲母.*$/, '');
    const folderPath = path.join(SOURCE_DIR, entry.name);
    const files = fs.readdirSync(folderPath);

    for (const file of files) {
      if (file.endsWith('.md')) {
        const charName = path.basename(file, '.md');
        const sourceFilePath = path.join(folderPath, file);
        const rawContent = fs.readFileSync(sourceFilePath, 'utf8');

        // 解析注音與拼音
        let bopomofo = '';
        let pinyin = '';
        const bopomofoMatch = rawContent.match(/審定注音[：:]\s*([^\r\n（]+)(?:[（\(]([^）\)]+)[）\)])?/);
        if (bopomofoMatch) {
          bopomofo = bopomofoMatch[1]?.trim() || '';
          pinyin = bopomofoMatch[2]?.trim() || '';
        }

        // 解析部首與筆畫
        let radical = '';
        let strokes = '';
        const radicalMatch = rawContent.match(/部首筆畫[：:]\s*([^/／\r\n]+)[/／]\s*總筆畫\s*(\d+)\s*畫/);
        if (radicalMatch) {
          radical = radicalMatch[1]?.trim() || '';
          strokes = radicalMatch[2]?.trim() || '';
        }

        // 提取典籍出處摘要
        const sources = [];
        const sourceMatches = rawContent.matchAll(/《([^》]+)》/g);
        for (const m of sourceMatches) {
          if (!sources.includes(`《${m[1]}》`) && sources.length < 3) {
            sources.push(`《${m[1]}》`);
          }
        }
        const sourceText = sources.join('、');

        // 生成標準 Frontmatter
        const frontmatter = `---
title: "${charName}"
character: "${charName}"
bopomofo: "${bopomofo}"
pinyin: "${pinyin}"
initial: "${initial}"
${radical ? `radical: "${radical}"\n` : ''}${strokes ? `strokes: ${strokes}\n` : ''}${sourceText ? `source: "${sourceText}"\n` : ''}tags: ["古典典故", "字音考據", "${initial}_聲母"]
pubDate: 2026-08-27
---

`;

        // 移除原始檔案開頭可能重複的 YAML 或標題，保持乾淨本文
        let cleanBody = rawContent;
        if (cleanBody.startsWith('---')) {
          const secondDash = cleanBody.indexOf('---', 3);
          if (secondDash !== -1) {
            cleanBody = cleanBody.substring(secondDash + 3).trim();
          }
        }

        const targetFilePath = path.join(TARGET_DIR, `${charName}.md`);
        fs.writeFileSync(targetFilePath, frontmatter + cleanBody, 'utf8');
        syncedCount++;
        console.log(`  ✓ 已同步 [${initial}_聲母]: ${charName} (${bopomofo || pinyin})`);
      }
    }
  }
}

console.log(`\n🎉 同步完成！共成功同步 ${syncedCount} 個典故單字至 src/content/dictionary/`);
